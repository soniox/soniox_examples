import fs from "fs";
import process from "process";
import { parseArgs } from "node:util";

const SONIOX_API_BASE_URL = "https://api.soniox.com";

// Get Soniox STT config.
function getConfig(audioUrl, fileId, translation) {
  const config = {
    // Select the model to use.
    // See: soniox.com/docs/stt/models
    model: "stt-async-v3",

    // Set language hints when possible to significantly improve accuracy.
    // See: soniox.com/docs/stt/concepts/language-hints
    language_hints: ["en", "es"],

    // Enable language identification. Each token will include a "language" field.
    // See: soniox.com/docs/stt/concepts/language-identification
    enable_language_identification: true,

    // Enable speaker diarization. Each token will include a "speaker" field.
    // See: soniox.com/docs/stt/concepts/speaker-diarization
    enable_speaker_diarization: true,

    // Set context to help the model understand your domain, recognize important terms,
    // and apply custom vocabulary and translation preferences.
    // See: soniox.com/docs/stt/concepts/context
    context: {
      general: [
        { key: "domain", value: "Healthcare" },
        { key: "topic", value: "Diabetes management consultation" },
        { key: "doctor", value: "Dr. Martha Smith" },
        { key: "patient", value: "Mr. David Miller" },
        { key: "organization", value: "St John's Hospital" },
      ],
      text: "Mr. David Miller visited his healthcare provider last month for a routine follow-up related to diabetes care. The clinician reviewed his recent test results, noted improved glucose levels, and adjusted his medication schedule accordingly. They also discussed meal planning strategies and scheduled the next check-up for early spring.",
      terms: [
        "Celebrex",
        "Zyrtec",
        "Xanax",
        "Prilosec",
        "Amoxicillin Clavulanate Potassium",
      ],
      translation_terms: [
        { source: "Mr. Smith", target: "Sr. Smith" },
        { source: "St John's", target: "St John's" },
        { source: "stroke", target: "ictus" },
      ],
    },

    // Optional identifier to track this request (client-defined).
    // See: https://soniox.com/docs/stt/api-reference/transcriptions/create_transcription#request
    client_reference_id: "MyReferenceId",

    // Audio source (only one can specified):
    // - Public URL of the audio file.
    // - File ID of a previously uploaded file
    // See: https://soniox.com/docs/stt/api-reference/transcriptions/create_transcription#request
    audio_url: audioUrl,
    file_id: fileId,
  };

  // Webhook.
  // You can set a webhook to get notified when the transcription finishes or fails.
  // See: https://soniox.com/docs/stt/api-reference/transcriptions/create_transcription#request

  // Translation options.
  // See: soniox.com/docs/stt/rt/real-time-translation#translation-modes
  if (translation === "one_way") {
    // Translates all languages into the target language.
    config.translation = { type: "one_way", target_language: "es" };
  } else if (translation === "two_way") {
    // Translates from language_a to language_b and back from language_b to language_a.
    config.translation = {
      type: "two_way",
      language_a: "en",
      language_b: "es",
    };
  } else if (translation !== "none") {
    throw new Error(`Unsupported translation: ${translation}`);
  }

  return config;
}

