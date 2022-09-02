from soniox.transcribe_file import transcribe_file_stream
from soniox.speech_service import SpeechClient, set_api_key

set_api_key("<YOUR-API-KEY>")


def main():
    with SpeechClient() as client:
        result = transcribe_file_stream("../test_data/test_audio_long.flac", client)
        print(" ".join(w.text for w in result.words))


if __name__ == "__main__":
    main()
