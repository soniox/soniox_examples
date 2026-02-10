import os
import argparse
from typing import Optional

from soniox import SonioxClient
from soniox.types import (
    CreateTranscriptionConfig,
    StructuredContext,
    TranslationConfig,
    StructuredContextGeneralItem,
    StructuredContextTranslationTerm,
)
from soniox.utils import render_tokens


def get_config(translation: Optional[str]) -> CreateTranscriptionConfig:
    config = CreateTranscriptionConfig(
        # Select the model to use.
        # See: soniox.com/docs/stt/models
        model="stt-async-v4",
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
        # Optional identifier to track this request (client-defined).
        # See: https://soniox.com/docs/stt/api-reference/transcriptions/create_transcription#request
        client_reference_id="MyReferenceId",
    )

    # Webhook.
    # You can set a webhook to get notified when the transcription finishes or fails.
    # See: https://soniox.com/docs/stt/api-reference/transcriptions/create_transcription#request
    # In SDK you can set the following fields:
    # - config.webhook_url
    # - config.webhook_auth_header_name
    # - config.webhook_auth_header_value

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


def transcribe_file(
    client: SonioxClient,
    audio_url: Optional[str],
    audio_path: Optional[str],
    translation: Optional[str],
) -> None:
    if audio_url is not None:
        # Public URL of the audio file to transcribe.
        assert audio_path is None
        file = None
    elif audio_path is not None:
        # Local file to be uploaded to obtain file id.
        assert audio_url is None
        file = client.files.upload(audio_path)
    else:
        raise ValueError("Missing audio: audio_url or audio_path must be specified.")

    config = get_config(translation)

    print("Creating transcription...")
    transcription = client.transcriptions.create(
        config=config, file_id=file.id if file else None, audio_url=audio_url
    )
    print("Waiting for transcription...")
    client.transcriptions.wait(transcription.id)

    result = client.transcriptions.get_transcript(transcription.id)

    print(render_tokens(result.tokens, []))

    client.transcriptions.delete(transcription.id)

    if file is not None:
        client.files.delete(file.id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--audio_url", help="Public URL of the audio file to transcribe."
    )
    parser.add_argument(
        "--audio_path", help="Path to a local audio file to transcribe."
    )
    parser.add_argument("--delete_all_files", action="store_true")
    parser.add_argument("--delete_all_transcriptions", action="store_true")
    parser.add_argument("--translation", default="none")
    args = parser.parse_args()

    api_key = os.environ.get("SONIOX_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing SONIOX_API_KEY.\n"
            "1. Get your API key at https://console.soniox.com\n"
            "2. Run: export SONIOX_API_KEY=<YOUR_API_KEY>"
        )

    client = SonioxClient()

    # Delete all uploaded files.
    if args.delete_all_files:
        print("Deleting all files...")
        client.files.delete_all()
        return

    # Delete all transcriptions.
    if args.delete_all_transcriptions:
        print("Deleting all transcriptions...")
        client.transcriptions.delete_all()
        return

    # If not deleting, require one audio source.
    if not (args.audio_url or args.audio_path):
        parser.error("Provide --audio_url or --audio_path (or use a delete flag).")

    transcribe_file(client, args.audio_url, args.audio_path, args.translation)


if __name__ == "__main__":
    main()
