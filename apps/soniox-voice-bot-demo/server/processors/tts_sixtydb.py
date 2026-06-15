import asyncio
import time

import httpx

from messages import (
    ErrorMessage,
    LLMFullMessage,
    Message,
    MetricsMessage,
    TranscriptionMessage,
    TTSAudioMessage,
    UserSpeechStartMessage,
)
from processors.message_processor import MessageProcessor
from processors.sixtydb_client import DEFAULT_BASE_URL, synthesize_pcm

DEFAULT_SAMPLE_RATE = 24000
DEFAULT_SPEED = 1.0
DEFAULT_STABILITY = 50
DEFAULT_SIMILARITY = 75
DEFAULT_ENHANCE = True

# How much PCM to emit per TTSAudioMessage. The HTTP endpoint returns the whole
# utterance at once; we slice it into ~40 ms frames so the browser worklet is fed
# smoothly and so a barge-in can stop playback partway through.
CHUNK_MS = 40


class SixtyDBTTSProcessor(MessageProcessor):
    """Processor that converts LLM text output to speech using the 60db TTS API.

    Unlike the Soniox provider, 60db's simple endpoint is request/response rather
    than streaming, so we synthesize once per completed LLM turn
    (``LLMFullMessage``) and slice the resulting audio into PCM frames. The output
    is raw ``s16le`` PCM at ``sample_rate`` — identical to what the Soniox
    processor emits — so this is a drop-in alternative behind ``MessageProcessor``.
    """

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        base_url: str = DEFAULT_BASE_URL,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        speed: float = DEFAULT_SPEED,
        stability: int = DEFAULT_STABILITY,
        similarity: int = DEFAULT_SIMILARITY,
        enhance: bool = DEFAULT_ENHANCE,
    ):
        """Initialize the 60db TTS processor.

        Args:
            api_key: The 60db API key (Bearer token).
            voice_id: The 60db voice id to synthesize with.
            base_url: The 60db API base URL. Defaults to "https://api.60db.ai".
            sample_rate: The output sample rate in Hz. Defaults to 24000.
            speed: Speech speed multiplier (0.5-2.0). Defaults to 1.0.
            stability: Voice stability (0-100, lower = more expressive).
            similarity: Voice similarity/fidelity (0-100).
            enhance: Whether to apply 60db's audio enhancement.
        """
        self._api_key = api_key
        self._voice_id = voice_id
        self._base_url = base_url
        self._sample_rate = sample_rate
        self._speed = speed
        self._stability = stability
        self._similarity = similarity
        self._enhance = enhance

        self._chunk_bytes = max(2, int(sample_rate * 2 * CHUNK_MS / 1000) & ~1)

        self._client: httpx.AsyncClient | None = None
        self._task: asyncio.Task | None = None
        # Monotonic generation counter. Bumped on every new turn and on barge-in
        # so a late HTTP response can detect it has been superseded and drop its
        # audio instead of talking over the user.
        self._generation = 0

    async def start(self, send_message, log):
        self.log = log.bind(processor="tts", provider="sixtydb")
        self._send_message = send_message

        if not self._api_key:
            self.log.error("Missing 60db API key (SIXTYDB_API_KEY)")
        if not self._voice_id:
            self.log.error("Missing 60db voice id (SIXTYDB_VOICE_ID)")

        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))

    async def cleanup(self):
        self._cancel_generation()

        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._client:
            await self._client.aclose()
            self._client = None

    async def process(self, message: Message):
        if isinstance(message, LLMFullMessage):
            # The full turn is available; synthesize it as a single request.
            # Cancel/invalidate any still-running synthesis from a previous turn.
            self._cancel_generation()
            self._generation += 1
            generation = self._generation
            self._task = asyncio.create_task(
                self._synthesize(message.text(), generation)
            )

        if isinstance(message, UserSpeechStartMessage) or isinstance(
            message, TranscriptionMessage
        ):
            # Stop TTS if any user speech is detected (either with transcription or VAD)
            self._cancel_generation()

    def _cancel_generation(self):
        # Bumping the generation invalidates any in-flight/queued audio, and
        # cancelling the task stops an outstanding HTTP request promptly.
        self._generation += 1
        if self._task and not self._task.done():
            self._task.cancel()

    async def _synthesize(self, text: str, generation: int):
        text = text.strip()
        if not text or not self._client:
            return

        start_time = time.perf_counter()
        try:
            pcm = await synthesize_pcm(
                self._client,
                api_key=self._api_key,
                text=text,
                voice_id=self._voice_id,
                base_url=self._base_url,
                target_rate=self._sample_rate,
                speed=self._speed,
                stability=self._stability,
                similarity=self._similarity,
                enhance=self._enhance,
            )
        except asyncio.CancelledError:
            return
        except (httpx.HTTPError, ValueError) as e:
            self.log.error("60db TTS request failed", error=e)
            if self._send_message:
                await self._send_message(ErrorMessage("TTS request failed"))
            return

        # A barge-in (or a newer turn) happened while we were synthesizing — drop
        # this audio rather than play it over the user.
        if generation != self._generation:
            return

        first_chunk_sent = False
        for offset in range(0, len(pcm), self._chunk_bytes):
            if generation != self._generation:
                return
            chunk = pcm[offset : offset + self._chunk_bytes]
            if not first_chunk_sent:
                first_chunk_sent = True
                first_chunk_ms = (time.perf_counter() - start_time) * 1000
                await self._send_message(
                    MetricsMessage("tts_first_chunk_ms", first_chunk_ms)
                )
            await self._send_message(TTSAudioMessage(chunk))

        total_ms = (time.perf_counter() - start_time) * 1000
        await self._send_message(MetricsMessage("tts_total_ms", total_ms))
