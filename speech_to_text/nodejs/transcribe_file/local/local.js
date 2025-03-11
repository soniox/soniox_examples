import fetch from "node-fetch";
import { readFile } from "node:fs/promises";

const API_BASE = "https://api.soniox.com";
const FILE_TO_TRANSCRIBE = "coffee_shop.mp3";

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
const API_KEY = process.env.SONIOX_API_KEY;

const headers = {
  Authorization: `Bearer ${API_KEY}`,
};

// 1. Upload a file
console.log("Starting file upload...");
const fileBuffer = await readFile(FILE_TO_TRANSCRIBE);
const fileBlob = new Blob([fileBuffer]);
const fileFormData = new FormData();

fileFormData.append("file", fileBlob);

let response = await fetch(`${API_BASE}/v1/files`, {
  method: "POST",
  headers: headers,
  body: fileFormData,
});

if (!response.ok) {
  throw new Error(`Failed to upload file: ${response.statusText}`);
}

const file = await response.json();

// 2. Start a new transcription session by sending the audio URL to the API
console.log("Starting transcription...");
response = await fetch(`${API_BASE}/v1/transcriptions`, {
  method: "POST",
  headers: {
    ...headers,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    file_id: file.id,
    model: "stt-async-preview",
  }),
});

if (!response.ok) {
  throw new Error(`Failed to create transcription: ${response.statusText}`);
}

let transcription = await response.json();

const transcriptionId = transcription.id;
console.log(`Transcription started with ID: ${transcriptionId}`);

// 3. Poll the transcription endpoint until the status is 'completed'
while (true) {
  let response = await fetch(
    `${API_BASE}/v1/transcriptions/${transcription.id}`,
    {
      method: "GET",
      headers: headers,
    }
  );

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

// 4. Retrieve the final transcript once transcription is completed
response = await fetch(
  `${API_BASE}/v1/transcriptions/${transcription.id}/transcript`,
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
