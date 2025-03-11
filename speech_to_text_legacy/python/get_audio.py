from typing import Iterable
from soniox.speech_service import SpeechClient
from soniox.speech_service_pb2 import GetAudioResponse
from soniox.storage import get_audio


# Helper function to save audio returned by GetAudio and print information.
def save_audio(responses_iter: Iterable[GetAudioResponse], file_path: str) -> None:
    print(f"Saving audio to: {file_path}")
    audio_file_size = 0
    with open(file_path, "wb") as fh:
        for response in responses_iter:
            fh.write(response.data)
            audio_file_size += len(response.data)
    print(f"Audio file size: {audio_file_size}")


def main():
    with SpeechClient() as client:
        object_id = "my_id_for_audio"

        # Get audio by time range.
        save_audio(
            get_audio(object_id, client, start_ms=1167, duration_ms=976, audio_bytes_format="wav"),
            "get_audio_time.wav",
        )

        # Get audio by token range.
        save_audio(
            get_audio(object_id, client, token_start=17, token_end=19, audio_bytes_format="wav"),
            "get_audio_token.wav",
        )


if __name__ == "__main__":
    main()
