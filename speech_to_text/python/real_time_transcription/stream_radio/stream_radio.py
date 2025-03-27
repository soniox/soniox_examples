import json
import os
import threading
import time
import requests
from websockets import ConnectionClosedOK, ConnectionClosedError
from websockets.sync.client import connect

WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket"
RADIO_URL = "https://npr-ice.streamguys1.com/live.mp3?ck=1742897559135"

API_KEY = os.environ.get("SONIOX_API_KEY")
if API_KEY is None:
    raise KeyError("Missing SONIOX_API_KEY env variable. Please configure it.")

# Connect to WebSocket API
print("Opening WebSocket connection...")
with connect(WEBSOCKET_URL) as ws:
    # Send start request
    ws.send(
        json.dumps(
            {
                "api_key": API_KEY,
                "audio_format": "auto",  # let the API detect the format
                "model": "stt-rt-preview",
            }
        )
    )

    def send_audio():
        try:
            with requests.get(RADIO_URL, stream=True) as response:
                response.raise_for_status()

                chunk_size = 4096

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        ws.send(chunk)
                        time.sleep(0.12)

            # Signal end of file
            ws.send("")

        except Exception as e:
            print(f"Error sending audio: {e}")

    # Start a thread to send audio
    send_audio_thread = threading.Thread(target=send_audio)
    send_audio_thread.start()

    print(f"Transcription started from {RADIO_URL}")

    # Receive and process text messages
    try:
        while True:
            message = ws.recv()
            res = json.loads(message)

            if res.get("error_code"):
                print(f'\nError: {res["error_code"]} {res["error_message"]}')
                break

            for token in res.get("tokens", []):
                if token.get("text"):
                    # print out transcribed words
                    print(token["text"], end="", flush=True)

            if res.get("finished"):
                print("\nTranscription done.")

    except ConnectionClosedOK:
        print("\nConnection closed.")

    except ConnectionClosedError as ex:
        print("\nConnection error occurred: ", ex)

    except Exception as e:
        print(f"\nUnexpected error: {e}")

    finally:
        send_audio_thread.join()
        print("\nTranscription process ended.")
