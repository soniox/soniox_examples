from datetime import datetime
from soniox.speech_service import SpeechClient
from soniox.storage import search_objects


def main():
    with SpeechClient() as client:
        # Search for objects.
        search_response = search_objects(
            client,
            datetime_from=datetime.fromisoformat("2023-01-31T00:00+00:00"),
            metadata_query='company="Nike" AND agent="12345"',
            text_query="air jordan",
            num=20,
        )

        # Print search results.
        print(f"Results: {search_response.num_found}")
        for result in search_response.results:
            print(f"Object ID: {result.object_id}")
            print(f"Preview: {result.preview}")


if __name__ == "__main__":
    main()
