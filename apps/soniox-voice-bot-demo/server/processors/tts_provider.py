"""Factory that selects a TTS provider behind the common ``MessageProcessor``
interface, so the rest of the app is provider-agnostic.

Supported providers (``TTS_PROVIDER`` env var):
- ``soniox``  -> Soniox streaming WebSocket TTS (:class:`SonioxTTSProcessor`)
- ``sixtydb`` -> 60db HTTP TTS (:class:`SixtyDBTTSProcessor`); also accepts ``60db``
"""

from processors.message_processor import MessageProcessor
from processors.sixtydb_client import DEFAULT_BASE_URL as SIXTYDB_DEFAULT_BASE_URL
from processors.tts import SonioxTTSProcessor
from processors.tts_sixtydb import SixtyDBTTSProcessor

DEFAULT_PROVIDER = "sixtydb"
SONIOX_DEFAULT_HOST = "wss://tts-rt.soniox.com/tts-websocket"


def make_tts_processor(
    provider: str,
    *,
    language: str,
    voice: str,
    sample_rate: int,
    soniox_api_key: str,
    soniox_api_host: str = "",
    sixtydb_api_key: str = "",
    sixtydb_voice_id: str = "",
    sixtydb_base_url: str = SIXTYDB_DEFAULT_BASE_URL,
) -> MessageProcessor:
    """Build the TTS processor for ``provider``.

    Args:
        provider: "soniox" or "sixtydb" (case-insensitive; empty -> default).
        language: BCP-47-ish language code passed to providers that use it.
        voice: Soniox voice name. 60db ignores this and uses ``sixtydb_voice_id``.
        sample_rate: Output PCM sample rate in Hz (both providers emit s16le PCM).
        soniox_api_key: API key for Soniox TTS.
        soniox_api_host: Soniox TTS WebSocket host (falls back to the default).
        sixtydb_api_key: API key (Bearer token) for 60db.
        sixtydb_voice_id: Voice id for 60db.
        sixtydb_base_url: 60db API base URL.

    Raises:
        ValueError: if ``provider`` is not recognized.
    """
    name = (provider or DEFAULT_PROVIDER).strip().lower()

    if name == "soniox":
        return SonioxTTSProcessor(
            api_key=soniox_api_key,
            api_host=soniox_api_host or SONIOX_DEFAULT_HOST,
            language=language,
            voice=voice,
            sample_rate=sample_rate,
        )

    if name in ("sixtydb", "60db"):
        return SixtyDBTTSProcessor(
            api_key=sixtydb_api_key,
            voice_id=sixtydb_voice_id,
            base_url=sixtydb_base_url or SIXTYDB_DEFAULT_BASE_URL,
            sample_rate=sample_rate,
        )

    raise ValueError(
        f"Unknown TTS_PROVIDER '{provider}'. Expected 'soniox' or 'sixtydb'."
    )
