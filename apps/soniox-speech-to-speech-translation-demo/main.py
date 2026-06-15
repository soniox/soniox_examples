import os, json, asyncio, websockets, httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from tts import make_tts_backend

load_dotenv(override=True)

SONIOX_API_KEY = os.environ["SONIOX_API_KEY"]
STT_URL = "wss://stt-rt.soniox.com/transcribe-websocket"

# TTS provider selection. Defaults to 60db; set to "soniox" for Soniox TTS.
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "sixtydb")
SIXTYDB_API_KEY = os.getenv("SIXTYDB_API_KEY", "")
SIXTYDB_VOICE_ID = os.getenv("SIXTYDB_VOICE_ID", "")
SIXTYDB_API_BASE = os.getenv("SIXTYDB_API_BASE", "https://api.60db.ai")

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
    tts_backend = None
    stt_config = get_stt_config(
        diarization=diarize, lang_id=lang_id, target=target_lang
    )
    # Queue decouples STT producing tokens from TTS consuming them — important
    # when the source speaks faster than TTS can synthesize.
    tts_queue = asyncio.Queue() if tts else None
    # Shared with the TTS backend: handle_stt sets stt_done; the Soniox backend
    # uses current_stream_id to decide when the session's final audio has played.
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
            # The backend (Soniox WebSocket or 60db HTTP) is interchangeable: it
            # consumes translated text from tts_queue and streams PCM to the
            # browser. The rest of the handler doesn't care which one is used.
            tts_backend = make_tts_backend(
                TTS_PROVIDER,
                voice=voice,
                target_lang=target_lang,
                soniox_api_key=SONIOX_API_KEY,
                sixtydb_api_key=SIXTYDB_API_KEY,
                sixtydb_voice_id=SIXTYDB_VOICE_ID,
                sixtydb_base_url=SIXTYDB_API_BASE,
            )

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
                    tts_backend.run(
                        tts_queue=tts_queue,
                        browser_ws=browser_ws,
                        tts_state=tts_state,
                    )
                )

    except* WebSocketDisconnect:
        pass
    finally:
        if stt_ws is not None:
            await stt_ws.close()
        if tts_backend is not None:
            await tts_backend.aclose()


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
            # Signal the TTS backend to wrap up: flush the last utterance, then exit.
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


app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
