import argparse
import os
from typing import Any, Optional

import requests
from requests import Session

SONIOX_TTS_URL = "https://tts-rt.soniox.com/tts"
MODEL = "tts-rt-v1"
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


def get_output_path(*, output_path: str, audio_format: str) -> str:
    """
    Generates the resulting output path for the given audio format.
    """
    if "." in os.path.basename(output_path):
        return output_path
    ext = "pcm" if audio_format in ("pcm_s16le", "pcm_f32le", "pcm_mulaw", "pcm_alaw") else audio_format
    return f"{output_path}.{ext}"


# Get Soniox TTS config.
def get_config(
    *,
    language: str,
    voice: str,
    audio_format: str,
    text: str,
    sample_rate: Optional[int],
    bitrate: Optional[int],
) -> dict:
    config: dict[str, Any] = {
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
    session: Session,
    tts_url: str,
    config: dict,
    output_path: str,
) -> None:
    print("Connecting to Soniox...")
    res = session.post(tts_url, json=config, stream=True)
    if res.status_code != 200:
        try:
            err = res.json()
        except Exception:
            err = {"error_message": res.text}
        raise RuntimeError(
            f"TTS request failed (status={res.status_code}, "
            f"error_code={err.get('error_code')}, "
            f"error_message={err.get('error_message')})"
        )

    bytes_written = 0
    with open(output_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=8192):
            if not chunk:
                continue
            f.write(chunk)
            bytes_written += len(chunk)

    print(f"Wrote {bytes_written} bytes to {output_path}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--text",
        default=(
            "Soniox Text-to-Speech turns written text into natural, expressive audio "
            "with high accuracy. It is designed for conversational agents, narration, "
            "and accessible experiences, with low latency and high-quality voices."
        ),
    )
    parser.add_argument("--language", default="en")
    parser.add_argument("--voice", default="Adrian")
    parser.add_argument("--audio_format", default="wav")
    parser.add_argument("--sample_rate", type=int)
    parser.add_argument("--bitrate", type=int)
    parser.add_argument("--output_path", default="tts-rest")
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

    final_output_path = get_output_path(
        output_path=args.output_path, audio_format=args.audio_format
    )
    config = get_config(
        language=args.language,
        voice=args.voice,
        audio_format=args.audio_format,
        text=args.text,
        sample_rate=args.sample_rate,
        bitrate=args.bitrate,
    )

    # Create an authenticated session.
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    generate_speech(session, SONIOX_TTS_URL, config, final_output_path)


if __name__ == "__main__":
    main()
