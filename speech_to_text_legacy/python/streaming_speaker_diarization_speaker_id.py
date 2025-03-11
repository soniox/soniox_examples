from typing import Iterable
from soniox.transcribe_live import transcribe_stream
from soniox.speech_service import SpeechClient


def iter_audio() -> Iterable[bytes]:
    with open("../test_data/test_audio_sd.flac", "rb") as fh:
        while True:
            audio = fh.read(1024)
            if len(audio) == 0:
                break
            yield audio


def main():
    with SpeechClient() as client:
        for result in transcribe_stream(
            iter_audio(),
            client,
            model="en_v2_lowlatency",
            include_nonfinal=True,
            enable_streaming_speaker_diarization=True,
            enable_speaker_identification=True,
            cand_speaker_names=["John", "Judy"],
        ):
            speaker_num_to_name = {entry.speaker: entry.name for entry in result.speakers}

            def get_name(speaker):
                if speaker in speaker_num_to_name:
                    return speaker_num_to_name[speaker]
                else:
                    return "unknown"

            print(" ".join(f"'{w.text}'/{w.speaker}({get_name(w.speaker)})" for w in result.words))


if __name__ == "__main__":
    main()
