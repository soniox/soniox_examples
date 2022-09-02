import threading
import signal
from soniox.capture_device import SimulatedCaptureDevice
from soniox.transcribe_live import transcribe_capture
from soniox.speech_service import SpeechClient

# Number of channels we transcribe in parallel.
NUM_CHANNELS = 8

# Lock to prevent overlapping printouts.
print_lock = threading.Lock()


class Channel:
    def __init__(self, channel_num: int, client: SpeechClient, stop_event: threading.Event) -> None:
        self._channel_num = channel_num
        self._client = client
        self._stop_event = stop_event

        # Create a SimulatedCaptureDevice.
        self._capture_device = SimulatedCaptureDevice("../test_data/test_audio.raw")

    def run(self) -> None:
        # Call transcribe_capture with our capture device to transcribe.
        # We specify include_nonfinal=True (the default) to request nonfinal
        # words. If they are not desired, specify False. For example this
        # could be done if the stream was going to be time delayed and
        # annotated with captions based only on final words.
        for result in transcribe_capture(
            self._capture_device, self._client, include_nonfinal=True, stop_event=self._stop_event
        ):
            # Print words.
            final_str = " ".join(w.text for w in result.words if w.is_final)
            nonfinal_str = " ".join(w.text for w in result.words if not w.is_final)
            with print_lock:
                print(f"Channel {self._channel_num}:")
                print(f"  Final: {final_str}")
                print(f"  Nonfinal: {nonfinal_str}")


def main():
    # Set up a threading.Event which will be set when CTRL+C is pressed.
    stop_event = threading.Event()

    def sigint_handler(sig, stack):
        print("Interrupted, finishing...")
        stop_event.set()

    signal.signal(signal.SIGINT, sigint_handler)

    # Create a client to use for all transcriptions.
    with SpeechClient() as client:
        # Create channels and start threads that run Channel.run.
        threads = []
        for channel_num in range(NUM_CHANNELS):
            channel = Channel(channel_num, client, stop_event)
            thread = threading.Thread(target=channel.run)
            thread.start()
            threads.append(thread)

        # Join the threads, which will finish soon after stop_event is set.
        for thread in threads:
            thread.join()


if __name__ == "__main__":
    main()
