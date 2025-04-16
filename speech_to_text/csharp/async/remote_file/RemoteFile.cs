using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
string? apiKey = Environment.GetEnvironmentVariable("SONIOX_API_KEY");
if (string.IsNullOrEmpty(apiKey))
{
    throw new InvalidOperationException("SONIOX_API_KEY is not set.");
}
string apiBase = "https://api.soniox.com";
string audioUrl = "https://soniox.com/media/examples/coffee_shop.mp3";

var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);

async Task pollUntilComplete(string transcriptionId) {
    while (true)
    {
        var response = await client.GetAsync($"{apiBase}/v1/transcriptions/{transcriptionId}");
        response.EnsureSuccessStatusCode();
        var responseJson = await response.Content.ReadAsStringAsync();
        var transcription = JsonNode.Parse(responseJson);
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

Console.WriteLine("Starting transcription...");

var request = new StringContent(
    JsonSerializer.Serialize(new {
        audio_url = audioUrl,
        model = "stt-async-preview",
        language_hints = new []{"en", "es"}
    }),
    System.Text.Encoding.UTF8,
    "application/json"
);
var response = await client.PostAsync($"{apiBase}/v1/transcriptions", request);
response.EnsureSuccessStatusCode();
var responseJson = await response.Content.ReadAsStringAsync();
var transcription = JsonNode.Parse(responseJson);
var transcriptionId = transcription?["id"]?.ToString();
if (string.IsNullOrEmpty(transcriptionId))
{
    throw new InvalidOperationException("Transcription ID is missing.");
}

Console.WriteLine($"Transcription ID: {transcriptionId}");

await pollUntilComplete(transcriptionId);

// Get the transcript text
response = await client.GetAsync($"{apiBase}/v1/transcriptions/{transcriptionId}/transcript");
response.EnsureSuccessStatusCode();
responseJson = await response.Content.ReadAsStringAsync();
var transcript = JsonNode.Parse(responseJson);
var transcriptText = transcript?["text"]?.ToString();
if (string.IsNullOrEmpty(transcriptText))
{
    throw new InvalidOperationException("Transcript text is missing.");
}
Console.WriteLine("Transcript:");
Console.WriteLine(transcriptText);
