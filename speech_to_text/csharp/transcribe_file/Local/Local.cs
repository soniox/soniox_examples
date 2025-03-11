using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;

string apiBase = "https://api.soniox.com";
string fileToTranscribe = "coffee_shop.mp3";

// Retrieve the API key from the environment variable
string? apiKey = Environment.GetEnvironmentVariable("SONIOX_API_KEY");
if (string.IsNullOrEmpty(apiKey))
{
    throw new InvalidOperationException("SONIOX_API_KEY is not set.");
}

// Create a requests session and set the Authorization header
var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", apiKey);

// 1. Upload file
Console.WriteLine("Starting file upload...");
using var fileStream = new FileStream(fileToTranscribe, FileMode.Open, FileAccess.Read);
var fileContent = new MultipartFormDataContent();
fileContent.Add(new StreamContent(fileStream), "file", Path.GetFileName(fileToTranscribe));

var response = await client.PostAsync($"{apiBase}/v1/files", fileContent);
response.EnsureSuccessStatusCode();
var responseJson = await response.Content.ReadAsStringAsync();
var file = JsonNode.Parse(responseJson);

// Ensure file is parsed correctly
var fileId = file?["id"]?.ToString();
if (string.IsNullOrEmpty(fileId))
{
    throw new InvalidOperationException("File ID is missing after upload.");
}

// 2. Start a new transcription session
Console.WriteLine("Starting transcription...");
var request = new StringContent(
    JsonSerializer.Serialize(new { file_id = fileId, model = "stt-async-preview" }),
    System.Text.Encoding.UTF8,
    "application/json"
);
response = await client.PostAsync($"{apiBase}/v1/transcriptions", request);
response.EnsureSuccessStatusCode();
responseJson = await response.Content.ReadAsStringAsync();

var transcription = JsonNode.Parse(responseJson);
var transcriptionId = transcription?["id"]?.ToString();
if (string.IsNullOrEmpty(transcriptionId))
{
    throw new InvalidOperationException("Transcription ID is missing.");
}

Console.WriteLine($"Transcription started with ID: {transcriptionId}");

// 3. Poll the transcription endpoint until the status is 'completed'
while (true)
{
    response = await client.GetAsync($"{apiBase}/v1/transcriptions/{transcriptionId}");
    response.EnsureSuccessStatusCode();
    responseJson = await response.Content.ReadAsStringAsync();
    transcription = JsonNode.Parse(responseJson);

    var status = transcription?["status"]?.ToString();
    if (string.IsNullOrEmpty(status))
    {
        throw new InvalidOperationException("Status is missing in transcription response.");
    }

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

// 4. Retrieve the final transcript
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
