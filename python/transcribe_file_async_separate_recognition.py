import time
from soniox.speech_service import SpeechClient
from soniox.transcribe_file import transcribe_file_async


def main():
    with SpeechClient() as client:
        print("Uploading file.")
        file_id = transcribe_file_async(
            "../test_data/test_audio_multi_channel.flac",
            client,
            model="en_v2",
            num_audio_channels=2,
            enable_separate_recognition_per_channel=True,
            reference_name="test",
        )
        print(f"File ID: {file_id}")

        while True:
            print("Calling GetTranscribeAsyncStatus.")
            status = client.GetTranscribeAsyncStatus(file_id)
            print(f"Status: {status.status}")
            if status.status in ("COMPLETED", "FAILED"):
                break
            time.sleep(2.0)

        if status.status == "COMPLETED":
            print("Calling GetTranscribeAsyncResult")
            channel_results = client.GetTranscribeAsyncResult(file_id)
            for result in channel_results:
                print(f"Channel {result.channel}: " + "".join(word.text for word in result.words))
        else:
            print(f"Transcription failed with error: {status.error_message}")

        print("Calling DeleteTranscribeAsyncFile.")
        client.DeleteTranscribeAsyncFile(file_id)


if __name__ == "__main__":
    main()
