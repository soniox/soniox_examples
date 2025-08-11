import { createReadStream } from "fs";

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
const apiKey = process.env.SONIOX_API_KEY;
const websocketUrl = "wss://stt-rt.soniox.com/transcribe-websocket";
const fileToTranscribe = "two_way_translation.pcm_s16le";

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
      enable_speaker_diarization: true,
      translation: {
        type: "two_way",
        language_a: "en",
        language_b: "es",
      },
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

function renderTokens(finalTokens, nonFinalTokens) {
  // Render the tokens in the terminal using ANSI escape codes.
  let text = "";
  text += "\x1b[2J\x1b[H"; // Clear the screen and move to the top-left corner
  let isFinal = true;
  let speaker = "";
  let language = "";
  for (const token of finalTokens.concat(nonFinalTokens)) {
    let tokenText = token.text;
    if (!token.is_final && isFinal) {
      text += "\x1b[34m"; // change text color to blue
      isFinal = false;
    }
    if (token.speaker && token.speaker !== speaker) {
      if (speaker) {
        text += "\n\n";
      }
      speaker = token.speaker;
      text += `Speaker ${speaker}: `;
      tokenText = tokenText.trimStart();
      language = "";
    }
    if (token.language && token.language != language) {
      text += "\n";
      language = token.language;
      text += `[${language}] `;
      tokenText = tokenText.trimStart();
    }
    text += tokenText;
  }
  text += "\x1b[39m"; // reset text color
  console.log(text);
}

let finalTokens = [];

ws.addEventListener("message", (event) => {
  // Receive and process messages
  const res = JSON.parse(event.data);

  if (res.error_code) {
    console.log(`\nError: ${res.error_code} ${res.error_message}`);
    process.exit(1);
  }

  let nonFinalTokens = [];

  for (const token of res.tokens || []) {
    if (token.text) {
      if (token.is_final) {
        finalTokens.push(token);
      } else {
        nonFinalTokens.push(token);
      }
    }
  }

  renderTokens(finalTokens, nonFinalTokens);

  if (res.finished) {
    console.log("\nTranscription done.");
  }
});

ws.addEventListener("close", () => {});

ws.addEventListener("error", (error) => {
  console.error("Connection error occurred:", error);
});
