import fs from "fs";
import WebSocket from "ws";
import { parseArgs } from "node:util";

const SONIOX_WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket";

// Get Soniox STT config
function getConfig(apiKey, audioFormat, translation) {
  const config = {
    // Get your API key at console.soniox.com, then run: export SONIOX_API_KEY=<YOUR_API_KEY>
    api_key: apiKey,

    // Select the model to use.
    // See: soniox.com/docs/stt/models
    model: "stt-rt-v3",

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

    // Use endpointing to detect when the speaker stops.
    // It finalizes all non-final tokens right away, minimizing latency.
    // See: soniox.com/docs/stt/rt/endpoint-detection
    enable_endpoint_detection: true,
  };

  // Audio format.
  // See: soniox.com/docs/stt/rt/real-time-transcription#audio-formats
  if (audioFormat === "auto") {
    // Set to "auto" to let Soniox detect the audio format automatically.
    config.audio_format = "auto";
  } else if (audioFormat === "pcm_s16le") {
    // Example of a raw audio format; Soniox supports many others as well.
    config.audio_format = "pcm_s16le";
    config.sample_rate = 16000;
    config.num_channels = 1;
  } else {
    throw new Error(`Unsupported audio_format: ${audioFormat}`);
  }

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

// Read the audio file and send its bytes to the websocket.
async function streamAudio(audioPath, ws) {
  const stream = fs.createReadStream(audioPath, { highWaterMark: 3840 });

  for await (const chunk of stream) {
    ws.send(chunk);
    // Sleep for 120 ms to simulate real-time streaming.
    await new Promise((res) => setTimeout(res, 120));
  }

  // Empty string signals end-of-audio to the server
  ws.send("");
}

// Convert tokens into readable transcript
function renderTokens(finalTokens, nonFinalTokens) {
  let textParts = [];
  let currentSpeaker = null;
  let currentLanguage = null;

  const allTokens = [...finalTokens, ...nonFinalTokens];

  // Process all tokens in order.
  for (const token of allTokens) {
    let { text, speaker, language } = token;
    const isTranslation = token.translation_status === "translation";

    // Speaker changed -> add a speaker tag.
    if (speaker && speaker !== currentSpeaker) {
      if (currentSpeaker !== null) textParts.push("\n\n");
      currentSpeaker = speaker;
      currentLanguage = null; // Reset language on speaker changes.
      textParts.push(`Speaker ${currentSpeaker}:`);
    }

    // Language changed -> add a language or translation tag.
    if (language && language !== currentLanguage) {
      currentLanguage = language;
      const prefix = isTranslation ? "[Translation] " : "";
      textParts.push(`\n${prefix}[${currentLanguage}] `);
      text = text.trimStart();
    }

    textParts.push(text);
  }

  textParts.push("\n===============================");
  return textParts.join("");
}

function runSession(apiKey, audioPath, audioFormat, translation) {
  const config = getConfig(apiKey, audioFormat, translation);

  console.log("Connecting to Soniox...");
  const ws = new WebSocket(SONIOX_WEBSOCKET_URL);

  let finalTokens = [];

  ws.on("open", () => {
    // Send first request with config.
    ws.send(JSON.stringify(config));

    // Start streaming audio in the background.
    streamAudio(audioPath, ws).catch((err) =>
      console.error("Audio stream error:", err),
    );
    console.log("Session started.");
  });

  ws.on("message", (msg) => {
    const res = JSON.parse(msg.toString());

    // Error from server.
    // See: https://soniox.com/docs/stt/api-reference/websocket-api#error-response
    if (res.error_code) {
      console.error(`Error: ${res.error_code} - ${res.error_message}`);
      ws.close();
      return;
    }

    // Parse tokens from current response.
    let nonFinalTokens = [];
    if (res.tokens) {
      for (const token of res.tokens) {
        if (token.text) {
          if (token.is_final) {
            // Final tokens are returned once and should be appended to final_tokens.
            finalTokens.push(token);
          } else {
            // Non-final tokens update as more audio arrives; reset them on every response.
            nonFinalTokens.push(token);
          }
        }
      }
    }

    // Render tokens.
    const text = renderTokens(finalTokens, nonFinalTokens);
    console.log(text);

    // Session finished.
    if (res.finished) {
      console.log("Session finished.");
      ws.close();
    }
  });

  ws.on("error", (err) => console.error("WebSocket error:", err));
}

async function main() {
  const { values: argv } = parseArgs({
    options: {
      audio_path: { type: "string", required: true },
      audio_format: { type: "string", default: "auto" },
      translation: { type: "string", default: "none" },
    },
  });

  const apiKey = process.env.SONIOX_API_KEY;
  if (!apiKey) {
    throw new Error(
      "Missing SONIOX_API_KEY.\n" +
        "1. Get your API key at https://console.soniox.com\n" +
        "2. Run: export SONIOX_API_KEY=<YOUR_API_KEY>",
    );
  }

  runSession(apiKey, argv.audio_path, argv.audio_format, argv.translation);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
