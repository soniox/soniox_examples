from typing import Iterable
from soniox.transcribe_live import transcribe_stream
from soniox.speech_service import SpeechClient
from soniox.speech_service import SpeechContext, SpeechContextEntry


def iter_audio() -> Iterable[bytes]:
    with open("../test_data/carrie_underwood_kerry_washington.flac", "rb") as fh:
        while True:
            audio = fh.read(1024)
            if len(audio) == 0:
                break
            yield audio


def main():
    with SpeechClient() as client:
        # Create SpeechContext.
        speech_context = SpeechContext(
            entries=[
                SpeechContextEntry(
                    phrases=["Carrie Underwood", "Kerry Washington"],
                    boost=20,
                )
            ]
        )

        # Pass SpeechContext with transcribe request.
        for result in transcribe_stream(
            iter_audio(),
            client,
            model="en_v2_lowlatency",
            include_nonfinal=True,
            speech_context=speech_context,
        ):
            print("".join(w.text for w in result.words))


if __name__ == "__main__":
    main()
