from soniox.transcribe_file import transcribe_file_short
from soniox.speech_service import SpeechClient, SpeechContext, SpeechContextEntry, set_api_key

set_api_key("<YOUR-API-KEY>")


def test(client: SpeechClient, audio_file: str, speech_context: SpeechContext) -> None:
    base_result = transcribe_file_short(audio_file, client)
    base_text = " ".join(w.text for w in base_result.words)

    adapted_result = transcribe_file_short(audio_file, client, speech_context=speech_context)
    adapted_text = " ".join(w.text for w in adapted_result.words)

    print(f"{audio_file}")
    print(f"  Base transcript: {base_text}")
    print(f"  With adaptation: {adapted_text}")
    print()


def main():
    with SpeechClient() as client:
        test(
            client,
            "../test_data/test_audio_speech_adaptation.flac",
            SpeechContext(
                entries=[
                    SpeechContextEntry(
                        phrases=["air"],
                        boost=-15.0,
                    ),
                    SpeechContextEntry(
                        phrases=["heir"],
                        boost=15.0,
                    ),
                ]
            ),
        )


if __name__ == "__main__":
    main()
