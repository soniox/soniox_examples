"""Thin client for the 60db Text-to-Speech HTTP API.

The voice bot's audio path (browser worklet, Twilio bridge) consumes **raw
little-endian 16-bit PCM**. 60db's simple synthesis endpoint
(``POST /tts-synthesize``) instead returns a complete, base64-encoded container
file (mp3/wav/ogg/flac). We therefore request ``wav`` and unwrap it back to raw
PCM here so the rest of the app stays format-agnostic — it only ever sees PCM
``s16le`` at the configured sample rate, exactly like the Soniox provider emits.

Python 3.13 removed the ``audioop`` module, so the small amount of channel
down-mixing / resampling we may need is implemented in pure Python below. In the
common case (60db already returns mono 16-bit at the requested rate) these are
no-ops.
"""

import base64
import io
import wave
from array import array

import httpx

DEFAULT_BASE_URL = "https://api.60db.ai"

# 60db's documented synthesis sample rate. Used only as a fallback if the
# returned WAV omits/!= the target; we resample to the app's sample rate.
DEFAULT_SAMPLE_RATE = 24000


def _to_int16_mono(frames: bytes, sample_width: int, num_channels: int) -> array:
    """Decode raw WAV frames into a mono ``array('h')`` of 16-bit samples."""
    if sample_width == 2:
        samples = array("h")
        samples.frombytes(frames)
    elif sample_width == 1:
        # 8-bit WAV is unsigned; center around 0 and scale up to 16-bit.
        samples = array("h", (((b - 128) << 8) for b in frames))
    else:
        raise ValueError(
            f"Unsupported 60db WAV sample width: {sample_width} bytes "
            "(expected 1 or 2)"
        )

    if num_channels == 1:
        return samples
    if num_channels < 1:
        raise ValueError(f"Invalid channel count in 60db WAV: {num_channels}")

    # Down-mix to mono by averaging the interleaved channels.
    mono = array("h", bytes(2 * (len(samples) // num_channels)))
    for i in range(len(mono)):
        base = i * num_channels
        total = 0
        for c in range(num_channels):
            total += samples[base + c]
        mono[i] = int(total / num_channels)
    return mono


def _resample_linear(samples: array, src_rate: int, dst_rate: int) -> array:
    """Linearly resample a mono 16-bit signal. No-op when the rates match."""
    if src_rate == dst_rate or len(samples) == 0:
        return samples

    n = len(samples)
    out_n = max(1, round(n * dst_rate / src_rate))
    out = array("h", bytes(2 * out_n))
    ratio = src_rate / dst_rate
    for i in range(out_n):
        pos = i * ratio
        i0 = int(pos)
        frac = pos - i0
        s0 = samples[i0] if i0 < n else samples[-1]
        s1 = samples[i0 + 1] if i0 + 1 < n else s0
        out[i] = int(s0 + (s1 - s0) * frac)
    return out


def wav_to_pcm_s16le(wav_bytes: bytes, target_rate: int) -> bytes:
    """Unwrap a WAV container into raw little-endian 16-bit mono PCM."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav:
        num_channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        framerate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    samples = _to_int16_mono(frames, sample_width, num_channels)
    samples = _resample_linear(samples, framerate or target_rate, target_rate)

    # ``array('h')`` is host byte order; the consumers expect little-endian.
    import sys

    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


async def synthesize_pcm(
    client: httpx.AsyncClient,
    *,
    api_key: str,
    text: str,
    voice_id: str,
    base_url: str = DEFAULT_BASE_URL,
    target_rate: int = DEFAULT_SAMPLE_RATE,
    speed: float = 1.0,
    stability: int = 50,
    similarity: int = 75,
    enhance: bool = True,
) -> bytes:
    """Synthesize ``text`` via 60db and return raw PCM ``s16le`` at ``target_rate``.

    Uses the simple (non-streaming) ``POST /tts-synthesize`` endpoint, which
    returns the full clip in one response.
    """
    response = await client.post(
        f"{base_url.rstrip('/')}/tts-synthesize",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "text": text,
            "voice_id": voice_id,
            "speed": speed,
            "stability": stability,
            "similarity": similarity,
            "enhance": enhance,
            # Request a container we can losslessly unwrap to raw PCM.
            "output_format": "wav",
        },
    )
    response.raise_for_status()
    payload = response.json()

    audio_b64 = payload.get("audio_base64")
    if not audio_b64:
        raise ValueError("60db response did not contain 'audio_base64'")

    sample_rate = int(payload.get("sample_rate") or target_rate)
    wav_bytes = base64.b64decode(audio_b64)
    # The WAV header already carries the true rate; pass the response rate only
    # as a fallback for headerless edge cases.
    return wav_to_pcm_s16le(wav_bytes, target_rate or sample_rate)
