from soniox.transcribe_live import transcribe_microphone
from soniox.speech_service import SpeechClient


def main():
    with SpeechClient() as client:
        print("Transcribing from your microphone ...")
        for result in transcribe_microphone(
            client,
            model="en_v2_lowlatency",
            include_nonfinal=True,
        ):
            print("".join(w.text for w in result.words))


if __name__ == "__main__":
    main()
