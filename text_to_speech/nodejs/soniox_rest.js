import fs from "fs";
import path from "path";
import { Readable } from "stream";
import { pipeline } from "stream/promises";
import { parseArgs } from "node:util";
import process from "process";

const SONIOX_TTS_URL = "https://tts-rt.soniox.com/tts";
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

const DEFAULT_TEXT =
  "Soniox Text-to-Speech turns written text into natural, expressive audio " +
  "with high accuracy. It is designed for conversational agents, narration, " +
  "and accessible experiences, with low latency and high-quality voices.";

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
  const base = outputPath || "tts-rest";
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
  language,
  voice,
  audioFormat,
  text,
  sampleRate,
  bitrate,
}) {
  const config = {
    // Select the model to use.
    // See: soniox.com/docs/tts/models
    model: MODEL,

    // Set the language of the input text.
    // See: soniox.com/docs/tts/concepts/supported-languages
    language,

    // Select the voice to use.
    // See: soniox.com/docs/tts/concepts/voices
    voice,

    // Audio format.
    // See: soniox.com/docs/tts/concepts/audio-formats
    audio_format: audioFormat,

    // Input text.
    text,
  };

  if (sampleRate !== undefined) config.sample_rate = sampleRate;
  if (bitrate !== undefined) config.bitrate = bitrate;

  return config;
}

async function generateSpeech({ apiKey, config, outputPath, sampleRate }) {
  console.log("Connecting to Soniox...");

  const res = await fetch(SONIOX_TTS_URL, {
    method: "POST",
    headers: {
      // Soniox REST TTS uses Bearer auth.
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(config),
  });

  if (!res.ok) {
    let err;
    try {
      err = await res.json();
    } catch {
      err = { error_message: await res.text() };
    }
    throw new Error(
      `TTS request failed (status=${res.status}, ` +
        `error_code=${err.error_code}, error_message=${err.error_message})`,
    );
  }

  if (!res.body) {
    throw new Error("Empty response body.");
  }

  const wrapInWav =
    config.audio_format === "pcm_s16le" &&
    path.extname(outputPath).toLowerCase() === ".wav";

  if (wrapInWav) {
    // Buffer the full PCM response, then write a WAV file with a correct
    // data-chunk size so the output plays in every media player.
    const pcm = Buffer.from(await res.arrayBuffer());
    const wav = pcmS16leToWav(pcm, { sampleRate });
    fs.writeFileSync(outputPath, wav);
    console.log(`Wrote ${wav.length} bytes to ${path.resolve(outputPath)}`);
  } else {
    // Stream the audio response directly to the output file.
    const fileStream = fs.createWriteStream(outputPath);
    await pipeline(Readable.fromWeb(res.body), fileStream);
    const { size } = fs.statSync(outputPath);
    console.log(`Wrote ${size} bytes to ${path.resolve(outputPath)}`);
  }
}

async function main() {
  const { values: argv } = parseArgs({
    options: {
      text: { type: "string", default: DEFAULT_TEXT },
      language: { type: "string", default: "en" },
      voice: { type: "string", default: "Adrian" },
      audio_format: { type: "string", default: "pcm_s16le" },
      sample_rate: { type: "string" },
      bitrate: { type: "string" },
      output_path: { type: "string", default: "tts-rest" },
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

  const outputPath = resolveOutputPath(argv.output_path, argv.audio_format);
  const config = getConfig({
    language: argv.language,
    voice: argv.voice,
    audioFormat: argv.audio_format,
    text: argv.text,
    sampleRate,
    bitrate,
  });

  await generateSpeech({ apiKey, config, outputPath, sampleRate });
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
