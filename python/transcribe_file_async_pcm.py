import time
from soniox.speech_service import SpeechClient
from soniox.transcribe_file import transcribe_file_async


def main():
    with SpeechClient() as client:
        print("Uploading file.")
        file_id = transcribe_file_async(
            "../test_data/test_audio_long.raw",
            client,
            model="en_v2",
            audio_format="pcm_s16le",
            sample_rate_hertz=16000,
            num_audio_channels=1,
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
            result = client.GetTranscribeAsyncResult(file_id)
            print(f"Text: " + "".join(word.text for word in result.words))
        else:
            print(f"Transcription failed with error: {status.error_message}")

        print("Calling DeleteTranscribeAsyncFile.")
        client.DeleteTranscribeAsyncFile(file_id)


if __name__ == "__main__":
    main()
