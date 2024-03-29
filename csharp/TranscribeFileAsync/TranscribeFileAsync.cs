using Soniox.Types;
using Soniox.Client;
using Soniox.Client.Proto;

using var client = new SpeechClient();

var fileId = await client.TranscribeFileAsync(
    "../../test_data/test_audio_long.flac",
    new TranscriptionConfig
    {
        Model = "en_v2",
        ClientRequestReference = "test",
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
    var completeResult = await client.GetTranscribeAsyncResult(fileId);
    Result result = (completeResult as SingleResult)!.Result;
    var text = string.Join("", result.Words.Select(word => word.Text).ToArray());
    Console.WriteLine("Text: " + text);
}
else
{
    Console.WriteLine($"Transcription failed with error: {status.ErrorMessage}");
}

Console.WriteLine("Calling DeleteTranscribeAsyncFile.");
await client.DeleteTranscribeAsyncFile(fileId);