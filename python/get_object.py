from soniox.speech_service import SpeechClient
from soniox.storage import get_object


def main():
    with SpeechClient() as client:
        object_id = "my_id_for_audio"

        # Get object.
        stored_object = get_object(object_id, client)

        # Print transcript tokens and text.
        transcript = stored_object.transcript
        print([token.text for token in transcript.tokens])
        print(transcript.text)


if __name__ == "__main__":
    main()
