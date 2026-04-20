import asyncio
import json

import websockets

from messages import (
    ErrorMessage,
    TranscriptionEndpointMessage,
    TranscriptionMessage,
    UserAudioMessage,
)
from processors.message_processor import MessageProcessor

KEEPALIVE_MESSAGE = json.dumps({"type": "keepalive"})
KEEPALIVE_INTERVAL = 5

END_TOKEN = "<end>"


class STTProcessor(MessageProcessor):
    """Processor that transcribes user audio to text using streaming STT."""

    def __init__(
        self,
        api_key: str,
        api_host: str = "wss://stt-rt.soniox.com/transcribe-websocket",
        audio_format: str = "pcm_s16le",
        audio_sample_rate: int | None = 16000,
        num_channels: int | None = 1,
        language_hints: list[str] | None = None,
        context: str | None = None,
    ):
        """
        Initialize the STT processor.

        Args:
            api_key (str): The API key for the Soniox STT API.
            api_host (str, optional): The host for the Soniox STT API.
                Defaults to "wss://stt-rt.soniox.com/transcribe-websocket".
            audio_format (str): The audio format to use. Defaults to "pcm_s16le".
                All supported audio formats are listed here:
                https://soniox.com/docs/stt/rt/real-time-transcription#audio-formats
            audio_sample_rate (int, optional): The sample rate to use for audio transcription. Defaults to 16000.
                Relevant only for raw audio formats.
            num_channels (int, optional): The number of channels to use for audio transcription. Defaults to 1.
                Relevant only for raw audio formats.
            language_hints (list[str], optional): A list of language hints to use for speech recognition. Learn
                more about language hints here: https://soniox.com/docs/stt/rt/real-time-transcription#language-hints
            context (str, optional): A context string for improving speech recognition. Learn more about context
                here: https://soniox.com/docs/stt/concepts/context
        """
        self._api_key = api_key
        self._api_host = api_host

        self._audio_format = audio_format
        self._sample_rate = audio_sample_rate
        self._num_channels = num_channels

        self._language_hints = language_hints
        self._context = context

        self._websocket = None
        self._receive_task = None
        self._keepalive_task = None
        self._send_task = None
        self._send_queue = asyncio.Queue(maxsize=100)

        self._send_message = None
        self._alive = False

    async def start(
        self,
        send_message,
        log,
    ):
        self.log = log.bind(processor="stt")
        self._send_message = send_message

        try:
            self._websocket = await websockets.connect(self._api_host)
        except websockets.exceptions.ConnectionClosed as e:
            self.log.error("Unable to connect to Soniox API", error=e)
            raise

        # Send the initial configuration message
        config = {
            "api_key": self._api_key,
            "model": "stt-rt-preview",
            "enable_endpoint_detection": True,
            "enable_non_final_tokens": True,
            "language_hints": self._language_hints,
            "context": self._context,
        }

        # Set the audio format
        if (
            self._audio_format.startswith("pcm")
            or self._audio_format == "mulaw"
            or self._audio_format == "alaw"
        ):
            # Raw audio format
            config["audio_format"] = self._audio_format
            config["sample_rate"] = self._sample_rate
            config["num_channels"] = self._num_channels
        else:
            # auto, aac, aiff, amr, asf, flac, mp3, ogg, wav, webm
            config["audio_format"] = self._audio_format

        # Send the configuration message
        await self._websocket.send(json.dumps(config))

        self._receive_task = asyncio.create_task(self._receive_task_handler())
        self._keepalive_task = asyncio.create_task(self._keepalive_task_handler())
        self._send_task = asyncio.create_task(self._send_task_handler())

        self._alive = True

    async def cleanup(self):
        self._alive = False

        tasks = []

        if self._receive_task:
            self._receive_task.cancel()
            tasks.append(self._receive_task)
        if self._keepalive_task:
            self._keepalive_task.cancel()
            tasks.append(self._keepalive_task)
        if self._send_task:
            self._send_task.cancel()
            tasks.append(self._send_task)

        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass  # Task was cancelled

        if self._websocket:
            await self._websocket.close()
            self._websocket = None

    async def process(self, message):
        if not self._alive:
            return

        if isinstance(message, UserAudioMessage):
            try:
                self._send_queue.put_nowait(message.audio_data())
            except asyncio.QueueFull:
                self.log.warning("STT send queue full, dropping audio")

    async def _send_task_handler(self):
        try:
            while self._alive:
                audio_data = await self._send_queue.get()
                if not self._websocket:
                    break
                try:
                    await self._websocket.send(audio_data)
                except websockets.exceptions.ConnectionClosed:
                    self.log.error("Unable to send audio data to Soniox API")
                    if self._send_message:
                        await self._send_message(ErrorMessage("STT connection lost"))
                    await self.cleanup()
                    break
        except asyncio.CancelledError:
            pass

    async def _keepalive_task_handler(self):
        try:
            while self._alive:
                if self._websocket:
                    await self._websocket.send(KEEPALIVE_MESSAGE)
                else:
                    break

                await asyncio.sleep(KEEPALIVE_INTERVAL)

        except websockets.exceptions.ConnectionClosed:
            pass

    async def _receive_task_handler(self):
        if not self._websocket or not self._send_message:
            return

        try:
            async for message in self._websocket:
                content = json.loads(message)
                tokens = content["tokens"]

                if tokens:
                    final_tokens = []
                    non_final_tokens = []
                    has_endpoint = False

                    for token in tokens:
                        if token["is_final"] and token["text"] == END_TOKEN:
                            has_endpoint = True
                        elif token["is_final"]:
                            final_tokens.append(token)
                        else:
                            non_final_tokens.append(token)

                    await self._send_message(
                        TranscriptionMessage(
                            final_tokens=final_tokens,
                            non_final_tokens=non_final_tokens,
                        )
                    )

                    if has_endpoint:
                        await self._send_message(TranscriptionEndpointMessage())

                error_code = content.get("error_code")
                error_message = content.get("error_message")
                if error_code or error_message:
                    # In case of error, still send the final transcript (if any remaining in the buffer)
                    await self._send_message(TranscriptionEndpointMessage())

                    self.log.error(
                        f"Error from Soniox API: {error_code} {error_message}"
                    )

        except websockets.exceptions.ConnectionClosed:
            # Expected when closing the connection
            self.log.debug("Connection to Soniox API closed")
