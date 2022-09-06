from soniox.transcribe_file import transcribe_file_short
from soniox.speech_service import SpeechClient, set_api_key
from soniox.speech_service import SpeechContext, SpeechContextEntry

set_api_key("<YOUR-API-KEY>")


def main():
    with SpeechClient() as client:
        # Create SpeechContext.
        speech_context = SpeechContext(
            entries=[
                SpeechContextEntry(
                    phrases=["acetylcarnitine"],
                    boost=20,
                ),
                SpeechContextEntry(
                    phrases=["zestoretic"],
                    boost=20,
                )
            ]
        )

        # Pass SpeechContext with transcribe request.
        result = transcribe_file_short(
            "../test_data/acetylcarnitine_zestoretic.flac", 
            client, 
            speech_context=speech_context
        )

        print(" ".join(word.text for word in result.words))


if __name__ == "__main__":
    main()
