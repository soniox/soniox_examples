import os
import time
import argparse
from typing import Optional
import requests
from requests import Session

SONIOX_API_BASE_URL = "https://api.soniox.com"


# Get Soniox STT config.
def get_config(
    audio_url: Optional[str], file_id: Optional[str], translation: Optional[str]
) -> dict:
    config = {
        # Select the model to use.
        # See: soniox.com/docs/stt/models
        "model": "stt-async-v3",
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
        # Optional identifier to track this request (client-defined).
        # See: https://soniox.com/docs/stt/api-reference/transcriptions/create_transcription#request
        "client_reference_id": "MyReferenceId",
        #
        # Audio source (only one can specified):
        # - Public URL of the audio file.
        # - File ID of a previously uploaded file
        # See: https://soniox.com/docs/stt/api-reference/transcriptions/create_transcription#request
        "audio_url": audio_url,
        "file_id": file_id,
    }

    # Webhook.
    # You can set a webhook to get notified when the transcription finishes or fails.
    # See: https://soniox.com/docs/stt/api-reference/transcriptions/create_transcription#request

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


def upload_audio(session: Session, audio_path: str) -> str:
    print("Starting file upload...")
    res = session.post(
        f"{SONIOX_API_BASE_URL}/v1/files",
        files={"file": open(audio_path, "rb")},
    )
    file_id = res.json()["id"]
    print(f"File ID: {file_id}")
    return file_id


def create_transcription(session: Session, config: dict) -> str:
    print("Creating transcription...")
    try:
        res = session.post(
            f"{SONIOX_API_BASE_URL}/v1/transcriptions",
            json=config,
        )
        res.raise_for_status()
        transcription_id = res.json()["id"]
        print(f"Transcription ID: {transcription_id}")
        return transcription_id
    except Exception as e:
        print("error here:", e)


def wait_until_completed(session: Session, transcription_id: str) -> None:
    print("Waiting for transcription...")
    while True:
        res = session.get(f"{SONIOX_API_BASE_URL}/v1/transcriptions/{transcription_id}")
        res.raise_for_status()
        data = res.json()
        if data["status"] == "completed":
            return
        elif data["status"] == "error":
            raise Exception(f"Error: {data.get('error_message', 'Unknown error')}")
        time.sleep(1)


def get_transcription(session: Session, transcription_id: str) -> dict:
    res = session.get(
        f"{SONIOX_API_BASE_URL}/v1/transcriptions/{transcription_id}/transcript"
    )
    res.raise_for_status()
    return res.json()


def delete_transcription(session: Session, transcription_id: str) -> dict:
    res = session.delete(f"{SONIOX_API_BASE_URL}/v1/transcriptions/{transcription_id}")
    res.raise_for_status()


def delete_file(session: Session, file_id: str) -> dict:
    res = session.delete(f"{SONIOX_API_BASE_URL}/v1/files/{file_id}")
    res.raise_for_status()


def delete_all_files(session: Session) -> None:
    files: list[dict] = []
    cursor: str = ""

    while True:
        print("Getting files...")
        res = session.get(f"{SONIOX_API_BASE_URL}/v1/files?cursor={cursor}")
        res.raise_for_status()
        res_json = res.json()
        files.extend(res_json["files"])
        cursor = res_json["next_page_cursor"]
        if cursor is None:
            break

    total = len(files)
    if total == 0:
        print("No files to delete.")
        return

    print(f"Deleting {total} files...")
    for idx, file in enumerate(files):
        file_id = file["id"]
        print(f"Deleting file: {file_id} ({idx + 1}/{total})")
        delete_file(session, file_id)


def delete_all_transcriptions(session: Session) -> None:
    transcriptions: list[dict] = []
    cursor: str = ""

    while True:
        print("Getting transcriptions...")
        res = session.get(f"{SONIOX_API_BASE_URL}/v1/transcriptions?cursor={cursor}")
        res.raise_for_status()
        res_json = res.json()
        for transcription in res_json["transcriptions"]:
            status = transcription["status"]
            # Delete only transcriptions with completed or error status.
            if status in ("completed", "error"):
                transcriptions.append(transcription)
        cursor = res_json["next_page_cursor"]
        if cursor is None:
            break

    total = len(transcriptions)
    if total == 0:
        print("No transcriptions to delete.")
        return

    print(f"Deleting {total} transcriptions...")
    for idx, transcription in enumerate(transcriptions):
        transcription_id = transcription["id"]
        print(f"Deleting transcription: {transcription_id} ({idx + 1}/{total})")
        delete_transcription(session, transcription_id)


# Convert tokens into a readable transcript.
def render_tokens(final_tokens: list[dict]) -> str:
    text_parts: list[str] = []
    current_speaker: Optional[str] = None
    current_language: Optional[str] = None

    # Process all tokens in order.
    for token in final_tokens:
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

    return "".join(text_parts)


def transcribe_file(
    session: Session,
    audio_url: Optional[str],
    audio_path: Optional[str],
    translation: Optional[str],
) -> None:
    if audio_url is not None:
        # Public URL of the audio file to transcribe.
        assert audio_path is None
        file_id = None
    elif audio_path is not None:
        # Local file to be uploaded to obtain file id.
        assert audio_url is None
        file_id = upload_audio(session, audio_path)
    else:
        raise ValueError("Missing audio: audio_url or audio_path must be specified.")

    config = get_config(audio_url, file_id, translation)

    transcription_id = create_transcription(session, config)

    wait_until_completed(session, transcription_id)

    result = get_transcription(session, transcription_id)

    text = render_tokens(result["tokens"])
    print(text)

    delete_transcription(session, transcription_id)

    if file_id is not None:
        delete_file(session, file_id)


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

    # Create an authenticated session.
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {api_key}"

    # Delete all uploaded files.
    if args.delete_all_files:
        delete_all_files(session)
        return

    # Delete all transcriptions.
    if args.delete_all_transcriptions:
        delete_all_transcriptions(session)
        return

    # If not deleting, require one audio source.
    if not (args.audio_url or args.audio_path):
        parser.error("Provide --audio_url or --audio_path (or use a delete flag).")

    transcribe_file(session, args.audio_url, args.audio_path, args.translation)


if __name__ == "__main__":
    main()
