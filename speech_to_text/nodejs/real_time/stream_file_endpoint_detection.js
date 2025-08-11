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
      model: "stt-rt-preview-v2",
      language_hints: ["en", "es"],
      enable_non_final_tokens: false,
      enable_endpoint_detection: true,
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

let currentText = "";

ws.addEventListener("message", (event) => {
  // Receive and process messages
  const res = JSON.parse(event.data);

  if (res.error_code) {
    console.log(`\nError: ${res.error_code} ${res.error_message}`);
    process.exit(1);
  }

  for (const token of res.tokens || []) {
    if (token.text) {
      if (token.text == "<end>") {
        console.log(currentText);
        currentText = "";
      } else if (!currentText) {
        currentText += token.text.trimStart();
      } else {
        currentText += token.text;
      }
    }
  }

  if (res.finished) {
    if (currentText) {
      console.log(currentText);
    }
    console.log("\nTranscription done.");
  }
});

ws.addEventListener("close", () => {});

ws.addEventListener("error", (error) => {
  console.error("Connection error occurred:", error);
});
