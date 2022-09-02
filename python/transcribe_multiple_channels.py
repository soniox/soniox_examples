from typing import Dict, List
import os
import argparse
import soundfile

from soniox.speech_service import SpeechClient, Result
from soniox.transcribe_file import transcribe_bytes_stream
from soniox.multi_channel_utils import get_multi_channel_transcript


def process_file(audio_file: str, silence_threshold_ms: int, client: SpeechClient) -> None:
    samples, sample_rate = soundfile.read(audio_file, dtype="int16", always_2d=True)
    assert len(samples.shape) == 2

    num_channels = samples.shape[1]
    if num_channels == 0:
        raise Exception(f"No channels in audio file: {audio_file}")

    results: Dict[int, Result] = {}

    for channel in range(num_channels):
        result = transcribe_bytes_stream(
            samples[:, channel].tobytes(),
            client,
            audio_format="pcm_s16le",
            sample_rate_hertz=sample_rate,
            num_audio_channels=1,
        )
        assert isinstance(result, Result)
        results[channel] = result

    transcript = get_multi_channel_transcript(results, silence_threshold_ms)

    transcript_file = os.path.splitext(audio_file)[0] + ".soniox.txt"
    with open(transcript_file, "w") as fh:
        fh.write(transcript)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--silence_threshold_ms",
        type=int,
        default=250,
        help="Minimum amount of silence to allow switching to a different speaker.",
    )
    parser.add_argument("audio_files", type=str, nargs="+", help="Audio files to transcribe.")
    args = parser.parse_args()

    audio_files: List[str] = args.audio_files
    print(f"Transcribing {len(audio_files)} audio files.")

    with SpeechClient() as client:
        for audio_file in audio_files:
            process_file(audio_file, args.silence_threshold_ms, client)

    print("Finished.")


if __name__ == "__main__":
    main()
