import json
import os
import threading

import requests
from websockets import ConnectionClosedOK
from websockets.sync.client import connect

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = os.environ.get("SONIOX_API_KEY")
websocket_url = "wss://stt-rt.soniox.com/transcribe-websocket"
audio_url = "https://npr-ice.streamguys1.com/live.mp3?ck=1742897559135"


def stream_audio(ws):
    with requests.get(audio_url, stream=True) as res:
        res.raise_for_status()
        for chunk in res.iter_content(chunk_size=4096):
            if chunk:
                ws.send(chunk)
    ws.send("")  # signal end of stream


def main():
    print("Opening WebSocket connection...")

    with connect(websocket_url) as ws:
        # Send start request
        ws.send(
            json.dumps(
                {
                    "api_key": api_key,
                    "audio_format": "auto",  # server detects the format
                    "model": "stt-rt-preview-v2",
                    "language_hints": ["en", "es"],
                }
            )
        )

        # Start streaming audio in background
        threading.Thread(target=stream_audio, args=(ws,), daemon=True).start()

        print(f"Transcription started from {audio_url}")

        final_text = ""

        try:
            while True:
                message = ws.recv()
                res = json.loads(message)

                if res.get("error_code"):
                    print(f"Error: {res['error_code']} - {res['error_message']}")
                    break

                non_final_text = ""

                for token in res.get("tokens", []):
                    if token.get("text"):
                        if token.get("is_final"):
                            final_text += token["text"]
                        else:
                            non_final_text += token["text"]

                print(
                    "\033[2J\033[H"  # clear the screen, move to top-left corner
                    + final_text  # write final text
                    + "\033[34m"  # change text color to blue
                    + non_final_text  # write non-final text
                    + "\033[39m"  # reset text color
                )

                if res.get("finished"):
                    print("\nTranscription complete.")
        except ConnectionClosedOK:
            pass
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
