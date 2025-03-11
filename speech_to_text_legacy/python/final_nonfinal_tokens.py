from typing import Iterable
from soniox.transcribe_live import transcribe_stream
from soniox.speech_service import SpeechClient


def iter_audio() -> Iterable[bytes]:
    with open("../test_data/test_audio_long.flac", "rb") as fh:
        while True:
            audio = fh.read(1024)
            if len(audio) == 0:
                break
            yield audio


def main():
    with SpeechClient() as client:
        # All final tokens will be collected in this list.
        all_final_tokens = []

        for result in transcribe_stream(
            iter_audio(),
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
