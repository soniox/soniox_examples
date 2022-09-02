from soniox.speech_service import SpeechClient, set_api_key

set_api_key("<YOUR-API-KEY>")


def main():
    with SpeechClient() as client:
        print("Calling GetTranscribeAsyncAllFilesStatus.")
        files_status = client.GetTranscribeAsyncAllFilesStatus()

        for file_status in files_status:
            print(
                f"File ID: {file_status.file_id}, status: {file_status.status}, created: {file_status.created_time.ToDatetime()}"
            )

            if file_status.status != "TRANSCRIBING":
                print("Calling DeleteTranscribeAsyncFile.")
                client.DeleteTranscribeAsyncFile(file_status.file_id)


if __name__ == "__main__":
    main()
