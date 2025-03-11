import fetch from "node-fetch";

const API_BASE = "https://api.soniox.com";
const AUDIO_URL = "https://soniox.com/media/examples/coffee_shop.mp3";

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
const API_KEY = process.env.SONIOX_API_KEY;

const headers = {
  Authorization: `Bearer ${API_KEY}`,
  "Content-Type": "application/json",
};

// 1. Start a new transcription session by sending the audio URL to the API
console.log("Starting transcription...");
let response = await fetch(`${API_BASE}/v1/transcriptions`, {
  method: "POST",
  headers: headers,
  body: JSON.stringify({
    audio_url: AUDIO_URL,
    model: "stt-async-preview",
  }),
});

if (!response.ok) {
  throw new Error(`Failed to create transcription: ${response.statusText}`);
}

let transcription = await response.json();

const transcriptionId = transcription.id;
console.log(`Transcription started with ID: ${transcriptionId}`);

// 2. Poll the transcription endpoint until the status is 'completed'
while (true) {
  response = await fetch(`${API_BASE}/v1/transcriptions/${transcriptionId}`, {
    method: "GET",
    headers: headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to get transcription: ${response.statusText}`);
  }

  transcription = await response.json();

  const status = transcription.status;
  if (status === "error") {
    throw new Error(
      `Transcription error: ${transcription.error_message || "Unknown error"}`
    );
  } else if (status === "completed") {
    // Stop polling when the transcription is complete
    break;
  }

  // Wait for 1 second before polling again
  await new Promise((resolve) => setTimeout(resolve, 1000));
}

// 3. Retrieve the final transcript once transcription is completed
response = await fetch(
  `${API_BASE}/v1/transcriptions/${transcriptionId}/transcript`,
  {
    method: "GET",
    headers: headers,
  }
);

if (!response.ok) {
  throw new Error(`Failed to get transcript: ${response.statusText}`);
}

const transcript = await response.json();

// Print the transcript text
console.log("Transcript:");
console.log(transcript.text);
