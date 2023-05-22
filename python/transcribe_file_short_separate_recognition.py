from soniox.transcribe_file import transcribe_file_short
from soniox.speech_service import SpeechClient


def main():
    with SpeechClient() as client:
        channel_results = transcribe_file_short(
            "../test_data/test_audio_multi_channel.flac",
            client,
            num_audio_channels=2,
            enable_separate_recognition_per_channel=True,
        )
        for result in channel_results:
            print(f"Channel {result.channel}: " + " ".join(word.text for word in result.words))


if __name__ == "__main__":
    main()
