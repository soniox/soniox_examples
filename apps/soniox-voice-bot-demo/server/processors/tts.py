import asyncio
import base64
import json
import time
import uuid

import websockets

from messages import (
    ErrorMessage,
    LLMChunkMessage,
    LLMFullMessage,
    Message,
    MetricsMessage,
    TranscriptionMessage,
    TTSAudioMessage,
    UserSpeechStartMessage,
)
from processors.message_processor import MessageProcessor

DEFAULT_MODEL = "tts-rt-v1"
DEFAULT_VOICE = "Alina"
DEFAULT_LANGUAGE = "en"
DEFAULT_AUDIO_FORMAT = "pcm_s16le"
DEFAULT_SAMPLE_RATE = 24000


class TTSProcessor(MessageProcessor):
    """Processor that converts LLM text output to speech using streaming TTS."""

    def __init__(
        self,
        api_key: str,
        api_host: str = "wss://tts-rt.soniox.com/tts-websocket",
        model: str = DEFAULT_MODEL,
        voice: str = DEFAULT_VOICE,
        language: str = DEFAULT_LANGUAGE,
        audio_format: str = DEFAULT_AUDIO_FORMAT,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
    ):
        """Initialize the TTS processor.

        Args:
            api_key: The API key for the Soniox TTS API.
            api_host: The WebSocket host for the TTS service.
            model: The TTS model to use. Defaults to "tts-rt-v1".
            voice: The voice to use. Defaults to "Alina".
            language: The language code. Defaults to "en".
            audio_format: The output audio format. Defaults to "pcm_s16le".
            sample_rate: The output sample rate in Hz. Defaults to 24000.
        """
        self._api_key = api_key
        self._api_host = api_host
        self._model = model
        self._voice = voice
        self._language = language
        self._audio_format = audio_format
        self._sample_rate = sample_rate

        self._websocket = None
        self._receive_task = None
        self._send_task = None
        self._send_queue = asyncio.Queue(maxsize=100)

        self._active_stream_id: str | None = None
        self._tts_lock = asyncio.Lock()
        self._alive = False

        self._tts_start_time: float | None = None
        self._first_audio_sent: bool = False

    async def start(self, send_message, log):
        self.log = log.bind(processor="tts")
        self._send_message = send_message

        try:
            self._websocket = await websockets.connect(self._api_host)
        except websockets.exceptions.ConnectionClosed as e:
            self.log.error("Unable to connect to Soniox API", error=e)
            raise

        self._receive_task = asyncio.create_task(self._receive_task_handler())
        self._send_task = asyncio.create_task(self._send_task_handler())
        self._alive = True

    async def cleanup(self):
        self._alive = False

        tasks = []

        if self._receive_task:
            self._receive_task.cancel()
            tasks.append(self._receive_task)
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

    async def process(self, message: Message):
        if isinstance(message, LLMChunkMessage) or isinstance(message, LLMFullMessage):
            await self._generate_tts_response(message)

        if isinstance(message, UserSpeechStartMessage) or isinstance(
            message, TranscriptionMessage
        ):
            # Stop TTS if any user speech is detected (either with transcription or VAD)
            self._cancel_generation()

    def _cancel_generation(self):
        # Soniox doesn't have support for cancelling in-progress TTS streams,
        # but we can achieve a similar effect by simply knowing the stream ID
        self._active_stream_id = None

    async def _generate_tts_response(self, message: LLMChunkMessage | LLMFullMessage):
        async with self._tts_lock:
            if not self._alive:
                return

            if not self._websocket:
                self.log.error("Websocket connection to Soniox API is not established")
                return

        if not self._active_stream_id:
            # Create new stream
            stream_id = f"tts-{uuid.uuid4()}"

            config = {
                "api_key": self._api_key,
                "model": self._model,
                "language": self._language,
                "voice": self._voice,
                "audio_format": self._audio_format,
                "sample_rate": self._sample_rate,
                "stream_id": stream_id,
            }

            try:
                await self._websocket.send(json.dumps(config))
            except websockets.exceptions.ConnectionClosed as e:
                self.log.error("Unable to send TTS config to Soniox API", error=e)
                if self._send_message:
                    await self._send_message(ErrorMessage("TTS connection lost"))
                return

            self._active_stream_id = stream_id
            self._tts_start_time = time.perf_counter()
            self._first_audio_sent = False

        # Send the text message
        try:
            # Send the text message or partial text message.
            if isinstance(message, LLMChunkMessage):
                # Stream text chunks directly to the TTS API
                text = message.text()
                text_end = False
            elif isinstance(message, LLMFullMessage):
                # LLM finished the generation. We already sent the text, just send the termination signal.
                text = ""
                text_end = True
            else:
                raise ValueError("Unexpected message type")

            text_request = {
                "text": text,
                "text_end": text_end,
                "stream_id": self._active_stream_id,
            }

            try:
                self._send_queue.put_nowait(text_request)
            except asyncio.QueueFull:
                self.log.warning("TTS send queue full, dropping text")

        except asyncio.CancelledError:
            self.log.debug("TTS generation task was cancelled")
        except websockets.exceptions.ConnectionClosed as e:
            self.log.error("Unable to send text message to Soniox API", error=e)
            if self._send_message:
                await self._send_message(ErrorMessage("TTS connection lost"))

    async def _send_task_handler(self):
        while self._alive:
            message = await self._send_queue.get()
            if not self._websocket:
                break
            try:
                await self._websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                self.log.error("Connection closed while sending text")
                break

    async def _receive_task_handler(self):
        if not self._websocket or not self._send_message:
            return

        try:
            async for message in self._websocket:
                content = json.loads(message)
                stream_id = content["stream_id"]
                audio_base64 = content.get("audio", "")
                finalized = content.get("terminated", False)

                if stream_id == self._active_stream_id:
                    if audio_base64:
                        if not self._first_audio_sent and self._tts_start_time:
                            self._first_audio_sent = True
                            first_chunk_ms = (
                                time.perf_counter() - self._tts_start_time
                            ) * 1000
                            await self._send_message(
                                MetricsMessage("tts_first_chunk_ms", first_chunk_ms)
                            )

                        audio_chunk = base64.b64decode(audio_base64)
                        await self._send_message(TTSAudioMessage(audio_chunk))

                    if finalized:
                        if self._tts_start_time:
                            total_ms = (
                                time.perf_counter() - self._tts_start_time
                            ) * 1000
                            await self._send_message(
                                MetricsMessage("tts_total_ms", total_ms)
                            )
                        self._active_stream_id = None

                error_code = content.get("error_code")
                error_message = content.get("error_message")
                if error_code or error_message:
                    self.log.error(
                        f"Error from Soniox API: {error_code} {error_message}"
                    )

        except websockets.exceptions.ConnectionClosed:
            # Expected when closing the connection
            self.log.debug("Connection to Soniox API closed")
