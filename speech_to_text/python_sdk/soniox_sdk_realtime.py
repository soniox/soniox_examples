import os
import argparse
from typing import Optional

from soniox import SonioxClient
from soniox.types import (
    RealtimeSTTConfig,
    StructuredContext,
    TranslationConfig,
    StructuredContextGeneralItem,
    StructuredContextTranslationTerm,
)
from soniox.utils import render_tokens, start_audio_thread, throttle_audio


def get_config(audio_format: str, translation: Optional[str]) -> RealtimeSTTConfig:
    config = RealtimeSTTConfig(
        # Select the model to use.
        # See: soniox.com/docs/stt/models
        model="stt-rt-v4",
        #
        # Set language hints when possible to significantly improve accuracy.
        # See: soniox.com/docs/stt/concepts/language-hints
        language_hints=["en", "es"],
        #
        # Enable language identification. Each token will include a "language" field.
        # See: soniox.com/docs/stt/concepts/language-identification
        enable_language_identification=True,
        #
        # Enable speaker diarization. Each token will include a "speaker" field.
        # See: soniox.com/docs/stt/concepts/speaker-diarization
        enable_speaker_diarization=True,
        #
        # Set context to help the model understand your domain, recognize important terms,
        # and apply custom vocabulary and translation preferences.
        # See: soniox.com/docs/stt/concepts/context
        context=StructuredContext(
            general=[
                StructuredContextGeneralItem(key="domain", value="Healthcare"),
                StructuredContextGeneralItem(
                    key="topic", value="Diabetes management consultation"
                ),
                StructuredContextGeneralItem(key="doctor", value="Dr. Martha Smith"),
                StructuredContextGeneralItem(key="patient", value="Mr. David Miller"),
                StructuredContextGeneralItem(
                    key="organization", value="St John's Hospital"
                ),
            ],
            text="Mr. David Miller visited his healthcare provider last month for a routine follow-up related to diabetes care. The clinician reviewed his recent test results, noted improved glucose levels, and adjusted his medication schedule accordingly. They also discussed meal planning strategies and scheduled the next check-up for early spring.",
            terms=[
                "Celebrex",
                "Zyrtec",
                "Xanax",
                "Prilosec",
                "Amoxicillin Clavulanate Potassium",
            ],
            translation_terms=[
                StructuredContextTranslationTerm(
                    source="Mr. Smith", target="Sr. Smith"
                ),
                StructuredContextTranslationTerm(
                    source="St John's", target="St John's"
                ),
                StructuredContextTranslationTerm(source="stroke", target="ictus"),
            ],
        ),
        #
        # Use endpointing to detect when the speaker stops.
        # It finalizes all non-final tokens right away, minimizing latency.
        # See: soniox.com/docs/stt/rt/endpoint-detection
        enable_endpoint_detection=True,
    )

    # Audio format.
    # See: soniox.com/docs/stt/rt/real-time-transcription#audio-formats
    if audio_format == "auto":
        # Set to "auto" to let Soniox detect the audio format automatically.
        config.audio_format = "auto"
    elif audio_format == "pcm_s16le":
        # Example of a raw audio format; Soniox supports many others as well.
        config.audio_format = "pcm_s16le"
        config.sample_rate = 16000
        config.num_channels = 1
    else:
        raise ValueError(f"Unsupported audio_format: {audio_format}")

    # Translation options.
    # See: soniox.com/docs/stt/rt/real-time-translation#translation-modes
    if translation == "none":
        pass
    elif translation == "one_way":
        # Translates all languages into the target language.
        config.translation = TranslationConfig(
            type="one_way",
            target_language="es",
        )
    elif translation == "two_way":
        # Translates from language_a to language_b and back from language_b to language_a.
        config.translation = TranslationConfig(
            type="two_way",
            language_a="en",
            language_b="es",
        )
    else:
        raise ValueError(f"Unsupported translation: {translation}")

    return config


def run_session(
    client: SonioxClient,
    audio_path: str,
    audio_format: str,
    translation: str,
) -> None:
    config = get_config(audio_format, translation)

    print("Connecting to Soniox...")
    with client.realtime.stt.connect(config=config) as session:
        final_tokens = []

        # Read the audio file and send its bytes to the websocket.
        # Sleep for 0.1 s (100 ms) to simulate real-time streaming.
        start_audio_thread(session, throttle_audio(audio_path, delay_seconds=0.1))
        print("Session started.")

        for event in session.receive_events():
            # Error from server.
            # See: https://soniox.com/docs/stt/api-reference/websocket-api#error-response
            if event.error_code:
                print(f"Error: {event.error_code} - {event.error_message}")

            # Parse tokens from current response.
            non_final_tokens = []
            for token in event.tokens:
                if token.is_final:
                    # Final tokens are returned once and should be appended to final_tokens.
                    final_tokens.append(token)
                else:
                    # Non-final tokens update as more audio arrives; reset them on every response.
                    non_final_tokens.append(token)

            # Render tokens.
            print(render_tokens(final_tokens, non_final_tokens))

            # Session finished.
            if event.finished:
                print("Session finished.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_path", type=str)
    parser.add_argument("--audio_format", default="auto")
    parser.add_argument("--translation", default="none")
    args = parser.parse_args()

    api_key = os.environ.get("SONIOX_API_KEY")
    if api_key is None:
        raise RuntimeError("Missing SONIOX_API_KEY.")

    client = SonioxClient()

    run_session(client, args.audio_path, args.audio_format, args.translation)


if __name__ == "__main__":
    main()
