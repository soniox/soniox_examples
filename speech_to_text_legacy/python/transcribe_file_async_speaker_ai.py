import time
from soniox.speech_service import SpeechClient
from soniox.transcribe_file import transcribe_file_async


def main():
    with SpeechClient() as client:
        print("Uploading file.")
        file_id = transcribe_file_async(
            "../test_data/test_audio_sd.flac",
            client,
            model="en_v2",
            enable_global_speaker_diarization=True,
            min_num_speakers=1,
            max_num_speakers=6,
            enable_speaker_identification=True,
            cand_speaker_names=["John", "Judy"],
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

            speaker_num_to_name = {entry.speaker: entry.name for entry in result.speakers}
            speaker = None
            line = ""
            for word in result.words:
                if word.speaker != speaker:
                    if len(line) > 0:
                        print(line)
                    speaker = word.speaker
                    if speaker in speaker_num_to_name:
                        speaker_name = speaker_num_to_name[speaker]
                    else:
                        speaker_name = "unknown"
                    line = f"Speaker {speaker} ({speaker_name}): "
                    if word.text == " ":
                        continue
                line += word.text
            print(line)
        else:
            print(f"Transcription failed with error: {status.error_message}")

        print("Calling DeleteTranscribeAsyncFile.")
        client.DeleteTranscribeAsyncFile(file_id)


if __name__ == "__main__":
    main()
