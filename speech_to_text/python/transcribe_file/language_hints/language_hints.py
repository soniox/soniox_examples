import os
import time
import requests

API_BASE = "https://api.soniox.com"
AUDIO_URL = "https://soniox.com/media/examples/multiple_languages_one_speaker.mp3"
API_KEY = os.environ["SONIOX_API_KEY"]

session = requests.Session()
session.headers["Authorization"] = f"Bearer {API_KEY}"

# 1. Start a new transcription session by sending the audio URL to the API
print("Starting transcription...")

response = session.post(
    f"{API_BASE}/v1/transcriptions",
    json={
        "audio_url": AUDIO_URL,
        "model": "stt-async-preview",
        "language_hints": ["en", "es", "fr", "pt"],  # include list of language hints
    },
)
response.raise_for_status()
transcription = response.json()
transcription_id = transcription["id"]

print(f"Transcription started with ID: {transcription_id}")

# 2. Poll the transcription endpoint until the status is 'completed'
while True:
    response = session.get(f"{API_BASE}/v1/transcriptions/{transcription_id}")
    response.raise_for_status()
    transcription = response.json()

    status = transcription.get("status")
    if status == "error":
        raise Exception(
            f"Transcription error: {transcription.get('error_message', 'Unknown error')}"
        )
    elif status == "completed":
        break

    # Wait for 1 second before polling again
    time.sleep(1)

# 3. Retrieve the final transcript once transcription is completed
response = session.get(f"{API_BASE}/v1/transcriptions/{transcription_id}/transcript")
response.raise_for_status()
transcript = response.json()

print("Transcript:")
print(transcript["text"])
