from typing import List, Tuple
import signal
import threading
import sys
from soniox.transcribe_live import transcribe_microphone
from soniox.speech_service import SpeechClient, Result, set_api_key


set_api_key("<YOUR-API-KEY>")


def split_words(result: Result) -> Tuple[List[str], List[str]]:
    final_words = []
    non_final_words = []
    for word in result.words:
        if word.is_final:
            final_words.append(word.text)
        else:
            non_final_words.append(word.text)
    return final_words, non_final_words


def clear_line():
    sys.stdout.write("\033[K")
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")


def render_final_words(words: List[str]) -> List[str]:
    MAX_CHAR_PER_LINE = 100

    clear_line()
    clear_line()

    line = " ".join(words)
    if len(line) <= MAX_CHAR_PER_LINE:
        print(line)
        return words

    # Find the word to break the line.
    idx = line.rfind(" ", 0, MAX_CHAR_PER_LINE)
    assert idx != -1

    # Print all the words until the break.
    print(line[:idx])

    # Print and return the remaining words after the break.
    line = line[idx + 1 :]
    print(line)
    return line.split()


def render_non_final_words(words: List[str]) -> None:
    if len(words) > 0:
        line = " ".join(words)
        print(f"\n: {line}", end="")
    else:
        print("")


def main():
    stop_event = threading.Event()

    def sigint_handler(sig, stack):
        print("Interrupted, finishing transcription...")
        stop_event.set()

    signal.signal(signal.SIGINT, sigint_handler)

    with SpeechClient() as client:
        print("Transcribing from your microphone ...\n\n")

        final_words_last_line = []

        for result in transcribe_microphone(client, stop_event=stop_event):
            # Split words into final words and non-final words.
            new_final_words, non_final_words = split_words(result)

            # Render final words in last line.
            final_words_last_line += new_final_words
            final_words_last_line = render_final_words(final_words_last_line)

            # Render non-final words.
            render_non_final_words(non_final_words)

    print("\nTranscription finished.")


if __name__ == "__main__":
    main()
