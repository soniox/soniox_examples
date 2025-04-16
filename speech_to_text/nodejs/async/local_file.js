import fetch from "node-fetch";
import { readFile } from "node:fs/promises";

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
const apiKey = process.env.SONIOX_API_KEY;
const apiBase = "https://api.soniox.com";
const fileToTranscribe = "coffee_shop.mp3";

async function pollUntilComplete(transcriptionId) {
  while (true) {
    let res = await fetch(`${apiBase}/v1/transcriptions/${transcriptionId}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
    });
    if (!res.ok) {
      throw new Error(`Failed to get transcription: ${res.statusText}`);
    }
    const transcription = await res.json();
    if (transcription.status === "completed") {
      break;
    } else if (transcription.status === "error") {
      throw new Error(
        `Transcription error: ${transcription.error_message || "Unknown error"}`
      );
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
}

console.log("Starting file upload...");

const fileBuffer = await readFile(fileToTranscribe);
const fileBlob = new Blob([fileBuffer]);
const fileFormData = new FormData();
fileFormData.append("file", fileBlob);

let res = await fetch(`${apiBase}/v1/files`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
  },
  body: fileFormData,
});
if (!res.ok) {
  throw new Error(`Failed to upload file: ${res.statusText}`);
}
const file = await res.json();

console.log("Starting transcription...");

res = await fetch(`${apiBase}/v1/transcriptions`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    file_id: file.id,
    model: "stt-async-preview",
    language_hints: ["en", "es"],
  }),
});
if (!res.ok) {
  throw new Error(`Failed to create transcription: ${res.statusText}`);
}
const transcription = await res.json();
console.log(`Transcription ID: ${transcription.id}`);

await pollUntilComplete(transcription.id);

// Get the transcript text
res = await fetch(
  `${apiBase}/v1/transcriptions/${transcription.id}/transcript`,
  {
    method: "GET",
    headers: {
      Authorization: `Bearer ${apiKey}`,
    },
  }
);
if (!res.ok) {
  throw new Error(`Failed to get transcript: ${res.statusText}`);
}
const transcript = await res.json();
console.log("Transcript:");
console.log(transcript.text);
