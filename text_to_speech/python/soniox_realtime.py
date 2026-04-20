import argparse
import base64
import json
import os
import threading
import time
from typing import Any

from websockets import ConnectionClosedOK
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
    "flac",
]
DEFAULT_LINES = [
    "Welcome to Soniox real-time Text-to-Speech. ",
    "As text is streamed in, audio streams back in parallel with high accuracy, ",
    "so your application can start playing speech ",
    "within milliseconds of the first word.",
]


def get_output_path(*, output_path: str, audio_format: str) -> str:
    """
    Generates the resulting output path for the given audio format.
    """
    if "." in os.path.basename(output_path):
        return output_path
    ext = "pcm" if audio_format in ("pcm_s16le", "pcm_s16be") else audio_format
    return f"{output_path}.{ext}"


# Get Soniox TTS config.
def get_config(
    api_key: str,
    stream_id: str,
    language: str,
    voice: str,
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
) -> dict:
    config: dict[str, Any] = {
        # Get your API key at console.soniox.com, then run: export SONIOX_API_KEY=<YOUR_API_KEY>
        "api_key": api_key,
        #
        # Client-defined stream id to identify this realtime request.
        "stream_id": stream_id,
        #
        # Select the model to use.
        # See: soniox.com/docs/tts/models
        "model": MODEL,
        #
        # Set the language of the input text.
        # See: soniox.com/docs/tts/languages
        "language": language,
        #
        # Select the voice to use.
        # See: soniox.com/docs/tts/voices
        "voice": voice,
        #
        # Audio format.
        # See: soniox.com/docs/tts/audio-formats
        "audio_format": audio_format,
    }

    if sample_rate is not None:
        config["sample_rate"] = sample_rate
    if bitrate is not None:
        config["bitrate"] = bitrate

    return config


def get_text_request(text: str, stream_id: str, text_end: bool) -> dict:
    return {
        "text": text,
        "text_end": text_end,
        "stream_id": stream_id,
    }


# Stream text lines to the websocket.
def stream_text(lines: list[str], stream_id: str, ws) -> None:
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
        ws.send(json.dumps(get_text_request(clean_line, stream_id, text_end=False)))
        # Sleep for 100 ms to simulate real-time streaming.
        time.sleep(0.1)

    # Send text_end=true after the last chunk.
    ws.send(json.dumps(get_text_request("", stream_id, text_end=True)))


def send_requests(
    ws,
    api_key: str,
    lines: list[str],
    language: str,
    voice: str,
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
    stream_id: str,
) -> None:
    config = get_config(
        api_key=api_key,
        stream_id=stream_id,
        language=language,
        voice=voice,
        audio_format=audio_format,
        sample_rate=sample_rate,
        bitrate=bitrate,
    )
    ws.send(json.dumps(config))
    stream_text(lines, stream_id, ws)


def run_session(
    api_key: str,
    lines: list[str],
    language: str,
    voice: str,
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
    stream_id: str,
    output_path: str,
) -> None:
    print("Connecting to Soniox...")
    with connect(SONIOX_TTS_WEBSOCKET_URL) as ws:
        send_errors: list[Exception] = []

        def send_worker() -> None:
            try:
                send_requests(
                    ws,
                    api_key,
                    lines,
                    language,
                    voice,
                    audio_format,
                    sample_rate,
                    bitrate,
                    stream_id,
                )
            except Exception as exc:
                send_errors.append(exc)

        # Send config and text in the background while receiving responses.
        threading.Thread(
            target=send_worker,
            daemon=True,
        ).start()

        print("Session started.")
        audio_chunks: list[bytes] = []

        try:
            while True:
                if send_errors:
                    raise RuntimeError(f"Failed to send realtime requests: {send_errors[0]}")
                message = ws.recv()
                res = json.loads(message)

                # Error from server.
                if res.get("error_code") is not None:
                    print(f"Error: {res['error_code']} - {res['error_message']}")
                    break

                # Collect audio bytes from base64-encoded chunks.
                audio_b64 = res.get("audio")
                if audio_b64:
                    audio_chunks.append(base64.b64decode(audio_b64))

                # Session finished.
                if res.get("terminated"):
                    break

        except ConnectionClosedOK:
            # Normal, server closed after finished.
            pass
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            audio_data = b"".join(audio_chunks)
            if audio_data:
                destination = get_output_path(output_path=output_path, audio_format=audio_format)
                with open(destination, "wb") as fh:
                    fh.write(audio_data)
                print(f"Wrote {len(audio_data)} bytes to {destination}")
            else:
                print("No audio file was written.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--line",
        action="append",
        default=None,
        help="Line to send to realtime TTS (repeat --line for multiple lines).",
    )
    parser.add_argument("--language", default="en")
    parser.add_argument("--voice", default="Adrian")
    parser.add_argument("--audio_format", default="wav")
    parser.add_argument("--stream_id", default="stream-1")
    parser.add_argument("--output_path", default="tts-ws")
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
        lines=args.line or DEFAULT_LINES,
        language=args.language,
        voice=args.voice,
        audio_format=args.audio_format,
        sample_rate=args.sample_rate,
        bitrate=args.bitrate,
        stream_id=args.stream_id,
        output_path=args.output_path,
    )


if __name__ == "__main__":
    main()
