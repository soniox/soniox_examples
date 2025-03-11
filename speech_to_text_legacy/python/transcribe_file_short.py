from soniox.transcribe_file import transcribe_file_short
from soniox.speech_service import SpeechClient


def main():
    with SpeechClient() as client:
        result = transcribe_file_short(
            "../test_data/test_audio.flac",
            client,
            model="en_v2",
        )
        print(f"Text: " + "".join(word.text for word in result.words))
        print("Tokens:")
        for word in result.words:
            print(f"    '{word.text}' {word.start_ms} {word.duration_ms}")


if __name__ == "__main__":
    main()
