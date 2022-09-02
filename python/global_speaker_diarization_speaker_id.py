from soniox.transcribe_file import transcribe_file_stream
from soniox.speech_service import SpeechClient, set_api_key

set_api_key("<YOUR-API-KEY>")


def main():
    with SpeechClient() as client:
        result = transcribe_file_stream(
            "../test_data/test_audio_sd.flac",
            client,
            enable_global_speaker_diarization=True,
            min_num_speakers=1,
            max_num_speakers=6,
            enable_speaker_identification=True,
            cand_speaker_names=["John", "Judy"],
        )

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


if __name__ == "__main__":
    main()
