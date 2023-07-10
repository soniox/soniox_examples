using Json.Net;
using Soniox.Types;
using Soniox.Client;
using Soniox.Client.Proto;

using var client = new SpeechClient();

var docfmtConfig = new Dictionary<string, object> {
    {"format", new Dictionary<string, object> {
        {"end_of_sentence_spacing", "2"},
        {"numbers", "numeric"},
        {"ordinal_numbers", "abbreviated"},
        {"number_range", true},
        {"digits", true},
        {"DMY_date", "as_dictated"},
        {"MY_date", "as_dictated"},
        {"DM_date", "as_dictated"},
        {"clock_time", true},
        {"time_quantity", true},
        {"metric_units_abbreviated", true},
        {"percent_symbol", true},
        {"height_feet_inches", "text"},
        {"verbalized_punct", true},
    }},
    {"annotation", new Dictionary<string, object> {
        {"remove_section_phrase", true},
        {"sections", new List<object> {
            new Dictionary<string, object> {
                {"section_id", "ID1"},
                {"title", "Introduction"},
                {"phrases", new List<string> {
                    "introduction",
                    "section intro",
                    "intro",
                }},
            },
            new Dictionary<string, object> {
                {"section_id", "ID2"},
                {"title", "Plan"},
                {"phrases", new List<string> {
                    "section plan",
                }},
            },
        }},
    }},
};

var fileId = await client.TranscribeFileAsync(
    "PATH_TO_YOUR_AUDIO_FILE",
    new TranscriptionConfig
    {
        DocumentFormattingConfig = new DocumentFormattingConfig
        {
            ConfigJson = JsonNet.Serialize(docfmtConfig),
        },
    });

Console.WriteLine($"File ID: {fileId}");

TranscribeAsyncFileStatus status;
while (true)
{
    Console.WriteLine("Calling GetTranscribeAsyncFileStatus.");
    status = await client.GetTranscribeAsyncFileStatus(fileId);
    if (status.Status is "COMPLETED" or "FAILED")
    {
        break;
    }
    await Task.Delay(2000);
}

if (status.Status == "COMPLETED")
{
    Console.WriteLine("Calling GetTranscribeAsyncResult");
    var result = await client.GetTranscribeAsyncResultAll(fileId);
    var document = result.Document;
    if (document == null)
    {
        throw new System.Exception("No document!?");
    }
    Console.WriteLine($"Qscore: {document.Qscore:0.00}");
    foreach (var section in document.Sections)
    {
        Console.WriteLine($"  Section ID: {section.SectionId}");
        Console.WriteLine($"  Title: {section.Title}");
        Console.WriteLine($"  Text: {section.Text}");
    }
}
else
{
    Console.WriteLine($"Transcription failed with error: {status.ErrorMessage}");
}

Console.WriteLine("Calling DeleteTranscribeAsyncFile.");
await client.DeleteTranscribeAsyncFile(fileId);
