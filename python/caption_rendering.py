from typing import Iterable, List
from soniox.transcribe_live import transcribe_stream, transcribe_microphone
from soniox.speech_service import SpeechClient, set_api_key
from soniox.speech_service_pb2 import Result, Word


set_api_key("<YOUR-API-KEY>")


def iter_audio() -> Iterable[bytes]:
    with open("../test_data/test_audio_long.flac", "rb") as fh:
        while True:
            audio = fh.read(1024)
            if len(audio) == 0:
                break
            yield audio


_PUNCT_SYMBOLS = (",", ".", "?", "!")


class CaptionRenderer:
    _max_line_length: int
    _max_lines: int
    _clear_after_ms: int
    _words: List[Word]

    def __init__(self, max_line_length: int, max_lines: int, clear_after_ms: int) -> None:
        self._max_line_length = max_line_length
        self._max_lines = max_lines
        self._clear_after_ms = clear_after_ms
        self._words = []

    # This should be called whenever a new result is received.
    # It returns the list of lines that should be on the screen
    # at this time.
    def update(self, result: Result) -> List[str]:
        # Remove previous non-final words.
        while len(self._words) > 0 and not self._words[-1].is_final:
            self._words.pop()

        # Add words from result.
        self._words.extend(result.words)

        # Render words into lines.

        # Complete lines:
        # - Texts of consecutive complete lines (without newline).
        lines_text: List[str] = []
        # - For each complete line (above), the number of words (Word objects)
        #   from which it was built. NOTE: It is not correct to count words
        #   in a line for this purpose, as word.text might have spaces.
        lines_num_words: List[int] = []

        # Current line:
        # - Parts of the current line that that will form its text.
        line_text_parts: List[str] = []
        # - Length of the current line.
        line_length = 0
        # - Number of words (Word objects) from which the current line was built.
        line_num_words = 0

        # Process current words.
        for word in self._words:
            # Check if the word is a punctuation symbol.
            is_punct = word.text in _PUNCT_SYMBOLS

            # Determine whether to add a space before the word.
            add_space = line_length > 0 and not is_punct

            # Check if we need to go to the next line.
            # Reserve one character for a possible following punctuation
            # symbol in order to prevent lines from starting with a
            # punctuation symbol.
            eff_max_len = self._max_line_length if is_punct else self._max_line_length - 1
            if line_length > 0 and line_length + int(add_space) + len(word.text) > eff_max_len:
                # Add the current line to complete lines.
                lines_text.append("".join(line_text_parts))
                lines_num_words.append(line_num_words)

                # Start a new line.
                line_text_parts = []
                line_length = 0
                line_num_words = 0

                # Never add a space at the start of a line.
                add_space = False

            # If needed add a space before the word.
            if add_space:
                line_text_parts.append(f" ")
                line_length += 1

            # Add the word to the current line.
            line_text_parts.append(word.text)
            line_length += len(word.text)
            line_num_words += 1

        # Add the current line to complete lines if there is one.
        if line_length > 0:
            lines_text.append("".join(line_text_parts))
            lines_num_words.append(line_num_words)

        # If we have more than two lines and all words in the first line
        # are final, then remove the first line along with corresponding
        # buffered words in _words.
        if len(lines_text) > 2 and all(word.is_final for word in self._words[: lines_num_words[0]]):
            del self._words[: lines_num_words[0]]
            del lines_text[0]
            del lines_num_words[0]

        # If at least clear_after_ms time has elapsed since the last word
        # and all words are final, then clear everything.
        if (
            len(self._words) > 0
            and result.total_proc_time_ms
            >= self._words[-1].start_ms + self._words[-1].duration_ms + self._clear_after_ms
            and all(word.is_final for word in self._words)
        ):
            self._words = []
            lines_text = []
            lines_num_words = []

        # If the number of current lines exceeds max_lines, remove a certain
        # number of initial lines before returning them. Note that we must
        # not remove corresponding words from _words.
        if len(lines_text) > self._max_lines:
            num_delete = len(lines_text) - self._max_lines
            del lines_text[:num_delete]
            del lines_num_words[:num_delete]

        # Return texts of lines.
        return lines_text


def main():
    with SpeechClient() as client:
        # Initialize caption renderer.
        caption_renderer = CaptionRenderer(
            max_line_length=45,
            max_lines=2,
            clear_after_ms=2000,
        )

        # Transcribe a file as a stream.
        results_iter = transcribe_stream(iter_audio(), client)
        # Or transcribe in real time from microphone.
        # results_iter = transcribe_microphone(client)

        # Process the stream of Result objects.
        for result in results_iter:
            # Add result to caption renderer, getting lines to be displayed.
            lines = caption_renderer.update(result)

            # At this point, in a real application, the GUI would be updated
            # to display exactly these lines (i.e., replace any currently
            # displayed lines with these). In this example, we simply print
            # two empty lines followed by the text lines.
            print()
            print()
            for line in lines:
                print(line)


if __name__ == "__main__":
    main()
