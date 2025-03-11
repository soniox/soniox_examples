from soniox.transcribe_file import transcribe_file_short
from soniox.speech_service import SpeechClient


def main():
    with SpeechClient() as client:
        result = transcribe_file_short(
            "../test_data/test_audio_sd.flac",
            client,
            model="en_v2",
            enable_global_speaker_diarization=True,
            min_num_speakers=1,
            max_num_speakers=6,
            enable_speaker_identification=True,
            cand_speaker_names=["John", "Judy"],
        )

    # Build map from speaker number to name.
    speaker_num_to_name = {entry.speaker: entry.name for entry in result.speakers}

    # Print results with each speaker segment on its own line.

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


if __name__ == "__main__":
    main()
