import fs from "fs";
import path from "path";
import WebSocket from "ws";
import { parseArgs } from "node:util";
import process from "process";

const SONIOX_TTS_WEBSOCKET_URL = "wss://tts-rt.soniox.com/tts-websocket";
const MODEL = "tts-rt-v1";
const VALID_SAMPLE_RATES = [8000, 16000, 24000, 44100, 48000];
const VALID_BITRATES = [32000, 64000, 96000, 128000, 192000, 256000, 320000];
const VALID_AUDIO_FORMATS = [
  "pcm_f32le",
  "pcm_s16le",
  "pcm_mulaw",
  "pcm_alaw",
  "wav",
  "aac",
  "mp3",
  "opus",
  "flac",
];
const RAW_PCM_FORMATS = ["pcm_s16le", "pcm_f32le", "pcm_mulaw", "pcm_alaw"];

const DEFAULT_LINES = [
  "Welcome to Soniox real-time Text-to-Speech. ",
  "As text is streamed in, audio streams back in parallel with high accuracy, ",
  "so your application can start playing speech ",
  "within milliseconds of the first word.",
];

// Resolve a concrete output file path.
// If the provided path has no extension, derive one from audio_format:
//   * pcm_s16le  -> .wav  (we wrap the bytes in a WAV container below)
//   * other pcm_* -> .pcm (raw, no container)
//   * anything else -> the format name (e.g. .flac, .mp3, .opus)
function resolveOutputPath(outputPath, audioFormat) {
  if (outputPath && path.extname(outputPath)) {
    return outputPath;
  }
  const ext =
    audioFormat === "pcm_s16le"
      ? "wav"
      : RAW_PCM_FORMATS.includes(audioFormat)
        ? "pcm"
        : audioFormat;
  const base = outputPath || "tts-ws";
  return `${base}.${ext}`;
}

