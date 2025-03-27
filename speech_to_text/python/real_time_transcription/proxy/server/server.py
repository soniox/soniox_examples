import os
import json
import asyncio
import websockets
from dotenv import load_dotenv

load_dotenv()


async def handle_client(websocket):
    print("Browser client connected")

    # create a message queue to store client messages received before
    # Soniox Real-time API connection is ready, so we don't loose any
    message_queue = []
    soniox_ws = None
    soniox_ws_ready = False

    async def init_soniox_connection():
        nonlocal soniox_ws, soniox_ws_ready

        try:
            soniox_ws = await websockets.connect(
                "wss://stt-rt.soniox.com/transcribe-websocket"
            )
            print("Connected to Soniox STT Real-time API")

            # Send initial configuration message
            start_message = json.dumps(
                {
                    "api_key": os.getenv("SONIOX_API_KEY"),
                    "audio_format": "auto",
                    "model": "stt-rt-preview",
                }
            )
            await soniox_ws.send(start_message)
            print("Sent start message to Soniox")

            # mark connection as ready
            soniox_ws_ready = True

            # process any queued messages
            while len(message_queue) > 0 and soniox_ws_ready:
                data = message_queue.pop(0)
                await forward_data(data)

            # receive messages from Soniox STT Real-time API
            async for message in soniox_ws:
                try:
                    await websocket.send(message)
                except Exception as e:
                    print(f"Error forwarding Soniox response: {e}")
                    break

        except Exception as e:
            print(f"Soniox WebSocket error: {e}")
            soniox_ws_ready = False
        finally:
            if soniox_ws:
                await soniox_ws.close()
            soniox_ws_ready = False
            print("Soniox WebSocket closed")

    async def forward_data(data):
        try:
            if soniox_ws:
                await soniox_ws.send(data)
        except Exception as e:
            print(f"Error forwarding data to Soniox: {e}")

    # initialize Soniox connection
    soniox_task = asyncio.create_task(init_soniox_connection())

    try:
        # receive messages from browser client
        async for data in websocket:
            if soniox_ws_ready:
                # forward messages instantly
                await forward_data(data)
            else:
                # queue the message to be processed
                # as soon as connection to Soniox STT Real-time API is ready
                message_queue.append(data)
    except Exception as e:
        print(f"Error with browser client: {e}")
    finally:
        print("Browser client disconnected")
        soniox_task.cancel()
        try:
            await soniox_task
        except asyncio.CancelledError:
            pass


async def main():
    port = int(os.getenv("PORT", 3001))
    server = await websockets.serve(handle_client, "0.0.0.0", port)
    print(f"WebSocket proxy server listening on port {port}")

    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
