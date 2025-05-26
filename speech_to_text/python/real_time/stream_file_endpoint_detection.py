import json
import os
import threading
import time

from websockets import ConnectionClosedOK
from websockets.sync.client import connect

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = os.environ.get("SONIOX_API_KEY")
websocket_url = "wss://stt-rt.soniox.com/transcribe-websocket"
file_to_transcribe = "coffee_shop.pcm_s16le"


def stream_audio(ws):
    with open(file_to_transcribe, "rb") as fh:
        while True:
            data = fh.read(3840)
            if len(data) == 0:
                break
            ws.send(data)
            time.sleep(0.12)  # sleep for 120 ms
    ws.send("")  # signal end of stream


def main():
    print("Opening WebSocket connection...")

    with connect(websocket_url) as ws:
        # Send start request
        ws.send(
            json.dumps(
                {
                    "api_key": api_key,
                    "audio_format": "pcm_s16le",
                    "sample_rate": 16000,
                    "num_channels": 1,
                    "model": "stt-rt-preview",
                    "language_hints": ["en", "es"],
                    "enable_non_final_tokens": False,
                    "enable_endpoint_detection": True,
                }
            )
        )

        # Start streaming audio in background
        threading.Thread(target=stream_audio, args=(ws,), daemon=True).start()

        print("Transcription started")

        current_text = ""

        try:
            while True:
                message = ws.recv()
                res = json.loads(message)

                if res.get("error_code"):
                    print(f"Error: {res['error_code']} - {res['error_message']}")
                    break

                for token in res.get("tokens", []):
                    if token.get("text"):
                        if token["text"] == "<end>":
                            print(current_text)
                            current_text = ""
                        elif not current_text:
                            current_text = token["text"].lstrip()
                        else:
                            current_text += token["text"]

                if res.get("finished"):
                    if current_text:
                        print(current_text)

                    print("\nTranscription complete.")
        except ConnectionClosedOK:
            pass
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
