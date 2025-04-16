import { createReadStream } from "fs";

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
const apiKey = process.env.SONIOX_API_KEY;
const websocketUrl = "wss://stt-rt.soniox.com/transcribe-websocket";
const fileToTranscribe = "coffee_shop.pcm_s16le";

// Connect to WebSocket API
const ws = new WebSocket(websocketUrl);

console.log("Opening WebSocket connection...");
ws.addEventListener("open", async () => {
  // Send start request
  ws.send(
    JSON.stringify({
      api_key: apiKey,
      audio_format: "pcm_s16le",
      sample_rate: 16000,
      num_channels: 1,
      model: "stt-rt-preview",
      language_hints: ["en", "es"],
    })
  );

  // Read and send audio data from file over WebSocket connection
  const audioStream = createReadStream(fileToTranscribe, {
    highWaterMark: 3840,
  });

  console.log("Transcription started.");

  for await (const chunk of audioStream) {
    ws.send(chunk);
    await new Promise((resolve) => setTimeout(resolve, 120));
  }

  // Signal end of file
  ws.send("");
});

let finalText = "";

ws.addEventListener("message", (event) => {
  // Receive and process messages
  const res = JSON.parse(event.data);

  if (res.error_code) {
    console.log(`\nError: ${res.error_code} ${res.error_message}`);
    process.exit(1);
  }

  let nonFinalText = "";

  for (const token of res.tokens || []) {
    if (token.text) {
      if (token.is_final) {
        finalText += token.text;
      } else {
        nonFinalText += token.text;
      }
    }
  }

  console.log(
    "\x1b[2J\x1b[H" + // clear the screen, move to top-left corner
      finalText + // write final text
      "\x1b[34m" + // change text color to blue
      nonFinalText + // write non-final text
      "\x1b[39m" // reset text color
  );

  if (res.finished) {
    console.log("\nTranscription done.");
  }
});

ws.addEventListener("close", () => {});

ws.addEventListener("error", (error) => {
  console.error("Connection error occurred:", error);
});
