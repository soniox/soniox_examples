using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

// Retrieve the API key from the environment variable
string? apiKey = Environment.GetEnvironmentVariable("SONIOX_API_KEY");
if (string.IsNullOrEmpty(apiKey))
{
    throw new InvalidOperationException("SONIOX_API_KEY is not set.");
}
string apiBase = "https://api.soniox.com";
string fileToTranscribe = "../../coffee_shop.mp3";

var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);

async Task pollUntilComplete(string transcriptionId) {
    while (true)
    {
        var res = await client.GetAsync($"{apiBase}/v1/transcriptions/{transcriptionId}");
        res.EnsureSuccessStatusCode();
        var resJson = await res.Content.ReadAsStringAsync();
        var transcription = JsonNode.Parse(resJson);
        var status = transcription?["status"]?.ToString();
        if (string.IsNullOrEmpty(status))
        {
            throw new InvalidOperationException("Status is missing in transcription response.");
        }
        if (status == "completed")
        {
            return;
        }
        else if (status == "error")
        {
            var errorMessage = transcription?["error_message"]?.ToString() ?? "Unknown error";
            throw new Exception($"Transcription error: {errorMessage}");
        }
        await Task.Delay(1000);
    }
}

Console.WriteLine("Starting file upload...");

using var fileStream = new FileStream(fileToTranscribe, FileMode.Open, FileAccess.Read);
var fileContent = new MultipartFormDataContent();
fileContent.Add(new StreamContent(fileStream), "file", Path.GetFileName(fileToTranscribe));
var res = await client.PostAsync($"{apiBase}/v1/files", fileContent);
res.EnsureSuccessStatusCode();
var resJson = await res.Content.ReadAsStringAsync();
var file = JsonNode.Parse(resJson);
var fileId = file?["id"]?.ToString();
if (string.IsNullOrEmpty(fileId))
{
    throw new InvalidOperationException("File ID is missing after upload.");
}

Console.WriteLine("Starting transcription...");

var request = new StringContent(
    JsonSerializer.Serialize(new {
        file_id = fileId,
        model = "stt-async-preview",
        language_hints = new []{"en", "es"}
    }),
    System.Text.Encoding.UTF8,
    "application/json"
);
res = await client.PostAsync($"{apiBase}/v1/transcriptions", request);
res.EnsureSuccessStatusCode();
resJson = await res.Content.ReadAsStringAsync();
var transcription = JsonNode.Parse(resJson);
var transcriptionId = transcription?["id"]?.ToString();
if (string.IsNullOrEmpty(transcriptionId))
{
    throw new InvalidOperationException("Transcription ID is missing.");
}

Console.WriteLine($"Transcription ID: {transcriptionId}");

await pollUntilComplete(transcriptionId);

// Get the transcript text
res = await client.GetAsync($"{apiBase}/v1/transcriptions/{transcriptionId}/transcript");
res.EnsureSuccessStatusCode();
resJson = await res.Content.ReadAsStringAsync();
var transcript = JsonNode.Parse(resJson);
var transcriptText = transcript?["text"]?.ToString();
if (string.IsNullOrEmpty(transcriptText))
{
    throw new InvalidOperationException("Transcript text is missing.");
}
Console.WriteLine("Transcript:");
Console.WriteLine(transcriptText);

// Delete the transcription
res = await client.DeleteAsync($"{apiBase}/v1/transcriptions/{transcriptionId}");
res.EnsureSuccessStatusCode();

// Delete the file
res = await client.DeleteAsync($"{apiBase}/v1/files/{fileId}");
res.EnsureSuccessStatusCode();
