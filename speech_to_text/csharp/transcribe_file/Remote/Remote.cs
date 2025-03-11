using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

string apiBase = "https://api.soniox.com";
string audioUrl = "https://soniox.com/media/examples/coffee_shop.mp3";

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
string? apiKey = Environment.GetEnvironmentVariable("SONIOX_API_KEY");
if (string.IsNullOrEmpty(apiKey))
{
    throw new InvalidOperationException("SONIOX_API_KEY is not set.");
}

// Create a requests session and set the Authorization header
var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);

// 1. Start a new transcription session by sending the audio URL to the API
Console.WriteLine("Starting transcription...");

var request = new StringContent(
    JsonSerializer.Serialize(new { audio_url = audioUrl, model = "stt-async-preview" }),
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

Console.WriteLine($"Transcription started with ID: {transcriptionId}");

// 2. Poll the transcription endpoint until the status is 'completed'
while (true)
{
    response = await client.GetAsync($"{apiBase}/v1/transcriptions/{transcriptionId}");
    response.EnsureSuccessStatusCode();
    responseJson = await response.Content.ReadAsStringAsync();
    transcription = JsonNode.Parse(responseJson);

    var status = transcription?["status"]?.ToString();
    if (status == "error")
    {
        var errorMessage = transcription?["error_message"]?.ToString() ?? "Unknown error";
        throw new Exception($"Transcription error: {errorMessage}");
    }
    else if (status == "completed")
    {
        break;
    }

    await Task.Delay(1000);
}

// 3. Retrieve the final transcript once transcription is completed
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
