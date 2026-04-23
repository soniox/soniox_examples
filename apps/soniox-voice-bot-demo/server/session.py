import asyncio
import uuid
from typing import List

import structlog
from websockets import ConnectionClosed, ServerConnection

from messages import (
    ErrorMessage,
    LLMChunkMessage,
    Message,
    MetricsMessage,
    SessionStartMessage,
    TranscriptionMessage,
    TTSAudioMessage,
    UserAudioMessage,
    UserSpeechEndMessage,
    UserSpeechStartMessage,
)
from processors.message_processor import MessageProcessor

MAX_QUEUE_SIZE = 1000


class Session:
    """Manages a voice bot session, coordinating message flow between processors and WebSocket."""

    def __init__(
        self,
        message_processors: List[MessageProcessor],
        websocket: ServerConnection,
    ):
        self.session_id = str(uuid.uuid4())
        self.websocket = websocket
        self.processors = message_processors
        self.log = structlog.get_logger(session_id=self.session_id)

        self.message_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        self.send_message_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

    async def run(self):
        self.log.info("Starting session")

        async def add_message_to_queue(message: Message):
            await self.message_queue.put(message)

        for processor in self.processors:
            await processor.start(send_message=add_message_to_queue, log=self.log)

        receive_task = asyncio.create_task(self.receive_messages())
        process_task = asyncio.create_task(self.process_messages())
        send_task = asyncio.create_task(self.send_messages())

        self.message_queue.put_nowait(SessionStartMessage())

        try:
            done, pending = await asyncio.wait(
                {receive_task, process_task, send_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                if task.exception():
                    self.log.error(
                        "Task raised an exception",
                        task_name=task.get_name(),
                        error=task.exception(),
                    )

            for task in pending:
                task.cancel()

            await asyncio.shield(asyncio.gather(*pending, return_exceptions=True))

        except asyncio.CancelledError:
            self.log.info("Session run task was cancelled.")
        finally:
            await self.cleanup()
            self.log.info("Session completed.")

    async def cleanup(self):
        self.log.info("Cleaning up session")

        if self.websocket:
            try:
                await self.websocket.close()
            except ConnectionClosed:
                pass
            self.websocket = None

        for processor in self.processors:
            await processor.cleanup()

    async def receive_messages(self):
        try:
            async for message in self.websocket:
                # For now, we only have raw audio data message
                if isinstance(message, bytes):
                    await self.message_queue.put(UserAudioMessage(message))
                else:
                    # Message is a string - Potentially a JSON message
                    # (you can add custom JSON message types here, if you need to send
                    # additional info from the frontend to the backend)
                    self.log.error("Unknown message type", message=message)

        except ConnectionClosed:
            self.log.info("WebSocket connection closed")

    async def send_messages(self):
        try:
            while True:
                message = await self.send_message_queue.get()
                await self.websocket.send(message)
        except ConnectionClosed:
            pass

    async def process_messages(self):
        while True:
            message = await self.message_queue.get()

            for processor in self.processors:
                await processor.process(message)

            if isinstance(message, TranscriptionMessage):
                await self.send_message_queue.put(message.json())

            if isinstance(message, LLMChunkMessage):
                await self.send_message_queue.put(message.json())

            if isinstance(message, TTSAudioMessage):
                await self.send_message_queue.put(message.audio_data())

            if isinstance(message, SessionStartMessage):
                await self.send_message_queue.put(message.json())

            if isinstance(message, MetricsMessage):
                self.log.info(message.json())

            if isinstance(message, UserSpeechStartMessage):
                await self.send_message_queue.put(message.json())

            if isinstance(message, UserSpeechEndMessage):
                await self.send_message_queue.put(message.json())

            if isinstance(message, ErrorMessage):
                self.log.error(
                    "Critical error received, terminating session",
                    error=message.error(),
                )

                try:
                    if self.websocket:
                        await self.websocket.send(message.json())
                        await self.websocket.close(code=1011, reason="Critical Error")
                except ConnectionClosed:
                    self.log.debug(
                        "Websocket already closed before sending error message."
                    )

                break
