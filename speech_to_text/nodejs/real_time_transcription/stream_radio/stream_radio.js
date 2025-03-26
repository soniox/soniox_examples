import fetch from 'node-fetch';

const WEBSOCKET_URL = "wss://stt-rt.soniox.com/transcribe-websocket";
const RADIO_URL = "https://npr-ice.streamguys1.com/live.mp3?ck=1742897559135";

const API_KEY = process.env.SONIOX_API_KEY;
if (!API_KEY) {
  console.error("Missing SONIOX_API_KEY env variable. Please configure it.");
  process.exit(1);
}

// Connect to WebSocket API
const ws = new WebSocket(WEBSOCKET_URL);

console.log("Opening WebSocket connection...");
ws.addEventListener("open", async () => {
  // Send start request
  ws.send(
    JSON.stringify({
      api_key: API_KEY,
      audio_format: "auto", // let the API detect the format automatically
      model: "stt-rt-preview"
    })
  );

  console.log("Transcription started.");

  try {
    // Connect to the radio stream
    const response = await fetch(RADIO_URL);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    // Process the audio stream with callbacks
    const audioStream = response.body;

    audioStream.on('data', async (chunk) => {
      ws.send(chunk);
      await new Promise(resolve => setTimeout(resolve, 120));
    });

    audioStream.on('end', () => {
      console.log("Stream ended");
      // Signal end of file
      ws.send("");
    });

    audioStream.on('error', (error) => {
      console.error("Stream error:", error);
      ws.close();
    });

  } catch (error) {
    console.error("Error sending audio:", error);
    ws.close();
  }
});

ws.addEventListener("message", (event) => {
  // Receive and process messages
  const res = JSON.parse(event.data);

  if (res.error_code) {
    console.log(`\nError: ${res.error_code} ${res.error_message}`);
    process.exit(1);
  }

  for (const token of res.tokens || []) {
    if (token.text) {
      process.stdout.write(token.text);
    }
  }

  if (res.finished) {
    console.log("\nTranscription done.");
  }
});

ws.addEventListener("close", (event) => {
  console.log(`\nConnection closed with code ${event.code} and reason: ${event.reason}`);
});

ws.addEventListener("error", (error) => {
  console.error("WebSocket error:", error);
});
