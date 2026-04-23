# Based on the Twilio sample:
# https://github.com/twilio-samples/speech-assistant-openai-realtime-api-python/tree/main

import asyncio
import base64
import json
import os

import audioop
import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocketDisconnect

from twilio.twiml.voice_response import Connect, VoiceResponse

load_dotenv()

# Configuration
PORT = int(os.getenv("PORT", 5050))
SONIOX_VOICE_BOT_WS_URL = os.getenv("SONIOX_VOICE_BOT_WS_URL", "")
VOICE_BOT_LANGUAGE = os.getenv("VOICE_BOT_LANGUAGE", "en")
VOICE_BOT_VOICE = os.getenv("VOICE_BOT_VOICE", "female_1")

if not SONIOX_VOICE_BOT_WS_URL:
    raise ValueError(
        "Missing the SONIOX_VOICE_BOT_WS_URL. Please set it in the .env file."
    )


app = FastAPI()


@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()

    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f"wss://{host}/media-stream")
    response.append(connect)

    return HTMLResponse(content=str(response), media_type="application/xml")


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and Soniox voice bot."""
    await websocket.accept()

    # Tell the bot that the input will be in 16-bit PCM format.
    # The output format is currently fixed to whatever TTS produces.
    voice_bot_url_with_params = f"{SONIOX_VOICE_BOT_WS_URL}?audio_in_format=mulaw&audio_in_sample_rate=8000&audio_in_num_channels=1&language={VOICE_BOT_LANGUAGE}&voice={VOICE_BOT_VOICE}"
    async with websockets.connect(voice_bot_url_with_params) as voicebot_ws:
        # Connection specific state
        stream_sid = None

        # Queue to track 'mark' messages sent to Twilio
        # This helps implement interruption
        mark_queue = []

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the Soniox voice bot."""
            nonlocal stream_sid
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data["event"] == "media" and voicebot_ws.state.name == "OPEN":
                        audio_payload = data["media"]["payload"]
                        ulaw_audio_bytes = base64.b64decode(audio_payload)
                        await voicebot_ws.send(ulaw_audio_bytes)
                    elif data["event"] == "start":
                        stream_sid = data["start"]["streamSid"]
                        print(f"Incoming stream has started {stream_sid}")
                    elif data["event"] == "mark":
                        if mark_queue:
                            mark_queue.pop(0)
                    elif data["event"] == "stop":
                        print(f"Twilio stream {stream_sid} has stopped.")
                        break
            except WebSocketDisconnect:
                print("Client disconnected.")

        async def send_to_twilio():
            """Receive events from the Soniox voice bot server, send audio back to Twilio."""
            nonlocal stream_sid
            try:
                async for message in voicebot_ws:
                    if isinstance(message, str):
                        print(f"Received event: {message}")
                        message = json.loads(message)
                        if message["type"] == "transcription":
                            # Got transcription, bot should stop speaking (if speaking)
                            await handle_speech_started_event()
                    else:
                        # pcm_audio_bytes from OpenAI TTS: 24kHz, 16-bit signed, little-endian, mono
                        pcm_audio_bytes = message

                        # Resample to 8kHz
                        pcm_audio_bytes_8k = audioop.ratecv(
                            pcm_audio_bytes, 2, 1, 24000, 8000, None
                        )[0]
                        # Convert to 8-bit µ-law
                        ulaw_audio_bytes = audioop.lin2ulaw(pcm_audio_bytes_8k, 2)

                        audio_payload = base64.b64encode(ulaw_audio_bytes).decode(
                            "utf-8"
                        )
                        audio_delta = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": audio_payload},
                        }
                        await websocket.send_json(audio_delta)
                        await send_mark(websocket, stream_sid)

            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """If the bot is speaking (items in mark_queue), send a 'clear' message to Twilio to interrupt it."""
            print("Handling speech started event.")
            if mark_queue:
                await websocket.send_json({"event": "clear", "streamSid": stream_sid})
                mark_queue.clear()

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"},
                }
                await connection.send_json(mark_event)
                mark_queue.append("responsePart")

        receive_task = asyncio.create_task(receive_from_twilio())
        send_task = asyncio.create_task(send_to_twilio())

        _, pending = await asyncio.wait(
            [receive_task, send_task], return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
