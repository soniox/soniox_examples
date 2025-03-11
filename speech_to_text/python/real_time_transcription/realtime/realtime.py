import json
import os
import threading
import time
from websockets import ConnectionClosedOK, ConnectionClosedError
from websockets.sync.client import connect

WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket"
FILE_TO_STREAM = "coffee_shop.pcm_s16le"

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
API_KEY = os.environ.get("SONIOX_API_KEY")
if API_KEY is None:
    raise KeyError(
        "Your API key is missing. Please set the SONIOX_API_KEY environment variable."
    )

# Connect to WebSocket API
print("Opening WebSocket connection...")
with connect(WEBSOCKET_URL) as ws:
    # Send start request
    ws.send(
        json.dumps(
            {
                "api_key": API_KEY,
                "audio_format": "pcm_s16le",
                "sample_rate": 16000,
                "num_channels": 1,
                "model": "stt-rt-preview",
                "language_hints": [],
            }
        )
    )

    def send_audio():
        # Read and send audio data from file over WebSocket connection
        with open(FILE_TO_STREAM, "rb") as fh:
            while True:
                data = fh.read(3840)
                if len(data) == 0:
                    break
                ws.send(data)
                # Sleep for 120 ms
                time.sleep(0.12)

        # Signal end of file
        ws.send("")

    # Start a thread to send audio
    send_audio_thread = threading.Thread(target=send_audio)
    send_audio_thread.start()
    
    print("Transcription started.")

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
                    # Print out transcribed words
                    print(token["text"], end="", flush=True)
            
            if res.get("finished"):
                print("\nTranscription done.")

    except ConnectionClosedOK:
        pass

    except ConnectionClosedError as ex:
        print("\nConnection error occurred: ", ex)

    finally:
        send_audio_thread.join()
