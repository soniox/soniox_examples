import json
import os
import threading
import time
import argparse
from typing import Optional

from websockets import ConnectionClosedOK
from websockets.sync.client import connect

SONIOX_WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket"


# Get Soniox STT config.
def get_config(api_key: str, audio_format: str, translation: str) -> dict:
    config = {
        # Get your API key at console.soniox.com, then run: export SONIOX_API_KEY=<YOUR_API_KEY>
        "api_key": api_key,
        #
        # Select the model to use.
        # See: soniox.com/docs/stt/models
        "model": "stt-rt-v3",
        #
        # Set language hints when possible to significantly improve accuracy.
        # See: soniox.com/docs/stt/concepts/language-hints
        "language_hints": ["en", "es"],
        #
        # Enable language identification. Each token will include a "language" field.
        # See: soniox.com/docs/stt/concepts/language-identification
        "enable_language_identification": True,
        #
        # Enable speaker diarization. Each token will include a "speaker" field.
        # See: soniox.com/docs/stt/concepts/speaker-diarization
        "enable_speaker_diarization": True,
        #
        # Set context to help the model understand your domain, recognize important terms,
        # and apply custom vocabulary and translation preferences.
        # See: soniox.com/docs/stt/concepts/context
        "context": {
            "general": [
                {"key": "domain", "value": "Healthcare"},
                {"key": "topic", "value": "Diabetes management consultation"},
                {"key": "doctor", "value": "Dr. Martha Smith"},
                {"key": "patient", "value": "Mr. David Miller"},
                {"key": "organization", "value": "St John's Hospital"},
            ],
            "text": "Mr. David Miller visited his healthcare provider last month for a routine follow-up related to diabetes care. The clinician reviewed his recent test results, noted improved glucose levels, and adjusted his medication schedule accordingly. They also discussed meal planning strategies and scheduled the next check-up for early spring.",
            "terms": [
                "Celebrex",
                "Zyrtec",
                "Xanax",
                "Prilosec",
                "Amoxicillin Clavulanate Potassium",
            ],
            "translation_terms": [
                {"source": "Mr. Smith", "target": "Sr. Smith"},
                {"source": "St John's", "target": "St John's"},
                {"source": "stroke", "target": "ictus"},
            ],
        },
        #
        # Use endpointing to detect when the speaker stops.
        # It finalizes all non-final tokens right away, minimizing latency.
        # See: soniox.com/docs/stt/rt/endpoint-detection
        "enable_endpoint_detection": True,
    }

    # Audio format.
    # See: soniox.com/docs/stt/rt/real-time-transcription#audio-formats
    if audio_format == "auto":
        # Set to "auto" to let Soniox detect the audio format automatically.
        config["audio_format"] = "auto"
    elif audio_format == "pcm_s16le":
        # Example of a raw audio format; Soniox supports many others as well.
        config["audio_format"] = "pcm_s16le"
        config["sample_rate"] = 16000
        config["num_channels"] = 1
    else:
        raise ValueError(f"Unsupported audio_format: {audio_format}")

    # Translation options.
    # See: soniox.com/docs/stt/rt/real-time-translation#translation-modes
    if translation == "none":
        pass
    elif translation == "one_way":
        # Translates all languages into the target language.
        config["translation"] = {
            "type": "one_way",
            "target_language": "es",
        }
    elif translation == "two_way":
        # Translates from language_a to language_b and back from language_b to language_a.
        config["translation"] = {
            "type": "two_way",
            "language_a": "en",
            "language_b": "es",
        }
    else:
        raise ValueError(f"Unsupported translation: {translation}")

    return config


# Read the audio file and send its bytes to the websocket.
def stream_audio(audio_path: str, ws) -> None:
    with open(audio_path, "rb") as fh:
        while True:
            data = fh.read(3840)
            if len(data) == 0:
                break
            ws.send(data)
            # Sleep for 120 ms to simulate real-time streaming.
            time.sleep(0.120)

    # Empty string signals end-of-audio to the server
    ws.send("")


# Convert tokens into a readable transcript.
def render_tokens(final_tokens: list[dict], non_final_tokens: list[dict]) -> str:
    text_parts: list[str] = []
    current_speaker: Optional[str] = None
    current_language: Optional[str] = None

    # Process all tokens in order.
    for token in final_tokens + non_final_tokens:
        text = token["text"]
        speaker = token.get("speaker")
        language = token.get("language")
        is_translation = token.get("translation_status") == "translation"

        # Speaker changed -> add a speaker tag.
        if speaker is not None and speaker != current_speaker:
            if current_speaker is not None:
                text_parts.append("\n\n")
            current_speaker = speaker
            current_language = None  # Reset language on speaker changes.
            text_parts.append(f"Speaker {current_speaker}:")

        # Language changed -> add a language or translation tag.
        if language is not None and language != current_language:
            current_language = language
            prefix = "[Translation] " if is_translation else ""
            text_parts.append(f"\n{prefix}[{current_language}] ")
            text = text.lstrip()

        text_parts.append(text)

    text_parts.append("\n===============================")

    return "".join(text_parts)


def run_session(
    api_key: str,
    audio_path: str,
    audio_format: str,
    translation: str,
) -> None:
    config = get_config(api_key, audio_format, translation)

    print("Connecting to Soniox...")
    with connect(SONIOX_WEBSOCKET_URL) as ws:
        # Send first request with config.
        ws.send(json.dumps(config))

        # Start streaming audio in the background.
        threading.Thread(
            target=stream_audio,
            args=(audio_path, ws),
            daemon=True,
        ).start()

        print("Session started.")

        final_tokens: list[dict] = []

        try:
            while True:
                message = ws.recv()
                res = json.loads(message)

                # Error from server.
                # See: https://soniox.com/docs/stt/api-reference/websocket-api#error-response
                if res.get("error_code") is not None:
                    print(f"Error: {res['error_code']} - {res['error_message']}")
                    break

                # Parse tokens from current response.
                non_final_tokens: list[dict] = []
                for token in res.get("tokens", []):
                    if token.get("text"):
                        if token.get("is_final"):
                            # Final tokens are returned once and should be appended to final_tokens.
                            final_tokens.append(token)
                        else:
                            # Non-final tokens update as more audio arrives; reset them on every response.
                            non_final_tokens.append(token)

                # Render tokens.
                text = render_tokens(final_tokens, non_final_tokens)
                print(text)

                # Session finished.
                if res.get("finished"):
                    print("Session finished.")

        except ConnectionClosedOK:
            # Normal, server closed after finished.
            pass
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_path", type=str)
    parser.add_argument("--audio_format", default="auto")
    parser.add_argument("--translation", default="none")
    args = parser.parse_args()

    api_key = os.environ.get("SONIOX_API_KEY")
    if api_key is None:
        raise RuntimeError("Missing SONIOX_API_KEY.")

    run_session(api_key, args.audio_path, args.audio_format, args.translation)


if __name__ == "__main__":
    main()
