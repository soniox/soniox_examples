from soniox.transcribe_live import transcribe_microphone
from soniox.speech_service import SpeechClient


def main():
    with SpeechClient() as client:
        print("Transcribing from your microphone ...")
        all_final_tokens = []
        for result in transcribe_microphone(
            client,
            model="en_v2_lowlatency",
            include_nonfinal=True,
        ):
            # Split current result response into final and non-final tokens.
            final_tokens = []
            nonfinal_tokens = []
            for word in result.words:
                if word.is_final:
                    final_tokens.append(word.text)
                else:
                    nonfinal_tokens.append(word.text)

            # Append current final tokens to all final tokens.
            all_final_tokens += final_tokens

            # Print all final tokens and current non-final tokens.
            all_final_tokens_str = "".join(all_final_tokens)
            nonfinal_tokens_str = "".join(nonfinal_tokens)
            print(f"Final: {all_final_tokens_str}")
            print(f"Non-final: {nonfinal_tokens_str}")
            print("-----")


if __name__ == "__main__":
    main()
