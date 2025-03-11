using Soniox.Types;
using Soniox.Client;
using Soniox.Client.Proto;

using var client = new SpeechClient();

var completeResult = await client.TranscribeFileStream(
    "../../test_data/test_audio_long.flac",
    new TranscriptionConfig
    {
        Model = "en_v2",
    });

Result result = (completeResult as SingleResult)!.Result;

var text = string.Join("", result.Words.Select(word => word.Text).ToArray());
Console.WriteLine("Text: " + text);
Console.WriteLine("Tokens:");
foreach (var word in result.Words)
{
    Console.WriteLine($"    '{word.Text}' {word.StartMs} {word.DurationMs}");
}