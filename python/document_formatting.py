import time
import json
from soniox.speech_service import SpeechClient, DocumentFormattingConfig
from soniox.transcribe_file import transcribe_file_async


def main():
    with SpeechClient() as client:
        docfmt_config = {
            "format": {
                "end_of_sentence_spacing": "2",
                "numbers": "numeric",
                "ordinal_numbers": "abbreviated",
                "number_range": True,
                "digits": True,
                "DMY_date": "as_dictated",
                "MY_date": "as_dictated",
                "DM_date": "as_dictated",
                "clock_time": True,
                "time_quantity": True,
                "metric_units_abbreviated": True,
                "percent_symbol": True,
                "height_feet_inches": "text",
                "verbalized_punct": True,
            },
            "annotation": {
                "remove_section_phrase": True,
                "sections": [
                    {
                        "section_id": "ID1",
                        "title": "Introduction",
                        "phrases": [
                            "introduction",
                            "section intro",
                            "intro",
                        ],
                    },
                    {
                        "section_id": "ID2",
                        "title": "Plan",
                        "phrases": [
                            "section plan",
                        ],
                    },
                ],
            },
        }

        print("Uploading file.")
        file_id = transcribe_file_async(
            "PATH_TO_YOUR_AUDIO_FILE",
            client,
            reference_name="test",
            document_formatting_config=DocumentFormattingConfig(
                config_json=json.dumps(docfmt_config)
            ),
        )
        print(f"File ID: {file_id}")

        while True:
            print("Calling GetTranscribeAsyncStatus.")
            status = client.GetTranscribeAsyncStatus(file_id)
            print(f"Status: {status.status}")
            if status.status in ("COMPLETED", "FAILED"):
                break
            time.sleep(2.0)

        if status.status == "COMPLETED":
            print("Calling GetTranscribeAsyncResult")
            result = client.GetTranscribeAsyncResultAll(file_id)
            document = result.document

            print(f"Qscore: {document.qscore:.2f}")
            for section in document.sections:
                print(f"Section:")
                print(f"  Section ID: {repr(section.section_id)}")
                print(f"  Title: {repr(section.title)}")
                print(f"  Text: {repr(section.text)}")
                # print(f"  Tokens: {section.tokens}")
        else:
            print(f"Transcription failed with error: {status.error_message}")

        print("Calling DeleteTranscribeAsyncFile.")
        client.DeleteTranscribeAsyncFile(file_id)


if __name__ == "__main__":
    main()
