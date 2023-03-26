using Soniox.Types;
using Soniox.Client;
using Soniox.Client.Proto;

using var client = new SpeechClient();

var completeResult = await client.TranscribeFileShort(
    "../../test_data/test_audio.flac",
    new TranscriptionConfig { });

Result result = (completeResult as SingleResult)!.Result;

foreach (var word in result.Words)
{
    Console.WriteLine($"{word.Text} {word.StartMs} {word.DurationMs}");
}