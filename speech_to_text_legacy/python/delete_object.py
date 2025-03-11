from soniox.speech_service import SpeechClient
from soniox.storage import delete_object


def main():
    with SpeechClient() as client:
        object_id = "my_id_for_audio"

        # Delete object.
        delete_object(object_id, client)


if __name__ == "__main__":
    main()
