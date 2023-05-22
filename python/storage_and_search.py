from soniox.transcribe_file import transcribe_file_short
from soniox.speech_service import SpeechClient, StorageConfig
from soniox.storage import search_objects


def main():
    with SpeechClient() as client:
        storage_config = StorageConfig(
            object_id="my_id_for_audio",
            metadata={
                "company": "Nike",
                "agent": "12345",
            },
            title="Air Jordan shoes review",
        )
        transcribe_file_short(
            "../test_data/test_audio_storage.flac", client, storage_config=storage_config
        )

        # Search for objects with query "homesick".
        search_response = search_objects(client, text_query="air jordan")

        # Print search results.
        print(f"Results: {search_response.num_found}")
        for result in search_response.results:
            print(f"Object ID: {result.object_id}")
            print(f"Preview: {result.preview}")


if __name__ == "__main__":
    main()
