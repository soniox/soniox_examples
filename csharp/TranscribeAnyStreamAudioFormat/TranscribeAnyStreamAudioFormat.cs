using System.Linq;
using System.Runtime.CompilerServices;
using Soniox.Types;
using Soniox.Client;
using Soniox.Client.Proto;

using var client = new SpeechClient();

// TranscribeStream requires the user to provide the audio to transcribe
// as an IAsyncEnumerable<bytes[]> instance. This can be implemented as
// an async function that uses "yield return". This example function
// reads a file in chunks.
async IAsyncEnumerable<byte[]> EnumerateAudioChunks(
    [EnumeratorCancellation] CancellationToken cancellationToken = default(CancellationToken)
)
{
    string filePath = "../../test_data/test_audio_long.raw";
    int bufferSize = 1024;

    await using var fileStream = new FileStream(
        filePath, FileMode.Open, FileAccess.Read, FileShare.Read,
        bufferSize: bufferSize, useAsync: true
    );

    while (true)
    {
        byte[] buffer = new byte[bufferSize];
        int numRead = await fileStream.ReadAsync(buffer, cancellationToken);
        if (numRead == 0)
        {
            break;
        }
        Array.Resize(ref buffer, numRead);
        yield return buffer;
    }
}

IAsyncEnumerable<Result> resultsEnumerable = client.TranscribeStream(
    EnumerateAudioChunks(),
    new TranscriptionConfig
    {
        IncludeNonfinal = true,
        AudioFormat = "pcm_s16le",
        SampleRateHertz = 16000,
        NumAudioChannels = 1,
    });

await foreach (var result in resultsEnumerable)
{
    // Note result.Words contains final and non-final words,
    // we do not print this this information in this example.
    var wordsStr = string.Join(" ", result.Words.Select(word => word.Text).ToArray());
    Console.WriteLine($"Words: {wordsStr}");
}
