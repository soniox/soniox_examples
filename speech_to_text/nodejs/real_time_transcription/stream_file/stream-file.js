import { createReadStream } from "fs"

const WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket"
const FILE_TO_STREAM = "coffee_shop.pcm_s16le"

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
const API_KEY = process.env.SONIOX_API_KEY;

// Connect to WebSocket API
const ws = new WebSocket(WEBSOCKET_URL);

console.log("Opening WebSocket connection...")
ws.addEventListener("open", async () => {
  // Send start request
  ws.send(
    JSON.stringify({
      api_key: API_KEY,
      audio_format: "pcm_s16le",
      sample_rate: 16000,
      num_channels: 1,
      model: "stt-rt-preview"
    }),
  );

  // Read and send audio data from file over WebSocket connection
  const audioStream = createReadStream(FILE_TO_STREAM, {
    highWaterMark: 3840,
  });

  console.log("Transcription started.")
  for await (const chunk of audioStream) {
    ws.send(chunk);
    await new Promise((resolve) => setTimeout(resolve, 120));
  }

  // Signal end of file
  ws.send("");
});

ws.addEventListener("message", (event) => {
  // Receive and process messages
  const res = JSON.parse(event.data);

  if (res.error_code) {
    console.log(`\nError: ${res.error_code} ${res.error_message}`);
    process.exit(1);
  }

  for (const token of res.tokens) {
    if (token.text) {
      process.stdout.write(token.text);
    }
  }

  if (res.finished) {
    console.log("\nTranscription done.");
  }
});

ws.addEventListener("close", () => {});

ws.addEventListener("error", (error) => {
  // handle WebSocket connection errors
  console.error(error.error);
});
