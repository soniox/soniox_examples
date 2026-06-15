"""Text-to-speech backends for the speech-to-speech demo.

The WebSocket handler in ``main.py`` is provider-agnostic: it pushes translated
text onto a queue and lets a *backend* turn that into PCM audio frames which are
streamed to the browser. Two backends are provided behind a common
:class:`TtsBackend` interface:

- :class:`SonioxTtsBackend`  – Soniox real-time streaming TTS over WebSocket.
- :class:`SixtyDBTtsBackend` – 60db HTTP TTS (``POST /tts-synthesize``).

Both emit raw little-endian 16-bit PCM at 24 kHz, which is exactly what the
browser plays (see ``frontend/app.js``), so they are interchangeable.

Queue protocol (items put on ``tts_queue`` by ``handle_stt``):
- ``("text", str)`` – a chunk of translated text for the current utterance.
- ``("end", None)`` – the current utterance is complete; flush/synthesize it.
- ``None``          – no more input; finish up and signal ``session_done``.
"""

import abc
import asyncio
import base64
import io
import json
import sys
import wave
from array import array

import httpx
import websockets
from fastapi import WebSocket, WebSocketDisconnect

SONIOX_TTS_URL = "wss://tts-rt.soniox.com/tts-websocket"
SIXTYDB_DEFAULT_BASE_URL = "https://api.60db.ai"
TTS_SAMPLE_RATE = 24000

DEFAULT_PROVIDER = "sixtydb"

# ~40 ms of PCM per browser frame (24000 Hz * 2 bytes * 0.04 s = 1920 bytes).
_CHUNK_BYTES = int(TTS_SAMPLE_RATE * 2 * 0.04) & ~1


class TtsBackend(abc.ABC):
    """Consumes translated text from ``tts_queue`` and streams PCM to the browser."""

    @abc.abstractmethod
    async def run(
        self,
        tts_queue: asyncio.Queue,
        browser_ws: WebSocket,
        tts_state: dict,
    ) -> None:
        ...

    async def aclose(self) -> None:
        """Release any resources (sockets, HTTP clients). Safe to call twice."""


# ---------------------------------------------------------------------------
# Soniox streaming WebSocket backend
# ---------------------------------------------------------------------------


