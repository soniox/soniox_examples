import argparse
import os
from pathlib import Path
from typing import Any

from soniox import SonioxClient
from soniox.errors import SonioxAPIError
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


def get_config(
    *,
    text: str,
    model: str,
    language: str,
    voice: str,
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
) -> dict[str, Any]:
    config: dict[str, Any] = {
        # Select the model to use.
        # See: soniox.com/docs/tts/models
        "model": model,
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
        #
        # Input text.
        "text": text,
    }

    if sample_rate is not None:
        config["sample_rate"] = sample_rate
    if bitrate is not None:
        config["bitrate"] = bitrate

    return config


def generate_speech(
    client: SonioxClient,
    config: dict[str, Any],
    output_path: str | None,
) -> None:
    destination = (
        Path(output_path)
        if output_path
        else output_file_for_audio_format(config["audio_format"], "tts_async")
    )

    print("Generating speech...")
    written = client.tts.generate_to_file(destination, **config)
    print(f"Wrote {written} bytes to {destination.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--text",
        default=(
            "Soniox Text-to-Speech turns written text into natural, expressive audio "
            "with high accuracy. It is designed for conversational agents, narration, "
            "and accessible experiences, with low latency and high-quality voices."
        ),
        help="Text to generate into speech.",
    )
    parser.add_argument("--model", default="tts-rt-v1")
    parser.add_argument("--language", default="en")
    parser.add_argument("--voice", default="Adrian")
    parser.add_argument("--audio_format", default="wav")
    parser.add_argument("--sample_rate", type=int)
    parser.add_argument("--bitrate", type=int)
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
    config = get_config(
        text=args.text,
        model=args.model,
        language=args.language,
        voice=args.voice,
        audio_format=args.audio_format,
        sample_rate=args.sample_rate,
        bitrate=args.bitrate,
    )
    try:
        generate_speech(client, config, args.output_path)
    except SonioxAPIError as exc:
        print("Soniox API error:", exc)
        if exc.request_id:
            print("  request_id:", exc.request_id)
    finally:
        client.close()

if __name__ == "__main__":
    main()
