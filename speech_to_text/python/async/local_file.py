import os
import time

import requests

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = os.environ["SONIOX_API_KEY"]
api_base = "https://api.soniox.com"
file_to_transcribe = "coffee_shop.mp3"

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
    print("Starting file upload...")

    res = session.post(
        f"{api_base}/v1/files",
        files={
            "file": open(file_to_transcribe, "rb"),
        },
    )
    file_id = res.json()["id"]
    print(f"File ID: {file_id}")

    print("Starting transcription...")

    res = session.post(
        f"{api_base}/v1/transcriptions",
        json={
            "file_id": file_id,
            "model": "stt-async-preview",
            "language_hints": ["en", "es"],
        },
    )
    res.raise_for_status()
    transcription_id = res.json()["id"]
    print(f"Transcription ID: {transcription_id}")

    poll_until_complete(transcription_id)

    # Get the transcript text
    res = session.get(f"{api_base}/v1/transcriptions/{transcription_id}/transcript")
    res.raise_for_status()
    print("Transcript:")
    print(res.json()["text"])

    # Delete the transcription
    res = session.delete(f"{api_base}/v1/transcriptions/{transcription_id}")
    res.raise_for_status()

    # Delete the file
    res = session.delete(f"{api_base}/v1/files/{file_id}")
    res.raise_for_status()


if __name__ == "__main__":
    main()
