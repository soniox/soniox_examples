from soniox.transcribe_file import transcribe_file_short
from soniox.speech_service import SpeechClient


def main():
    with SpeechClient() as client:
        result = transcribe_file_short(
            "../test_data/test_audio_dictation.mp3", client, enable_dictation=True
        )
        print(" ".join(w.text for w in result.words))


if __name__ == "__main__":
    main()