// Adds Soniox API_KEY to each request.
async function apiFetch(endpoint, { method = "GET", body, headers = {} } = {}) {
  const apiKey = process.env.SONIOX_API_KEY;
  if (!apiKey) {
    throw new Error(
      "Missing SONIOX_API_KEY.\n" +
        "1. Get your API key at https://console.soniox.com\n" +
        "2. Run: export SONIOX_API_KEY=<YOUR_API_KEY>",
    );
  }

  const res = await fetch(`${SONIOX_API_BASE_URL}${endpoint}`, {
    method,
    headers: {
      Authorization: `Bearer ${apiKey}`,
      ...headers,
    },
    body,
  });

  if (!res.ok) {
    const msg = await res.text();
    console.log(msg);
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${msg}`);
  }

  return method !== "DELETE" ? res.json() : null;
}

async function uploadAudio(audioPath) {
  console.log("Starting file upload...");

  const form = new FormData();
  form.append("file", new Blob([fs.readFileSync(audioPath)]), audioPath);

  const res = await apiFetch("/v1/files", {
    method: "POST",
    body: form,
  });

  console.log(`File ID: ${res.id}`);
  return res.id;
}

async function createTranscription(config) {
  console.log("Creating transcription...");
  const res = await apiFetch("/v1/transcriptions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  console.log(`Transcription ID: ${res.id}`);
  return res.id;
}

async function waitUntilCompleted(transcriptionId) {
  console.log("Waiting for transcription...");
  while (true) {
    const res = await apiFetch(`/v1/transcriptions/${transcriptionId}`);
    if (res.status === "completed") return;
    if (res.status === "error") throw new Error(`Error: ${res.error_message}`);
    await new Promise((r) => setTimeout(r, 1000));
  }
}

async function getTranscription(transcriptionId) {
  return apiFetch(`/v1/transcriptions/${transcriptionId}/transcript`);
}

async function deleteTranscription(transcriptionId) {
  await apiFetch(`/v1/transcriptions/${transcriptionId}`, { method: "DELETE" });
}

async function deleteFile(fileId) {
  await apiFetch(`/v1/files/${fileId}`, { method: "DELETE" });
}

async function deleteAllFiles() {
  let files = [];
  let cursor = "";

  while (true) {
    const res = await apiFetch(`/v1/files?cursor=${cursor}`);
    files = files.concat(res.files);
    cursor = res.next_page_cursor;
    if (!cursor) break;
  }

  if (files.length === 0) {
    console.log("No files to delete.");
    return;
  }

  console.log(`Deleting ${files.length} files...`);
  for (let i = 0; i < files.length; i++) {
    console.log(`Deleting file: ${files[i].id} (${i + 1}/${files.length})`);
    await deleteFile(files[i].id);
  }
}

async function deleteAllTranscriptions() {
  let transcriptions = [];
  let cursor = "";

  while (true) {
    const res = await apiFetch(`/v1/transcriptions?cursor=${cursor}`);
    // Delete only transcriptions with completed or error status.
    transcriptions = transcriptions.concat(
      res.transcriptions.filter(
        (t) => t.status === "completed" || t.status === "error",
      ),
    );
    cursor = res.next_page_cursor;
    if (!cursor) break;
  }

  if (transcriptions.length === 0) {
    console.log("No transcriptions to delete.");
    return;
  }

  console.log(`Deleting ${transcriptions.length} transcriptions...`);
  for (let i = 0; i < transcriptions.length; i++) {
    console.log(
      `Deleting transcription: ${transcriptions[i].id} (${i + 1}/${transcriptions.length})`,
    );
    await deleteTranscription(transcriptions[i].id);
  }
}

// Convert tokens into a readable transcript.
function renderTokens(finalTokens) {
  const textParts = [];
  let currentSpeaker = null;
  let currentLanguage = null;

  // Process all tokens in order.
  for (const token of finalTokens) {
    let { text, speaker, language } = token;
    const isTranslation = token.translation_status === "translation";

    // Speaker changed -> add a speaker tag.
    if (speaker !== undefined && speaker !== currentSpeaker) {
      if (currentSpeaker !== null) textParts.push("\n\n");
      currentSpeaker = speaker;
      currentLanguage = null; // Reset language on speaker changes.
      textParts.push(`Speaker ${currentSpeaker}:`);
    }

    // Language changed -> add a language or translation tag.
    if (language !== undefined && language !== currentLanguage) {
      currentLanguage = language;
      const prefix = isTranslation ? "[Translation] " : "";
      textParts.push(`\n${prefix}[${currentLanguage}] `);
      text = text.trimStart();
    }

    textParts.push(text);
  }
  return textParts.join("");
}

async function transcribeFile(audioUrl, audioPath, translation) {
  let fileId = null;

  if (!audioUrl && !audioPath) {
    throw new Error(
      "Missing audio: audio_url or audio_path must be specified.",
    );
  }
  if (audioPath) {
    fileId = await uploadAudio(audioPath);
  }

  const config = getConfig(audioUrl, fileId, translation);
  const transcriptionId = await createTranscription(config);
  await waitUntilCompleted(transcriptionId);

  const result = await getTranscription(transcriptionId);
  const text = renderTokens(result.tokens);
  console.log(text);

  await deleteTranscription(transcriptionId);
  if (fileId) await deleteFile(fileId);
}

async function main() {
  const { values: argv } = parseArgs({
    options: {
      audio_url: {
        type: "string",
        description: "Public URL of the audio file to transcribe",
      },
      audio_path: {
        type: "string",
        description: "Path to a local audio file to transcribe",
      },
      delete_all_files: {
        type: "boolean",
        description: "Delete all uploaded files",
      },
      delete_all_transcriptions: {
        type: "boolean",
        description: "Delete all transcriptions",
      },
      translation: { type: "string", default: "none" },
    },
  });

  if (argv.delete_all_files) {
    await deleteAllFiles();
    return;
  }

  if (argv.delete_all_transcriptions) {
    await deleteAllTranscriptions();
    return;
  }

  await transcribeFile(argv.audio_url, argv.audio_path, argv.translation);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
