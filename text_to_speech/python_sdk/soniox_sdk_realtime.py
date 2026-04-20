import argparse
import os
import threading
import time
from pathlib import Path
from uuid import uuid4

from soniox import SonioxClient
from soniox.errors import SonioxRealtimeError
from soniox.types import RealtimeTTSConfig
from soniox.utils import output_file_for_audio_format

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


def get_config(
    model: str,
    language: str,
    voice: str,
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
    stream_id: str | None,
) -> RealtimeTTSConfig:
    config = RealtimeTTSConfig(
        # Stream id for this realtime TTS session.
        # If omitted, a random id is generated.
        stream_id=stream_id or f"tts-{uuid4()}",
        #
        # Select the model to use.
        # See: soniox.com/docs/tts/models
        model=model,
        #
        # Set the language of the input text.
        # See: soniox.com/docs/tts/languages
        language=language,
        #
        # Select the voice to use.
        # See: soniox.com/docs/tts/voices
        voice=voice,
        #
        # Set output audio format and optional encoding parameters.
        # See: soniox.com/docs/tts/api-reference/websocket-api
        audio_format=audio_format,
        sample_rate=sample_rate,
        bitrate=bitrate,
    )

    return config


def run_session(
    client: SonioxClient,
    lines: list[str],
    model: str,
    language: str,
    voice: str,
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
    stream_id: str | None,
    output_path: str | None,
) -> None:
    # Build a realtime Text-to-Speech session configuration.
    config = get_config(
        model=model,
        language=language,
        voice=voice,
        audio_format=audio_format,
        sample_rate=sample_rate,
        bitrate=bitrate,
        stream_id=stream_id,
    )
    sanitized_lines = [line.strip() for line in lines if line.strip()]
    if not sanitized_lines:
        raise ValueError("Text is empty after parsing.")

    destination = (
        Path(output_path)
        if output_path
        else output_file_for_audio_format(audio_format, "tts_realtime")
    )
    print("Connecting to Soniox...")
    audio_chunks: list[bytes] = []
    try:
        with client.realtime.tts.connect(config=config) as session:
            print("Session started.")
            send_errors: list[Exception] = []

            def send_worker() -> None:
                try:
                    for line in sanitized_lines:
                        session.send_text_chunk(line, text_end=False)
                        time.sleep(0.1)
                    session.finish()
                except Exception as exc:
                    send_errors.append(exc)

            threading.Thread(target=send_worker, daemon=True).start()
            # Receive streamed audio chunks from the websocket.
            for audio_chunk in session.receive_audio_chunks():
                audio_chunks.append(audio_chunk)
            if send_errors:
                raise RuntimeError(f"Failed to send realtime text: {send_errors[0]}")
            print("Session finished.")
    finally:
        audio = b"".join(audio_chunks)
        if audio:
            destination.write_bytes(audio)
            print(f"Wrote {len(audio)} bytes to {destination.resolve()}")
        else:
            print("No audio file was written.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--line",
        action="append",
        default=None,
        help="Line to send to realtime TTS (repeat --line for multiple lines).",
    )
    parser.add_argument("--model", default="tts-rt-v1-preview")
    parser.add_argument("--language", default="en")
    parser.add_argument("--voice", default="Adrian")
    parser.add_argument("--audio_format", default="wav")
    parser.add_argument("--sample_rate", type=int)
    parser.add_argument("--bitrate", type=int)
    parser.add_argument("--stream_id", help="Optional stream id.")
    parser.add_argument(
        "--output_path",
        help="Optional output file path. If omitted, a timestamped path is generated.",
    )
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

    client = SonioxClient(api_key=api_key)

    try:
        run_session(
            client=client,
            lines=args.line or DEFAULT_LINES,
            model=args.model,
            language=args.language,
            voice=args.voice,
            audio_format=args.audio_format,
            sample_rate=args.sample_rate,
            bitrate=args.bitrate,
            stream_id=args.stream_id,
            output_path=args.output_path,
        )
    except SonioxRealtimeError as exc:
        print("Soniox realtime error:", exc)
    finally:
        client.close()


if __name__ == "__main__":
    main()