class SonioxTtsBackend(TtsBackend):
    """Real-time Soniox TTS. Streams text tokens per utterance over a WebSocket."""

    def __init__(self, api_key: str, voice: str, target_lang: str):
        self._api_key = api_key
        self._voice = voice
        self._target_lang = target_lang
        self._ws = None

    def _config(self, stream_id: str) -> dict:
        return {
            "api_key": self._api_key,
            "stream_id": stream_id,
            "model": "tts-rt-v1",
            "voice": self._voice,
            "language": self._target_lang,
            "audio_format": "pcm_s16le",
            "sample_rate": TTS_SAMPLE_RATE,
        }

    async def run(self, tts_queue, browser_ws, tts_state):
        self._ws = await websockets.connect(SONIOX_TTS_URL)

        tts_idle = asyncio.Event()
        tts_idle.set()  # default: no stream open, free to open one

        # Pre-open a TTS stream so the first utterance doesn't pay the
        # round-trip for stream setup.
        try:
            await self._ws.send(json.dumps(self._config("prewarm")))
            tts_state["current_stream_id"] = "prewarm"
            tts_idle.clear()
        except websockets.WebSocketException:
            pass

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._sender(tts_queue, tts_idle, tts_state))
            tg.create_task(self._pipe(browser_ws, tts_idle, tts_state))
            tg.create_task(self._keepalive())

    async def aclose(self):
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    async def _sender(self, tts_queue, tts_idle, tts_state):
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
                        await self._ws.send(
                            json.dumps(self._config(tts_state["current_stream_id"]))
                        )
                    # Send the text chunk
                    pkg = {
                        "stream_id": tts_state["current_stream_id"],
                        "text": payload,
                        "text_end": False,
                    }
                    await self._ws.send(json.dumps(pkg))
                    current_stream_used = True
                elif kind == "end":
                    if (
                        tts_state["current_stream_id"] is not None
                        and current_stream_used
                    ):
                        tts_idle.clear()  # mark stream as still draining
                        pkg = {
                            "stream_id": tts_state["current_stream_id"],
                            "text": "",
                            "text_end": True,
                        }
                        await self._ws.send(json.dumps(pkg))
                        tts_state["current_stream_id"] = None
                        current_stream_used = False
        except websockets.ConnectionClosedOK:
            pass
        except websockets.ConnectionClosedError as e:
            print(f"TTS WS closed: {e}")

    async def _pipe(self, browser_ws, tts_idle, tts_state):
        try:
            while True:
                message = await self._ws.recv()
                data = json.loads(message)

                if data.get("error_code") is not None:
                    print(
                        f"Error in stream_id {data['stream_id']}: "
                        f"{data['error_code']} - {data['error_message']}"
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
                    if (
                        tts_state["stt_done"]
                        and tts_state["current_stream_id"] is None
                    ):
                        await _send_session_done(browser_ws)
                        await self._ws.close()
                        break
        except (WebSocketDisconnect, RuntimeError, websockets.ConnectionClosedOK):
            pass
        except websockets.ConnectionClosedError as e:
            print(f"Error {e}")

    async def _keepalive(self):
        try:
            while True:
                await asyncio.sleep(20)
                await self._ws.send(json.dumps({"keep_alive": True}))
        except websockets.ConnectionClosedOK:
            pass
        except websockets.ConnectionClosedError as e:
            print(f"TTS WS closed: {e}")


# ---------------------------------------------------------------------------
# 60db HTTP backend
# ---------------------------------------------------------------------------


class SixtyDBTtsBackend(TtsBackend):
    """60db TTS via the simple ``POST /tts-synthesize`` endpoint.

    Accumulates text per utterance and synthesizes it in one request when the
    utterance ends, then streams the resulting PCM to the browser in small frames.
    """

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        base_url: str = SIXTYDB_DEFAULT_BASE_URL,
        speed: float = 1.0,
        stability: int = 50,
        similarity: int = 75,
        enhance: bool = True,
    ):
        self._api_key = api_key
        self._voice_id = voice_id
        self._base_url = base_url.rstrip("/")
        self._speed = speed
        self._stability = stability
        self._similarity = similarity
        self._enhance = enhance
        self._client: httpx.AsyncClient | None = None

    async def run(self, tts_queue, browser_ws, tts_state):
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        buffer: list[str] = []
        try:
            while True:
                item = await tts_queue.get()
                if item is None:
                    await self._flush(buffer, browser_ws)
                    break
                kind, payload = item
                if kind == "text":
                    buffer.append(payload)
                elif kind == "end":
                    await self._flush(buffer, browser_ws)
                    buffer = []
        finally:
            await _send_session_done(browser_ws)

    async def aclose(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _flush(self, buffer: list[str], browser_ws):
        text = "".join(buffer).strip()
        if not text or self._client is None:
            return
        try:
            pcm = await _synthesize_pcm(
                self._client,
                api_key=self._api_key,
                text=text,
                voice_id=self._voice_id,
                base_url=self._base_url,
                speed=self._speed,
                stability=self._stability,
                similarity=self._similarity,
                enhance=self._enhance,
            )
        except (httpx.HTTPError, ValueError) as e:
            print(f"60db TTS request failed: {e}")
            try:
                await browser_ws.send_json(
                    {"error_code": "tts_failed", "error_message": str(e)}
                )
            except Exception:
                pass
            return

        for offset in range(0, len(pcm), _CHUNK_BYTES):
            await browser_ws.send_bytes(pcm[offset : offset + _CHUNK_BYTES])


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def make_tts_backend(
    provider: str,
    *,
    voice: str,
    target_lang: str,
    soniox_api_key: str,
    sixtydb_api_key: str = "",
    sixtydb_voice_id: str = "",
    sixtydb_base_url: str = SIXTYDB_DEFAULT_BASE_URL,
) -> TtsBackend:
    """Build the TTS backend for ``provider`` ("soniox" or "sixtydb")."""
    name = (provider or DEFAULT_PROVIDER).strip().lower()

    if name == "soniox":
        return SonioxTtsBackend(
            api_key=soniox_api_key, voice=voice, target_lang=target_lang
        )
    if name in ("sixtydb", "60db"):
        return SixtyDBTtsBackend(
            api_key=sixtydb_api_key,
            voice_id=sixtydb_voice_id,
            base_url=sixtydb_base_url or SIXTYDB_DEFAULT_BASE_URL,
        )
    raise ValueError(
        f"Unknown TTS_PROVIDER '{provider}'. Expected 'soniox' or 'sixtydb'."
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _send_session_done(browser_ws: WebSocket) -> None:
    try:
        await browser_ws.send_json({"session_done": True})
    except Exception:
        pass


async def _synthesize_pcm(
    client: httpx.AsyncClient,
    *,
    api_key: str,
    text: str,
    voice_id: str,
    base_url: str,
    speed: float,
    stability: int,
    similarity: int,
    enhance: bool,
) -> bytes:
    """Synthesize ``text`` via 60db and return raw PCM s16le at 24 kHz."""
    response = await client.post(
        f"{base_url}/tts-synthesize",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "text": text,
            "voice_id": voice_id,
            "speed": speed,
            "stability": stability,
            "similarity": similarity,
            "enhance": enhance,
            "output_format": "wav",
        },
    )
    response.raise_for_status()
    payload = response.json()
    audio_b64 = payload.get("audio_base64")
    if not audio_b64:
        raise ValueError("60db response did not contain 'audio_base64'")
    return _wav_to_pcm_s16le(base64.b64decode(audio_b64), TTS_SAMPLE_RATE)


def _wav_to_pcm_s16le(wav_bytes: bytes, target_rate: int) -> bytes:
    """Unwrap a WAV container into raw little-endian 16-bit mono PCM.

    Python 3.13 removed ``audioop``, so down-mixing/resampling is done in pure
    Python. In the common case (mono 16-bit at ``target_rate``) this is a no-op
    beyond stripping the WAV header.
    """
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav:
        num_channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        framerate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    if sample_width == 2:
        samples = array("h")
        samples.frombytes(frames)
    elif sample_width == 1:
        samples = array("h", (((b - 128) << 8) for b in frames))
    else:
        raise ValueError(f"Unsupported 60db WAV sample width: {sample_width} bytes")

    if num_channels > 1:
        mono = array("h", bytes(2 * (len(samples) // num_channels)))
        for i in range(len(mono)):
            base = i * num_channels
            mono[i] = int(
                sum(samples[base + c] for c in range(num_channels)) / num_channels
            )
        samples = mono

    samples = _resample_linear(samples, framerate or target_rate, target_rate)

    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def _resample_linear(samples: array, src_rate: int, dst_rate: int) -> array:
    if src_rate == dst_rate or len(samples) == 0:
        return samples
    n = len(samples)
    out_n = max(1, round(n * dst_rate / src_rate))
    out = array("h", bytes(2 * out_n))
    ratio = src_rate / dst_rate
    for i in range(out_n):
        pos = i * ratio
        i0 = int(pos)
        frac = pos - i0
        s0 = samples[i0] if i0 < n else samples[-1]
        s1 = samples[i0 + 1] if i0 + 1 < n else s0
        out[i] = int(s0 + (s1 - s0) * frac)
    return out
