from typing import Iterable
from soniox.transcribe_live import transcribe_stream
from soniox.speech_service import SpeechClient


def iter_audio() -> Iterable[bytes]:
    with open("../test_data/test_audio_long.flac", "rb") as fh:
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
        ):
            print("".join(w.text for w in result.words))


if __name__ == "__main__":
    main()
