import argparse
import base64
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from websockets.sync.client import connect

SONIOX_TTS_WEBSOCKET_URL = "wss://tts-rt.soniox.com/tts-websocket"
MODEL = "tts-rt-v1-preview"
VALID_SAMPLE_RATES = [8000, 16000, 24000, 44100, 48000]
VALID_BITRATES = [32000, 64000, 96000, 128000, 192000, 256000, 320000]
VALID_AUDIO_FORMATS = [
    "pcm_f32le",
    "pcm_s16le",
    "pcm_mulaw",
    "pcm_alaw",
    "wav",
    "aac",
    "mp3",
    "opus",
    "flac"
]

STREAM_SPECS = [
    {
        "stream_id": "stream-a",
        "language": "en",
        "voice": "Adrian",
        "lines": [
            "Welcome to Soniox real-time Text-to-Speech. ",
            "This stream demonstrates English speech generation. ",
            "Thank you for listening.",
        ],
    },
    {
        "stream_id": "stream-b",
        "language": "sl",
        "voice": "Maya",
        "lines": [
            "Dobrodošli v sistem Soniox za pretvorbo besedila v govor v realnem času. ",
            "Ta tok prikazuje generiranje slovenskega govora. ",
            "Hvala za poslušanje.",
        ],
    },
    {
        "stream_id": "stream-c",
        "language": "es",
        "voice": "Daniel",
        "lines": [
            "Bienvenido a Soniox texto a voz en tiempo real. ",
            "Este flujo demuestra la generación de voz en español. ",
            "Gracias por escuchar.",
        ],
    },
]


def get_output_path(*, output_path: str, audio_format: str, stream_id: str) -> Path:
    if "." in Path(output_path).name:
        base = Path(output_path)
    else:
        ext = "pcm" if audio_format in ("pcm_s16le", "pcm_f32le", "pcm_mulaw", "pcm_alaw") else audio_format
        base = Path(f"{output_path}.{ext}")
    return base.with_name(f"{base.stem}-{stream_id}{base.suffix}")


def build_stream_config(
    *,
    api_key: str,
    stream_id: str,
    model: str,
    language: str,
    voice: str,
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "api_key": api_key,
        "stream_id": stream_id,
        "model": model,
        "language": language,
        "voice": voice,
        "audio_format": audio_format,
    }
    if sample_rate is not None:
        payload["sample_rate"] = sample_rate
    if bitrate is not None:
        payload["bitrate"] = bitrate
    return payload


def send_stream(
    ws,
    *,
    api_key: str,
    model: str,
    stream: dict[str, Any],
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
) -> None:
    stream_id = stream["stream_id"]

    # Optional delay before starting this stream
    delay = stream.get("delay", 0)
    if delay > 0:
        print(f"Delaying stream {stream_id} by {delay}s...")
        time.sleep(delay)

    # Send stream config to start the stream.
    print(f"Starting stream {stream_id}...")
    ws.send(
        json.dumps(
            build_stream_config(
                api_key=api_key,
                stream_id=stream_id,
                model=model,
                language=stream["language"],
                voice=stream["voice"],
                audio_format=audio_format,
                sample_rate=sample_rate,
                bitrate=bitrate,
            )
        )
    )

    # Send text lines.
    for line in stream["lines"]:
        clean = line.strip()
        if not clean:
            continue
        ws.send(json.dumps({"text": clean, "text_end": False, "stream_id": stream_id}))
        time.sleep(0.15)

    # Signal end of text for this stream.
    ws.send(json.dumps({"text": "", "text_end": True, "stream_id": stream_id}))
    print(f"Finished sending stream {stream_id}.")


def send_requests(
    ws,
    *,
    api_key: str,
    model: str,
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
    streams: list[dict[str, Any]],
) -> None:
    threads: list[threading.Thread] = []
    for stream in streams:
        t = threading.Thread(
            target=send_stream,
            args=(ws,),
            kwargs={
                "api_key": api_key,
                "model": model,
                "stream": stream,
                "audio_format": audio_format,
                "sample_rate": sample_rate,
                "bitrate": bitrate,
            },
            daemon=True,
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


def run_session(
    *,
    api_key: str,
    model: str,
    streams: list[dict[str, Any]],
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
    output_path: str,
) -> None:
    stream_ids = [stream["stream_id"] for stream in streams]
    audio_by_stream: dict[str, list[bytes]] = {stream_id: [] for stream_id in stream_ids}
    terminated: set[str] = set()

    print(f"Connecting to Soniox realtime TTS ({len(streams)} streams)...")
    try:
        with connect(SONIOX_TTS_WEBSOCKET_URL) as ws:
            send_errors: list[Exception] = []

            def send_worker() -> None:
                try:
                    send_requests(
                        ws,
                        api_key=api_key,
                        model=model,
                        audio_format=audio_format,
                        sample_rate=sample_rate,
                        bitrate=bitrate,
                        streams=streams,
                    )
                except Exception as exc:
                    send_errors.append(exc)

            threading.Thread(target=send_worker, daemon=True).start()

            while terminated != set(stream_ids):
                if send_errors:
                    raise RuntimeError(f"Failed to send realtime requests: {send_errors[0]}")
                response = json.loads(ws.recv())
                stream_id = response.get("stream_id")
                if stream_id not in audio_by_stream:
                    continue

                if response.get("error_code") is not None:
                    message = response.get("error_message", "unknown error")
                    raise RuntimeError(
                        f"TTS stream '{stream_id}' failed (code {response['error_code']}): {message}"
                    )

                audio_b64 = response.get("audio")
                if audio_b64:
                    audio_by_stream[stream_id].append(base64.b64decode(audio_b64))

                if response.get("terminated"):
                    terminated.add(stream_id)

        print("All streams terminated.")
    finally:
        for stream_id in stream_ids:
            audio = b"".join(audio_by_stream[stream_id])
            if not audio:
                print(f"No audio file was written for stream {stream_id}.")
                continue
            destination = get_output_path(
                output_path=output_path,
                audio_format=audio_format,
                stream_id=stream_id,
            )
            destination.write_bytes(audio)
            print(f"Wrote stream {stream_id} ({len(audio)} bytes) to {destination.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_format", default="wav")
    parser.add_argument("--output_path", default="tts-multi-stream")
    parser.add_argument("--sample_rate", type=int)
    parser.add_argument("--bitrate", type=int)
    args = parser.parse_args()

    if args.audio_format not in VALID_AUDIO_FORMATS:
        raise ValueError(f"audio_format must be one of {VALID_AUDIO_FORMATS}")
    if args.sample_rate is not None and args.sample_rate not in VALID_SAMPLE_RATES:
        raise ValueError(f"sample_rate must be None or one of {VALID_SAMPLE_RATES}")
    if args.bitrate is not None and args.bitrate not in VALID_BITRATES:
        raise ValueError(f"bitrate must be None or one of {VALID_BITRATES}")

    api_key = os.environ.get("SONIOX_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing SONIOX_API_KEY.\n"
            "1. Get your API key at https://console.soniox.com\n"
            "2. Run: export SONIOX_API_KEY=<YOUR_API_KEY>"
        )

    run_session(
        api_key=api_key,
        model=MODEL,
        streams=STREAM_SPECS,
        audio_format=args.audio_format,
        sample_rate=args.sample_rate,
        bitrate=args.bitrate,
        output_path=args.output_path,
    )


if __name__ == "__main__":
    main()
