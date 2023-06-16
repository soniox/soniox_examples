from soniox.speech_service import SpeechClient
from soniox.utils import timestamp_to_datetime


def main():
    with SpeechClient() as client:
        response = client.CreateTemporaryApiKey(
            usage_type="transcribe_websocket",
            client_request_reference="test_reference",
        )

        print(f"API key: {response.key}")
        print(f"Expires: {timestamp_to_datetime(response.expires_datetime)}")


if __name__ == "__main__":
    main()
