import os
import time

import requests

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = os.environ["SONIOX_API_KEY"]
api_base = "https://api.soniox.com"
audio_url = "https://soniox.com/media/examples/coffee_shop.mp3"

session = requests.Session()
session.headers["Authorization"] = f"Bearer {api_key}"


def poll_until_complete(transcription_id):
    while True:
        res = session.get(f"{api_base}/v1/transcriptions/{transcription_id}")
        res.raise_for_status()
        data = res.json()
        if data["status"] == "completed":
            return
        elif data["status"] == "error":
            raise Exception(
                f"Transcription failed: {data.get('error_message', 'Unknown error')}"
            )
        time.sleep(1)


def main():
    print("Starting transcription...")

    res = session.post(
        f"{api_base}/v1/transcriptions",
        json={
            "audio_url": audio_url,
            "model": "stt-async-preview",
            "language_hints": ["en", "es"],
            "enable_speaker_diarization": True,
        },
    )
    res.raise_for_status()
    transcription_id = res.json()["id"]
    print(f"Transcription ID: {transcription_id}")

    # Poll until transcription is done
    poll_until_complete(transcription_id)

    # Get the transcript text
    res = session.get(f"{api_base}/v1/transcriptions/{transcription_id}/transcript")
    res.raise_for_status()

    # Prepare transcript with speakers
    text = ""
    speaker = ""

    for token in res.json()["tokens"]:
        token_text = token["text"]

        if token.get("speaker") and token.get("speaker") != speaker:
            if speaker:
                text += "\n"
            speaker = token["speaker"]
            text += f"Speaker {speaker}: "
            token_text = token_text.lstrip()

        text += token_text

    print("Transcript:")
    print(text)

    # Delete the transcription
    res = session.delete(f"{api_base}/v1/transcriptions/{transcription_id}")
    res.raise_for_status()


if __name__ == "__main__":
    main()
