import os

import requests

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = os.environ["SONIOX_API_KEY"]
api_base = "https://api.soniox.com"
audio_url = "https://soniox.com/media/examples/coffee_shop.mp3"

session = requests.Session()
session.headers["Authorization"] = f"Bearer {api_key}"


def main():
    # Start a new transcription session and include webhook_url
    print("Starting transcription...")

    res = session.post(
        f"{api_base}/v1/transcriptions",
        json={
            "audio_url": audio_url,
            "model": "stt-async-preview",
            "language_hints": ["en", "es"],
            "webhook_url": "https://example.com/webhook",
        },
    )
    res.raise_for_status()

    # When you receive the Webhook, get the transcript and delete the
    # transcription.


if __name__ == "__main__":
    main()
