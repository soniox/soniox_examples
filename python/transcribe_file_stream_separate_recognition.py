from soniox.transcribe_file import transcribe_file_stream
from soniox.speech_service import SpeechClient, set_api_key

set_api_key("<YOUR-API-KEY>")


def main():
    with SpeechClient() as client:
        channel_results = transcribe_file_stream(
            "../test_data/test_audio_multi_channel.flac",
            client,
            num_audio_channels=2,
            enable_separate_recognition_per_channel=True,
        )
        for result in channel_results:
            print(f"Channel {result.channel}: " + " ".join(word.text for word in result.words))


if __name__ == "__main__":
    main()
