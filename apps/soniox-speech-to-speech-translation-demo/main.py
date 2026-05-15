import os, json, asyncio, base64, websockets, httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv(override=True)

SONIOX_API_KEY = os.environ["SONIOX_API_KEY"]
STT_URL = "wss://stt-rt.soniox.com/transcribe-websocket"
TTS_URL = "wss://tts-rt.soniox.com/tts-websocket"

app = FastAPI()


def get_stt_config(diarization: bool, lang_id: bool, target: str) -> dict:
    return {
        "api_key": SONIOX_API_KEY,
        "model": "stt-rt-v4",
        "audio_format": "auto",
        "enable_endpoint_detection": True,
        "max_endpoint_delay_ms": 500,
        "enable_speaker_diarization": diarization,
        "enable_language_identification": lang_id,
        "translation": {"type": "one_way", "target_language": target},
    }


def get_tts_config(stream_id: str, voice: str, lang: str) -> dict:
    return {
        "api_key": SONIOX_API_KEY,
        "stream_id": stream_id,
        "model": "tts-rt-v1",
        "voice": voice,
        "language": lang,
        "audio_format": "pcm_s16le",
        "sample_rate": 24000,
    }


@app.websocket("/ws/translate")
async def translation_websocket(
    browser_ws: WebSocket,
    target_lang: str = "en",
    lang_id: bool = True,
    diarize: bool = True,
    voice: str = "Maya",
    tts: bool = True,
    audio_url: str | None = None,
    audio_duration: float | None = None,
) -> None:
    await browser_ws.accept()
    stt_ws = None
    tts_ws = None
    stt_config = get_stt_config(
        diarization=diarize, lang_id=lang_id, target=target_lang
    )
    # Queue decouples STT producing tokens from TTS consuming them — important
    # when the source speaks faster than TTS can synthesize.
    tts_queue = asyncio.Queue() if tts else None
    # Shared between handle_stt (sets stt_done), tts_sender (writes current_stream_id),
    # and pipe_tts_to_browser (reads both to decide when the session is over).
    tts_state = {"current_stream_id": None, "stt_done": False}
    try:
        stt_ws = await websockets.connect(STT_URL)
        await stt_ws.send(json.dumps(stt_config))

        if audio_url and audio_duration:
            input_coro = stream_url_to_stt(
                audio_url=audio_url,
                duration=audio_duration,
                browser_ws=browser_ws,
                stt_ws=stt_ws,
            )
        else:
            input_coro = pipe_browser_audio_to_stt(browser_ws=browser_ws, stt_ws=stt_ws)

        if tts:
            tts_ws = await websockets.connect(TTS_URL)

            tts_idle = asyncio.Event()
            tts_idle.set()  # default: no stream open, free to open one

            # Pre-open a TTS stream so the first utterance doesn't pay the
            # round-trip for stream setup.
            try:
                await tts_ws.send(
                    json.dumps(
                        get_tts_config(
                            stream_id="prewarm", voice=voice, lang=target_lang
                        )
                    )
                )
                tts_state["current_stream_id"] = "prewarm"
                tts_idle.clear()
            except websockets.WebSocketException:
                pass

        async with asyncio.TaskGroup() as tg:
            tg.create_task(input_coro)
            tg.create_task(
                handle_stt(
                    stt_ws=stt_ws,
                    browser_ws=browser_ws,
                    tts_queue=tts_queue,
                    tts_state=tts_state,
                )
            )
            if tts:
                tg.create_task(
                    tts_sender(
                        tts_queue=tts_queue,
                        tts_idle=tts_idle,
                        tts_state=tts_state,
                        tts_ws=tts_ws,
                        target_lang=target_lang,
                        voice=voice,
                    )
                )
                tg.create_task(
                    pipe_tts_to_browser(
                        tts_ws=tts_ws,
                        browser_ws=browser_ws,
                        tts_idle=tts_idle,
                        tts_state=tts_state,
                    )
                )
                tg.create_task(tts_keepalive(tts_ws=tts_ws))

    except* WebSocketDisconnect:
        pass
    finally:
        if stt_ws is not None:
            await stt_ws.close()
        if tts_ws is not None:
            await tts_ws.close()


async def pipe_browser_audio_to_stt(browser_ws: WebSocket, stt_ws) -> None:
    while True:
        data = await browser_ws.receive_bytes()
        await stt_ws.send(data)


async def stream_url_to_stt(
    audio_url: str, duration: float, stt_ws, browser_ws: WebSocket
) -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            async with client.stream("GET", audio_url, follow_redirects=True) as resp:
                resp.raise_for_status()
                content_length = int(resp.headers.get("content-length", 0))
                byte_rate = content_length / duration if content_length else 16000
                bytes_per_tick = max(1, int(byte_rate * 0.1))

                buffer = bytearray()
                next_tick = asyncio.get_running_loop().time()
                async for chunk in resp.aiter_bytes():
                    buffer.extend(chunk)
                    while len(buffer) >= bytes_per_tick:
                        await stt_ws.send(bytes(buffer[:bytes_per_tick]))
                        del buffer[:bytes_per_tick]
                        next_tick += 0.1
                        delay = next_tick - asyncio.get_running_loop().time()
                        if delay > 0:
                            await asyncio.sleep(delay)
                if buffer:
                    await stt_ws.send(bytes(buffer))
                await stt_ws.send(b"")
        except httpx.HTTPError as e:
            await browser_ws.send_json(
                {"error_code": "fetch_failed", "error_message": str(e)}
            )


