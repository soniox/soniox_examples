from soniox.transcribe_file import transcribe_file_short
from soniox.speech_service import SpeechClient, set_api_key

set_api_key("<YOUR-API-KEY>")


def main():
    with SpeechClient() as client:
        result = transcribe_file_short(
            "../test_data/test_audio_profanity.mp3",
            client,
            enable_profanity_filter=True,
        )
        print("Words: " + " ".join(w.text for w in result.words))


if __name__ == "__main__":
    main()
