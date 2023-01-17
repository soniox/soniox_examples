import time
from soniox.speech_service import SpeechClient, set_api_key
from soniox.transcribe_file import transcribe_file_async

set_api_key("<YOUR-API-KEY>")


def main():
    with SpeechClient() as client:
        print("Uploading file.")
        file_id = transcribe_file_async(
            "../test_data/test_audio_long.flac", client, reference_name="test"
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
            print("Words: " + " ".join(w.text for w in result.words))
        else:
            print(f"Transcription failed with error: {status.error_message}")

        print("Calling DeleteTranscribeAsyncFile.")
        client.DeleteTranscribeAsyncFile(file_id)


if __name__ == "__main__":
    main()