async def handle_stt(
    stt_ws,
    browser_ws: WebSocket,
    tts_queue: asyncio.Queue | None,
    tts_state: dict,
) -> None:
    text_pushed = False
    try:
        while True:
            message = await stt_ws.recv()
            data = json.loads(message)
            await browser_ws.send_json(data)

            if data.get("error_code") is not None:
                print(f"Error: {data['error_code']} - {data['error_message']}")
                break

            if tts_queue is not None:
                for token in data.get("tokens", []):
                    text = token.get("text")
                    if not text:
                        continue
                    if text == "<end>":
                        await tts_queue.put(("end", None))
                    elif token.get("translation_status") == "translation":
                        await tts_queue.put(("text", text))
                        text_pushed = True
            if data.get("finished"):
                break
    except (WebSocketDisconnect, RuntimeError, websockets.ConnectionClosedOK):
        pass
    except websockets.ConnectionClosedError as e:
        print(f"Error {e}")
    finally:
        if tts_queue is not None:
            # Signal tts_sender to wrap up: close any open stream, then exit.
            await tts_queue.put(("end", None))
            await tts_queue.put(None)
        tts_state["stt_done"] = True
        # If no TTS audio will ever follow (TTS disabled or no text emitted),
        # there's no terminated event coming to trigger session_done — emit it
        # ourselves so the browser doesn't wait forever.
        if not text_pushed:
            try:
                await browser_ws.send_json({"session_done": True})
            except Exception:
                pass


async def tts_sender(
    tts_queue: asyncio.Queue,
    tts_idle: asyncio.Event,
    tts_state: dict,
    tts_ws,
    target_lang: str,
    voice: str,
) -> None:
    stream_counter = 0
    current_stream_used = False
    try:
        while True:
            data = await tts_queue.get()

            if data is None:
                break

            kind, payload = data
            if kind == "text":
                # Open a new stream if needed
                if tts_state["current_stream_id"] is None:
                    await tts_idle.wait()
                    stream_counter += 1
                    tts_state["current_stream_id"] = f"utterance-{stream_counter}"
                    config = get_tts_config(
                        stream_id=tts_state["current_stream_id"],
                        voice=voice,
                        lang=target_lang,
                    )
                    await tts_ws.send(json.dumps(config))
                # Send the text chunk
                pkg = {
                    "stream_id": tts_state["current_stream_id"],
                    "text": payload,
                    "text_end": False,
                }
                await tts_ws.send(json.dumps(pkg))
                current_stream_used = True
            elif kind == "end":
                if tts_state["current_stream_id"] is not None and current_stream_used:
                    tts_idle.clear()  # mark stream as still draining
                    pkg = {
                        "stream_id": tts_state["current_stream_id"],
                        "text": "",
                        "text_end": True,
                    }
                    await tts_ws.send(json.dumps(pkg))
                    tts_state["current_stream_id"] = None
                    current_stream_used = False
    except websockets.ConnectionClosedOK:
        pass
    except websockets.ConnectionClosedError as e:
        print(f"TTS WS closed: {e}")


async def pipe_tts_to_browser(
    tts_ws,
    browser_ws: WebSocket,
    tts_idle: asyncio.Event,
    tts_state: dict,
) -> None:
    try:
        while True:
            message = await tts_ws.recv()
            data = json.loads(message)

            if data.get("error_code") is not None:
                print(
                    f"Error in stream_id {data['stream_id']}: {data['error_code']} - {data['error_message']}"
                )

            audio_b64 = data.get("audio")
            if audio_b64:
                await browser_ws.send_bytes(base64.b64decode(audio_b64))

            if data.get("terminated"):
                tts_idle.set()
                if data["stream_id"] == tts_state["current_stream_id"]:
                    tts_state["current_stream_id"] = None
                # Once STT is finished and no stream remains open, this
                # terminated event marked the very last TTS audio of the
                # session — tell the browser it's safe to stop.
                if tts_state["stt_done"] and tts_state["current_stream_id"] is None:
                    try:
                        await browser_ws.send_json({"session_done": True})
                    except Exception:
                        pass
                    await tts_ws.close()
                    break
    except (WebSocketDisconnect, RuntimeError, websockets.ConnectionClosedOK):
        pass
    except websockets.ConnectionClosedError as e:
        print(f"Error {e}")


async def tts_keepalive(tts_ws):
    try:
        while True:
            await asyncio.sleep(20)
            await tts_ws.send(json.dumps({"keep_alive": True}))
    except websockets.ConnectionClosedOK:
        pass
    except websockets.ConnectionClosedError as e:
        print(f"TTS WS closed: {e}")


app.mount("/", StaticFiles(directory="web", html=True), name="static")
