import { RealtimeError, SonioxNodeClient } from "@soniox/node";
import fs from "fs";
import path from "path";
import { parseArgs } from "node:util";
import process from "process";

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

// Initialize the client.
// The API key is read from the SONIOX_API_KEY environment variable.
const client = new SonioxNodeClient();

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
  const base = outputPath || "tts_realtime";
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

// Build a realtime TTS stream config.
function getStreamConfig({
  model,
  language,
  voice,
  audioFormat,
  sampleRate,
  bitrate,
  streamId,
}) {
  const config = {
    // Client-defined stream id (auto-generated if omitted).
    ...(streamId && { stream_id: streamId }),

    // Select the model to use.
    // See: soniox.com/docs/tts/models
    model,

    // Set the language of the input text.
    // See: soniox.com/docs/tts/concepts/supported-languages
    language,

    // Select the voice to use.
    // See: soniox.com/docs/tts/concepts/voices
    voice,

    // Set output audio format and optional encoding parameters.
    // See: soniox.com/docs/api-reference/tts/generate_tts
    audio_format: audioFormat,
  };

  if (sampleRate !== undefined) config.sample_rate = sampleRate;
  if (bitrate !== undefined) config.bitrate = bitrate;

  return config;
}

async function runSession({
  lines,
  model,
  language,
  voice,
  audioFormat,
  sampleRate,
  bitrate,
  streamId,
  outputPath,
}) {
  const sanitizedLines = lines
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
  if (sanitizedLines.length === 0) {
    throw new Error("Text is empty after parsing.");
  }

  const destination = resolveOutputPath(outputPath, audioFormat);
  const config = getStreamConfig({
    model,
    language,
    voice,
    audioFormat,
    sampleRate,
    bitrate,
    streamId,
  });

  console.log("Connecting to Soniox...");
  const stream = await client.realtime.tts(config);
  console.log("Session started.");

  // Send text chunks in the background while receiving audio.
  let sendError = null;
  const sendPromise = (async () => {
    try {
      for (const line of sanitizedLines) {
        stream.sendText(line);
        // Sleep for 100 ms to simulate real-time streaming.
        await new Promise((res) => setTimeout(res, 100));
      }
      stream.finish();
    } catch (err) {
      sendError = err;
    }
  })();

  // Collect streamed audio chunks.
  const audioChunks = [];
  try {
    for await (const chunk of stream) {
      audioChunks.push(chunk);
    }
  } finally {
    await sendPromise;
    stream.close();
  }

  if (sendError) {
    throw new Error(`Failed to send realtime text: ${sendError.message}`);
  }

  console.log("Session finished.");

  const audio = Buffer.concat(audioChunks.map((c) => Buffer.from(c)));
  if (audio.length > 0) {
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
}

async function main() {
  const { values: argv } = parseArgs({
    options: {
      line: { type: "string", multiple: true },
      model: { type: "string", default: "tts-rt-v1" },
      language: { type: "string", default: "en" },
      voice: { type: "string", default: "Adrian" },
      audio_format: { type: "string", default: "pcm_s16le" },
      sample_rate: { type: "string" },
      bitrate: { type: "string" },
      stream_id: { type: "string" },
      output_path: { type: "string" },
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

  try {
    await runSession({
      lines: argv.line && argv.line.length > 0 ? argv.line : DEFAULT_LINES,
      model: argv.model,
      language: argv.language,
      voice: argv.voice,
      audioFormat: argv.audio_format,
      sampleRate,
      bitrate,
      streamId: argv.stream_id,
      outputPath: argv.output_path,
    });
  } catch (err) {
    if (err instanceof RealtimeError) {
      console.error("Soniox realtime error:", err.message);
    } else {
      throw err;
    }
  }
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
