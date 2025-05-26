import json
import os
import threading
import time

import requests
from websockets import ConnectionClosedOK
from websockets.sync.client import connect

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = os.environ.get("SONIOX_API_KEY")
websocket_url = "wss://stt-rt.soniox.com/transcribe-websocket"
file_to_transcribe = "coffee_shop.pcm_s16le"


def stream_audio(ws):
    with open(file_to_transcribe, "rb") as fh:
        start = time.monotonic()
        finalized = False
        while True:
            if time.monotonic() - start > 6 and not finalized:
                # Finalize current audio.
                ws.send('{"type": "finalize"}')
                finalized = True
                # Wait for 30 seconds but send keepalive every 10 seconds.
                for _ in range(3):
                    time.sleep(10)
                    ws.send('{"type": "keepalive"}')
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
                }
            )
        )

        # Start streaming audio in background
        threading.Thread(target=stream_audio, args=(ws,), daemon=True).start()

        print("Transcription started")

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
