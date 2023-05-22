from soniox.transcribe_live import transcribe_stream
from soniox.speech_service import SpeechClient


def iter_audio():
    with open("../test_data/test_audio_long.flac", "rb") as fh:
        while True:
            audio = fh.read(1024)
            if len(audio) == 0:
                break
            yield audio


def main():
    with SpeechClient() as client:
        # All final words will be collected in this list.
        all_final_words = []

        for result in transcribe_stream(iter_audio(), client):
            # Split current result response into final words and non-final words.
            final_words = []
            non_final_words = []
            for word in result.words:
                if word.is_final:
                    final_words.append(word.text)
                else:
                    non_final_words.append(word.text)

            # Append current final words to all final words.
            all_final_words += final_words

            # Print all final words and current non-final words.
            all_final_words_str = " ".join(all_final_words)
            non_final_words_str = " ".join(non_final_words)
            print(f"Final: {all_final_words_str}")
            print(f"Non-final: {non_final_words_str}")
            print("-----")


if __name__ == "__main__":
    main()
