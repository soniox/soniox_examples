import grpc
from soniox.speech_service_pb2 import TranscribeRequest, TranscriptionConfig
from soniox.speech_service_pb2_grpc import SpeechServiceStub


# Use default SSL credentials.
# This should be sufficient with recent gRPC versions.
creds = grpc.ssl_channel_credentials()

# If you are having problems with the secure connection, you should instead
# manually supply the roots.pem file (see below) and load it here like this.
# with open('roots.pem', 'rb') as f:
#     creds = grpc.ssl_channel_credentials(f.read())


def main():
    # Create secure channel with the credentials.
    with grpc.secure_channel("api.soniox.com:443", creds) as channel:
        # Create client.
        client = SpeechServiceStub(channel)
        # Create TranscribeRequest object.
        request = TranscribeRequest(
            config=TranscriptionConfig(
                model="en_v2",
            ),
        )
        # Set the API key.
        request.api_key = "<YOUR-API-KEY>"
        # Read the entire audio file.
        with open("../test_data/test_audio.flac", "rb") as fh:
            request.audio = fh.read()
        # Call Transcribe method with created TranscribeRequest object.
        response = client.Transcribe(request)
        # Print recognized tokens with start and duration.
        for w in response.result.words:
            print(f"'{w.text}' {w.start_ms} {w.duration_ms}")


if __name__ == '__main__':
    main()
