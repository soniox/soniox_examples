import threading
from typing import List

import numpy as np
import torch
from silero_vad import VADIterator

from messages import UserAudioMessage, UserSpeechEndMessage, UserSpeechStartMessage
from processors.message_processor import MessageProcessor


class VADProcessor(MessageProcessor):
    """Voice Activity Detection processor using Silero VAD model.

    Detects speech start/end boundaries from incoming audio and emits
    UserSpeechStartMessage and UserSpeechEndMessage events.
    """

    _model = None
    _lock = threading.Lock()

    @classmethod
    def warmup(cls):
        """Preload the Silero VAD model before any sessions start."""
        if cls._model is not None:
            return
        with cls._lock:
            if cls._model is not None:
                return
            torch.set_num_threads(1)
            cls._model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                onnx=True,
                trust_repo=True,
            )

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.5,
        min_silence_duration_ms: int = 300,
    ):
        """
        Initialize VAD processor using Silero VAD.

        Args:
            sample_rate: Audio sample rate (must be 8000 or 16000)
            threshold: Speech probability threshold (0-1)
            min_silence_duration_ms: Silence duration to trigger end
        """
        self._sample_rate = sample_rate
        self._threshold = threshold
        self._min_silence_duration_ms = min_silence_duration_ms

        VADProcessor.warmup()

        self._vad_iterator = VADIterator(
            VADProcessor._model,
            sampling_rate=sample_rate,
            threshold=threshold,
            min_silence_duration_ms=min_silence_duration_ms,
        )

        self._audio_buffer: List[np.ndarray] = []
        self._buffered_samples = 0

        self._send_message = None
        self._alive = False

    async def start(self, send_message, log):
        self.log = log.bind(processor="vad")
        self._send_message = send_message
        self._alive = True

    async def cleanup(self):
        self._alive = False
        self._audio_buffer.clear()

    async def process(self, message):
        if not self._alive:
            return

        if isinstance(message, UserAudioMessage):
            await self._process_audio(message.audio_data())

    async def _process_audio(self, audio_data: bytes):
        """Process incoming audio and detect speech boundaries."""
        if self._send_message is None:
            return

        audio_float = self._convert_to_float32(audio_data)

        self._audio_buffer.append(audio_float)
        self._buffered_samples += len(audio_float)

        chunk_size = 512 if self._sample_rate == 16000 else 256

        while self._buffered_samples >= chunk_size:
            chunk = self._combine_chunks(chunk_size)

            chunk_tensor = torch.from_numpy(chunk).unsqueeze(0)

            result = self._vad_iterator(chunk_tensor, return_seconds=False)

            if result is not None:
                if "start" in result:
                    await self._send_message(UserSpeechStartMessage())
                elif "end" in result:
                    await self._send_message(UserSpeechEndMessage())

    def _convert_to_float32(self, audio_bytes: bytes) -> np.ndarray:
        """Convert 16-bit PCM to float32 normalized [-1, 1]."""
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        return audio_int16.astype(np.float32) / 32768.0

    def _combine_chunks(self, num_samples: int) -> np.ndarray:
        """Combine buffered samples into a chunk."""
        combined = np.concatenate(self._audio_buffer)
        chunk = combined[:num_samples]
        remaining = combined[num_samples:]
        self._buffered_samples = len(remaining)
        if len(remaining) > 0:
            self._audio_buffer = [remaining]
        else:
            self._audio_buffer = []
        return chunk
