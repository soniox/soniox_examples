import os
import requests

API_BASE = "https://api.soniox.com"
AUDIO_URL = "https://soniox.com/media/examples/coffee_shop.mp3"

# Update to your own webhook url
WEBHOOK_URL = "https://example.com/webhook"

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
API_KEY = os.environ["SONIOX_API_KEY"]

session = requests.Session()
session.headers["Authorization"] = f"Bearer {API_KEY}"

# Start a new transcription session and include webhook_url
res = session.post(
    f"{API_KEY}/v1/transcriptions",
    json={
        "audio_url": AUDIO_URL,
        "webhook_url": WEBHOOK_URL,
        "model": "stt-async-preview",
    },
)
res.raise_for_status()
