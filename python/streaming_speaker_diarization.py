from soniox.transcribe_live import transcribe_capture
from soniox.capture_device import SimulatedCaptureDevice
from soniox.speech_service import SpeechClient, set_api_key

set_api_key("<YOUR-API-KEY>")


def main():
    with SpeechClient() as client:
        sim_capture = SimulatedCaptureDevice("../test_data/test_audio_sd.raw")
        for result in transcribe_capture(
            sim_capture, client, enable_streaming_speaker_diarization=True
        ):
            print(" ".join(f"{w.text}/{w.speaker}" for w in result.words))


if __name__ == "__main__":
    main()
