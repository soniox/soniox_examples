import fetch from "node-fetch";

// Retrieve the API key from environment variable (ensure SONIOX_API_KEY is set)
const apiKey = process.env.SONIOX_API_KEY;
const websocketUrl = "wss://stt-rt.soniox.com/transcribe-websocket";
const audioUrl = "https://npr-ice.streamguys1.com/live.mp3?ck=1742897559135";

// Connect to WebSocket API
const ws = new WebSocket(websocketUrl);

console.log("Opening WebSocket connection...");
ws.addEventListener("open", async () => {
  // Send start request
  ws.send(
    JSON.stringify({
      api_key: apiKey,
      audio_format: "auto", // server detects the format
      model: "stt-rt-preview-v2",
      language_hints: ["en", "es"],
    })
  );

  console.log("Transcription started.");

  try {
    // Connect to the radio stream
    const res = await fetch(audioUrl);
    if (!res.ok) {
      throw new Error(`HTTP error! Status: ${res.status}`);
    }
    res.body.on("data", (chunk) => {
      ws.send(chunk);
    });
    res.body.on("end", () => {
      console.log("Stream ended");
      ws.send(""); // signal end of stream
    });
    res.body.on("error", (error) => {
      console.error("Stream error:", error);
      ws.close();
    });
  } catch (error) {
    console.error("Error sending audio:", error);
    ws.close();
  }
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
