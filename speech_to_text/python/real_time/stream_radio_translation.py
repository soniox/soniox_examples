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


def render_tokens(final_tokens, non_final_tokens):
    # Render the tokens in the terminal using ANSI escape codes.
    text = ""
    text += "\033[2J\033[H"  # clear the screen, move to top-left corner
    is_final = True
    speaker = ""
    language = ""
    for token in final_tokens + non_final_tokens:
        token_text = token["text"]
        if not token["is_final"] and is_final:
            text += "\033[34m"  # change text color to blue
            is_final = False
        if token.get("speaker") and token["speaker"] != speaker:
            if speaker:
                text += "\n\n"
            speaker = token["speaker"]
            text += f"Speaker {speaker}: "
            token_text = token_text.lstrip()
            language = ""
        if token.get("language") and token["language"] != language:
            text += "\n"
            language = token["language"]
            text += f"[{language}] "
            token_text = token_text.lstrip()
        text += token_text
    text += "\033[39m"  # reset text color
    print(text)


def main():
    print("Opening WebSocket connection...")

    with connect(websocket_url) as ws:
        # Send start request
        ws.send(
            json.dumps(
                {
                    "api_key": api_key,
                    "audio_format": "auto",  # let the API detect the format
                    "model": "stt-rt-preview-v2",
                    "language_hints": ["en", "es"],
                    "enable_speaker_diarization": True,
                    "translation": {
                        "type": "one_way",
                        "target_language": "es",
                    },
                }
            )
        )

        # Start streaming audio in background
        threading.Thread(target=stream_audio, args=(ws,), daemon=True).start()

        print(f"Transcription started from {audio_url}")

        final_tokens = []

        try:
            while True:
                message = ws.recv()
                res = json.loads(message)

                if res.get("error_code"):
                    print(f"Error: {res['error_code']} - {res['error_message']}")
                    break

                non_final_tokens = []

                for token in res.get("tokens", []):
                    if token.get("text"):
                        if token.get("is_final"):
                            final_tokens.append(token)
                        else:
                            non_final_tokens.append(token)

                render_tokens(final_tokens, non_final_tokens)

                if res.get("finished"):
                    print("\nTranscription complete.")
        except ConnectionClosedOK:
            pass
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
