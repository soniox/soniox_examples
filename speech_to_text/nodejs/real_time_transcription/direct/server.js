require('dotenv').config()

const http = require('http');
const express = require('express');
const fetch = require('node-fetch');
const app = express();

async function getTemporaryApiKey() {
  // get temporary API key to avoid exposing SONIOX_API_KEY on client side
  const response = await fetch('https://api.soniox.com/v1/auth/temporary-api-key', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.SONIOX_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      usage_type: "transcribe_websocket",
      expires_in_seconds: 300 // 5 minutes, adjust to fit your needs
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to get API key. Status: ${response.status}, Response: ${await response.text()}`);
  }

  return await response.json();
}

app.get('/', async (req, res) => {
  try {
    const temporaryApiKeyData = await getTemporaryApiKey();

    // return a HTML template that imports Soniox STT Web Library and includes a temporary API key
    res.send(`
    <!DOCTYPE html>
    <html>
    <body>
      <h1>Direct stream demo</h1>
      <button id="trigger">Start</button>
      <hr />
      <div id="transcript"></div>
      <script type="module">
        // import Soniox STT Web Library
        import { RecordTranscribe } from "https://unpkg.com/@soniox/speech-to-text-web?module";

        const transcript = document.getElementById("transcript");
        const trigger = document.getElementById("trigger");



        // create new instance of RecordTranscribe class and authenticate with temp API key
        const recordTranscribe = new RecordTranscribe({
          apiKey: "${temporaryApiKeyData.api_key}a",
        });
        let recordTranscribeState = "stopped"; // "stopped" | "starting" | "running" | "stopping"

        trigger.onclick = () => {
          // start transcription only when library is in stopped status (means everything is ready)
          debugger;
          if (recordTranscribeState === "stopped") {
            transcript.textContent = "";
            trigger.textContent = "Starting...";
            recordTranscribeState = "starting";

            // start transcribing and bind callbacks
            recordTranscribe.start({
              model: "stt-rt-preview",

              onStarted: () => {
                // library connected to Soniox STT Real-time API and is transcribing
                recordTranscribeState = "running";
                trigger.textContent = "Stop";
              },
              onPartialResult: (result) => {
                // transcription results are returned, we output them
                transcript.textContent += result.text;
              },
              onFinished: () => {
                // transcription finished, we go back to initial recordTranscribeState
                trigger.textContent = "Start";
                recordTranscribeState = "stopped";
              },
              onError: (status, message) => {
                console.log("Error occurred", status, message);
                trigger.textContent = "Start";
                transcript.textContent += message;
                recordTranscribeState = "stopped";
              },
            });
          } else if (recordTranscribeState === "running") {
            // stop transcribing and wait for final result and connections to close
            trigger.textContent = "Stopping...";
            recordTranscribeState = "stopping";
            recordTranscribe.stop();
          }
        };
      </script>
    </body>
    </html>
    `);
  } catch (error) {
      console.error("Error getting Soniox API key:", error);
      res.status(500).send(`
        <!DOCTYPE html>
        <html>
        <body>
          <p>Authentication error</p>
          <p>There was an error retrieving the Soniox Temporary API key.</p>
          <p>Error details: ${error.message}</p>
        </body>
        </html>
      `);
    }
});

// Create HTTP server with Express
const server = http.createServer(app);

server.listen(process.env.PORT, () => {
  console.log(`WebSocket proxy server listening on port ${process.env.PORT}`);
});
