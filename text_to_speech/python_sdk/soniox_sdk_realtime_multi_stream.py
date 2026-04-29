import argparse
import os
import threading
import time
from uuid import uuid4

from soniox import SonioxClient
from soniox.errors import SonioxRealtimeError
from soniox.types import RealtimeTTSConfig
from soniox.utils import output_file_for_audio_format

VALID_SAMPLE_RATES = [8000, 16000, 24000, 44100, 48000]
VALID_BITRATES = [32000, 64000, 96000, 128000, 192000, 256000, 320000]
VALID_AUDIO_FORMATS = [
    "pcm_f32le",
    "pcm_s16le",
    "pcm_mulaw",
    "pcm_alaw",
    "wav",
    "aac",
    "mp3",
    "opus",
    "flac",
]

STREAM_SPECS = {
    "a": {
        "language": "en",
        "voice": "Adrian",
        "chunks": [
            "Welcome to Soniox real-time Text-to-Speech. ",
            "This stream demonstrates English speech generation. ",
            "Thank you for listening.",
        ],
    },
    "b": {
        "language": "sl",
        "voice": "Maya",
        "chunks": [
            "Dobrodošli v sistem Soniox za pretvorbo besedila v govor v realnem času. ",
            "Ta tok prikazuje generiranje slovenskega govora. ",
            "Hvala za poslušanje.",
        ],
    },
    "c": {
        "language": "es",
        "voice": "Daniel",
        "chunks": [
            "Bienvenido a Soniox texto a voz en tiempo real. ",
            "Este flujo demuestra la generación de voz en español. ",
            "Gracias por escuchar.",
        ],
    },
}


def run_multiplexed_session(
    *,
    client: SonioxClient,
    model: str,
    audio_format: str,
    sample_rate: int | None,
    bitrate: int | None,
) -> None:
    configs = {
        key: RealtimeTTSConfig(
            stream_id=f"sync-{key}-{uuid4()}",
            model=model,
            language=spec["language"],
            voice=spec["voice"],
            audio_format=audio_format,
            sample_rate=sample_rate,
            bitrate=bitrate,
        )
        for key, spec in STREAM_SPECS.items()
    }

    audio_by_stream: dict[str, list[bytes]] = {key: [] for key in configs}
    try:
        with client.realtime.tts.connect_multi_stream() as connection:
            streams = {key: connection.open_stream(config=configs[key]) for key in sorted(configs)}
            send_errors: list[Exception] = []
            receive_errors: list[Exception] = []

            def send_worker() -> None:
                try:
                    pending = {
                        key: [line.strip() for line in STREAM_SPECS[key]["chunks"] if line.strip()]
                        for key in sorted(streams)
                    }
                    while any(pending.values()):
                        for key in sorted(streams):
                            if not pending[key]:
                                continue
                            streams[key].send_text_chunk(pending[key].pop(0), text_end=False)
                            time.sleep(0.1)
                    for key in sorted(streams):
                        streams[key].finish()
                except Exception as exc:
                    send_errors.append(exc)

            def receive_worker(key: str) -> None:
                try:
                    for chunk in streams[key].receive_audio_chunks():
                        audio_by_stream[key].append(chunk)
                except Exception as exc:
                    receive_errors.append(exc)

            sender_thread = threading.Thread(target=send_worker, daemon=True)
            receiver_threads = [
                threading.Thread(target=receive_worker, args=(key,), daemon=True)
                for key in sorted(streams)
            ]

            for receiver_thread in receiver_threads:
                receiver_thread.start()
            sender_thread.start()

            sender_thread.join()
            for receiver_thread in receiver_threads:
                receiver_thread.join()

            if send_errors:
                raise RuntimeError(f"Failed to send realtime text: {send_errors[0]}")
            if receive_errors:
                raise RuntimeError(f"Failed to receive realtime audio: {receive_errors[0]}")
    finally:
        for key, chunks in sorted(audio_by_stream.items()):
            audio = b"".join(chunks)
            output_path = output_file_for_audio_format(audio_format, f"tts_sdk_realtime_multi_{key}")
            if audio:
                output_path.write_bytes(audio)
                print(f"Wrote stream {key.upper()} ({len(audio)} bytes) to {output_path.resolve()}")
            else:
                print(f"No audio file was written for stream {key.upper()}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="tts-rt-v1")
    parser.add_argument("--audio_format", default="wav")
    parser.add_argument("--sample_rate", type=int)
    parser.add_argument("--bitrate", type=int)
    args = parser.parse_args()

    if args.audio_format not in VALID_AUDIO_FORMATS:
        raise ValueError(f"audio_format must be one of {VALID_AUDIO_FORMATS}")
    if args.sample_rate is not None and args.sample_rate not in VALID_SAMPLE_RATES:
        raise ValueError(f"sample_rate must be None or one of {VALID_SAMPLE_RATES}")
    if args.bitrate is not None and args.bitrate not in VALID_BITRATES:
        raise ValueError(f"bitrate must be None or one of {VALID_BITRATES}")

    api_key = os.environ.get("SONIOX_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing SONIOX_API_KEY.\n"
            "1. Get your API key at https://console.soniox.com\n"
            "2. Run: export SONIOX_API_KEY=<YOUR_API_KEY>"
        )

    client = SonioxClient(api_key=api_key)
    try:
        run_multiplexed_session(
            client=client,
            model=args.model,
            audio_format=args.audio_format,
            sample_rate=args.sample_rate,
            bitrate=args.bitrate,
        )
    except SonioxRealtimeError as exc:
        print("Soniox realtime error:", exc)
    finally:
        client.close()


if __name__ == "__main__":
    main()
