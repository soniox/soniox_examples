import os

import requests

# Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
api_key = os.environ["SONIOX_API_KEY"]
api_base = "https://api.soniox.com"

session = requests.Session()
session.headers["Authorization"] = f"Bearer {api_key}"


def main():
    print("Getting all files...")

    files = []
    cursor = ""

    # Get files endpoint returns max 1000 files so cursor-based pagination is
    # needed to get all files.
    while True:
        print("Getting files...")

        res = session.get(f"{api_base}/v1/files?cursor={cursor}")
        res.raise_for_status()
        res_json = res.json()

        files.extend(res_json["files"])

        cursor = res_json["next_page_cursor"]

        if cursor is None:
            break
    
    total = len(files)

    if total == 0:
        print("No files found")
        return

    print(f"Deleting {total} files...")

    for i, file in enumerate(files):
        file_id = file["id"]

        print(f"Deleting file: {file_id} ({i + 1}/{total})")

        res = session.delete(f"{api_base}/v1/files/{file_id}")
        res.raise_for_status()


if __name__ == "__main__":
    main()
