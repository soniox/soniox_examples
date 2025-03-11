import os
from soniox.transcribe_file import transcribe_file_short
from soniox.speech_service import SpeechClient, SpeechContext, SpeechContextEntry


# Loads the domain vocabulary from a file into a new SpeechContext.
# Each line in the file must be of the form <phrase><tab><boost>.
def load_domain_vocabulary(vocab_path: str) -> SpeechContext:
    speech_context = SpeechContext()

    with open(vocab_path, "r") as fh:
        for line in fh:
            line = line.strip()
            if len(line) == 0:
                continue
            parts = line.split("\t")
            print(parts)
            if len(parts) != 2:
                raise Exception("Incorrect line.")
            phrase = parts[0]
            boost = int(parts[1])
            speech_context.entries.append(
                SpeechContextEntry(
                    phrases=[phrase],
                    boost=boost,
                )
            )

    return speech_context


def main():
    # Load the domain vocabulary.
    THIS_DIR = os.path.realpath(os.path.dirname(__file__))
    speech_context = load_domain_vocabulary(os.path.join(THIS_DIR, "domain_vocabulary.tsv"))

    # Trainscribe a file using the speech context.
    with SpeechClient() as client:
        result = transcribe_file_short(
            "../test_data/test_audio.flac", client, speech_context=speech_context
        )
        print(" ".join(w.text for w in result.words))


if __name__ == "__main__":
    main()