function pcmS16leToWav(pcm, { sampleRate, numChannels = 1 }) {
  const bitsPerSample = 16;
  const byteRate = sampleRate * numChannels * (bitsPerSample / 8);
  const blockAlign = numChannels * (bitsPerSample / 8);
  const dataSize = pcm.byteLength;
  const header = Buffer.alloc(44);
  header.write("RIFF", 0, "ascii");
  header.writeUInt32LE(36 + dataSize, 4);
  header.write("WAVE", 8, "ascii");
  header.write("fmt ", 12, "ascii");
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(numChannels, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(byteRate, 28);
  header.writeUInt16LE(blockAlign, 32);
  header.writeUInt16LE(bitsPerSample, 34);
  header.write("data", 36, "ascii");
  header.writeUInt32LE(dataSize, 40);
  return Buffer.concat([header, Buffer.from(pcm)]);
}

// Get Soniox TTS config.
function getConfig({
  apiKey,
  streamId,
  language,
  voice,
  audioFormat,
  sampleRate,
  bitrate,
}) {
  const config = {
    // Get your API key at console.soniox.com, then run: export SONIOX_API_KEY=<YOUR_API_KEY>
    api_key: apiKey,

    // Client-defined stream id to identify this realtime request.
    stream_id: streamId,

    // Select the model to use.
    // See: soniox.com/docs/tts/models
    model: MODEL,

    // Set the language of the input text.
    // See: soniox.com/docs/tts/languages
    language,

    // Select the voice to use.
    // See: soniox.com/docs/tts/voices
    voice,

    // Audio format.
    // See: soniox.com/docs/tts/audio-formats
    audio_format: audioFormat,
  };

  if (sampleRate !== undefined) config.sample_rate = sampleRate;
  if (bitrate !== undefined) config.bitrate = bitrate;

  return config;
}

function getTextRequest(text, streamId, textEnd) {
  return {
    text,
    text_end: textEnd,
    stream_id: streamId,
  };
}

// Stream text lines to the websocket.
async function streamText(lines, streamId, ws) {
  for (const line of lines) {
    const cleanLine = line.trim();
    if (!cleanLine) continue;
    ws.send(JSON.stringify(getTextRequest(cleanLine, streamId, false)));
    // Sleep for 100 ms to simulate real-time streaming.
    await new Promise((res) => setTimeout(res, 100));
  }

  // Send text_end=true after the last chunk.
  ws.send(JSON.stringify(getTextRequest("", streamId, true)));
}

function runSession({
  apiKey,
  lines,
  language,
  voice,
  audioFormat,
  sampleRate,
  bitrate,
  streamId,
  outputPath,
}) {
  return new Promise((resolve, reject) => {
    console.log("Connecting to Soniox...");
    const ws = new WebSocket(SONIOX_TTS_WEBSOCKET_URL);

    const audioChunks = [];

    const finalize = (err) => {
      const destination = resolveOutputPath(outputPath, audioFormat);
      if (audioChunks.length > 0) {
        const audio = Buffer.concat(audioChunks);
        // Wrap raw pcm_s16le in a WAV container so the .wav file plays everywhere.
        const bytes =
          audioFormat === "pcm_s16le" &&
          path.extname(destination).toLowerCase() === ".wav"
            ? pcmS16leToWav(audio, { sampleRate })
            : audio;
        fs.writeFileSync(destination, bytes);
        console.log(`Wrote ${bytes.length} bytes to ${path.resolve(destination)}`);
      } else {
        console.log("No audio file was written.");
      }
      if (err) reject(err);
      else resolve();
    };

    ws.on("open", () => {
      const config = getConfig({
        apiKey,
        streamId,
        language,
        voice,
        audioFormat,
        sampleRate,
        bitrate,
      });

      // Send first request with config.
      ws.send(JSON.stringify(config));

      // Start streaming text in the background.
      streamText(lines, streamId, ws).catch((err) => {
        console.error("Text stream error:", err);
      });
      console.log("Session started.");
    });

    ws.on("message", (msg) => {
      let res;
      try {
        res = JSON.parse(msg.toString());
      } catch {
        return;
      }

      // Error from server.
      // See: https://soniox.com/docs/tts/api-reference/websocket-api#error-response
      if (res.error_code) {
        console.error(`Error: ${res.error_code} - ${res.error_message}`);
        ws.close();
        return;
      }

      // Collect audio bytes from base64-encoded chunks.
      if (res.audio) {
        audioChunks.push(Buffer.from(res.audio, "base64"));
      }

      // Session finished.
      if (res.terminated) {
        console.log("Session finished.");
        ws.close();
      }
    });

    ws.on("close", () => {
      finalize(null);
    });

    ws.on("error", (err) => {
      console.error("WebSocket error:", err.message);
      finalize(err);
    });
  });
}

async function main() {
  const { values: argv } = parseArgs({
    options: {
      line: { type: "string", multiple: true },
      language: { type: "string", default: "en" },
      voice: { type: "string", default: "Adrian" },
      audio_format: { type: "string", default: "pcm_s16le" },
      stream_id: { type: "string", default: "stream-1" },
      output_path: { type: "string", default: "tts-ws" },
      sample_rate: { type: "string" },
      bitrate: { type: "string" },
    },
  });

  if (!VALID_AUDIO_FORMATS.includes(argv.audio_format)) {
    throw new Error(
      `audio_format must be one of ${VALID_AUDIO_FORMATS.join(", ")}`,
    );
  }
  let sampleRate =
    argv.sample_rate !== undefined ? Number(argv.sample_rate) : undefined;
  if (sampleRate === undefined && RAW_PCM_FORMATS.includes(argv.audio_format)) {
    sampleRate = 24000;
  }
  if (sampleRate !== undefined && !VALID_SAMPLE_RATES.includes(sampleRate)) {
    throw new Error(
      `sample_rate must be one of ${VALID_SAMPLE_RATES.join(", ")}`,
    );
  }
  const bitrate = argv.bitrate !== undefined ? Number(argv.bitrate) : undefined;
  if (bitrate !== undefined && !VALID_BITRATES.includes(bitrate)) {
    throw new Error(`bitrate must be one of ${VALID_BITRATES.join(", ")}`);
  }

  const apiKey = process.env.SONIOX_API_KEY;
  if (!apiKey) {
    throw new Error(
      "Missing SONIOX_API_KEY.\n" +
        "1. Get your API key at https://console.soniox.com\n" +
        "2. Run: export SONIOX_API_KEY=<YOUR_API_KEY>",
    );
  }

  await runSession({
    apiKey,
    lines: argv.line && argv.line.length > 0 ? argv.line : DEFAULT_LINES,
    language: argv.language,
    voice: argv.voice,
    audioFormat: argv.audio_format,
    sampleRate,
    bitrate,
    streamId: argv.stream_id,
    outputPath: argv.output_path,
  });
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
