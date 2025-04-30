import os

import requests

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = os.environ["SONIOX_API_KEY"]
api_base = "https://api.soniox.com"

session = requests.Session()
session.headers["Authorization"] = f"Bearer {api_key}"


def main():
    print("Getting all transcriptions...")

    transcriptions = []
    cursor = ""

    # Get transcriptions endpoint returns max 1000 transcriptions so
    # cursor-based pagination is needed to get all transcriptions.
    while True:
        print("Getting transcriptions...")

        res = session.get(f"{api_base}/v1/transcriptions?cursor={cursor}")
        res.raise_for_status()
        res_json = res.json()

        for transcription in res_json["transcriptions"]:
            # Only delete completed transcriptions
            if (
                transcription["status"] == "completed"
                or transcription["status"] == "error"
            ):
                transcriptions.append(transcription)

        cursor = res_json["next_page_cursor"]

        if cursor is None:
            break

    total = len(transcriptions)

    if total == 0:
        print("No transcriptions found")
        return

    print(f"Deleting {total} transcriptions...")

    for i, transcription in enumerate(transcriptions):
        transcription_id = transcription["id"]

        print(f"Deleting transcription: {transcription_id} ({i + 1}/{total})")

        res = session.delete(f"{api_base}/v1/transcriptions/{transcription_id}")
        res.raise_for_status()


if __name__ == "__main__":
    main()
