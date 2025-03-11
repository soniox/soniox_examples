import os
import re
import time
import requests

API_BASE = "https://api.soniox.com"
AUDIO_URL = "https://soniox.com/media/examples/coffee_shop.mp3"
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
        "enable_speaker_tags": True,
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

# print each speaker on a new line by matching the spk:NUM tag
line = None
for token in transcript["tokens"]:
    text = token["text"]
    match = re.match(r"^spk:(\d+)$", text)

    if match:
        if line is not None:
            print(line)
        line = f"Speaker {match[1]}:"
    else:
        if line is not None:
            line += text
if line:
    print(line)
