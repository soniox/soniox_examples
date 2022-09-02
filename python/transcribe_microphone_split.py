from soniox.transcribe_live import transcribe_microphone
from soniox.speech_service import SpeechClient, set_api_key

set_api_key("<YOUR-API-KEY>")


def main():
    with SpeechClient() as client:
        print("Transcribing from your microphone ...")
        all_final_words = []
        for result in transcribe_microphone(client):
            # Split current result response into final words and non-final words.
            final_words = []
            non_final_words = []
            for word in result.words:
                if word.is_final:
                    final_words.append(word.text)
                else:
                    non_final_words.append(word.text)

            # Append current final words to the list of all final words.
            all_final_words += final_words

            # Print all final words and current non-final words.
            all_final_words_str = " ".join(all_final_words)
            non_final_words_str = " ".join(non_final_words)
            print(f"Final: {all_final_words_str}")
            print(f"Non-final: {non_final_words_str}")
            print("-----")


if __name__ == "__main__":
    main()
