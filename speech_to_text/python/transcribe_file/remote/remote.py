import os
import time
import requests

API_BASE = "https://api.soniox.com"
AUDIO_URL = "https://soniox.com/media/examples/coffee_shop.mp3"

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
API_KEY = os.environ["SONIOX_API_KEY"]

# Create a requests session and set the Authorization header
session = requests.Session()
session.headers["Authorization"] = f"Bearer {API_KEY}"

# 1. Start a new transcription session by sending the audio URL to the API
print("Starting transcription...")
response = session.post(
    f"{API_BASE}/v1/transcriptions",
    json={
        "audio_url": AUDIO_URL,
        "model": "stt-async-preview",
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
        # Stop polling when the transcription is complete
        break

    # Wait for 1 second before polling again
    time.sleep(1)

# 3. Retrieve the final transcript once transcription is completed
response = session.get(f"{API_BASE}/v1/transcriptions/{transcription_id}/transcript")
response.raise_for_status()
transcript = response.json()

# Print the transcript text
print("Transcript:")
print(transcript["text"])
