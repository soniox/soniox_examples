import time
from soniox.speech_service import SpeechClient, set_api_key
from soniox.transcribe_file import transcribe_file_async

set_api_key("<YOUR-API-KEY>")


def main():
    with SpeechClient() as client:
        print("Uploading file.")
        file_id = transcribe_file_async(
            "../test_data/test_audio_sd.flac",
            client,
            enable_global_speaker_diarization=True,
            min_num_speakers=1,
            max_num_speakers=6,
            enable_speaker_identification=True,
            cand_speaker_names=["John", "Judy"],
            transcribe_async_mode="instant_file",
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

            speaker = None
            speaker_num_to_name = {}
            speaker_num_to_name = {entry.speaker: entry.name for entry in result.speakers}
            for word in result.words:
                if word.speaker != speaker:
                    if speaker is not None:
                        print()
                    speaker = word.speaker
                    if speaker in speaker_num_to_name:
                        speaker_name = speaker_num_to_name[speaker]
                    else:
                        speaker_name = "unknown"
                    print(f"Speaker {speaker} ({speaker_name}): ", end="")
                else:
                    print(" ", end="")
                print(word.text, end="")
            print()
        else:
            print(f"Transcription failed with error: {status.error_message}")

        print("Calling DeleteTranscribeAsyncFile.")
        client.DeleteTranscribeAsyncFile(file_id)


if __name__ == "__main__":
    main()
