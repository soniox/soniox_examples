from datetime import datetime

from soniox.speech_service import SpeechClient
from soniox.storage import list_objects


def main():
    with SpeechClient() as client:
        # List objects.
        list_response = list_objects(
            client,
            stored_datetime_from=datetime.fromisoformat("2023-02-01T00:00+00:00"),
            stored_datetime_to=datetime.fromisoformat("2023-05-01T00:00+00:00"),
            start=0,
            num=10,
        )

        # Print objects.
        for obj in list_response.objects:
            print(f"Object ID: {obj.object_id}")


if __name__ == "__main__":
    main()
