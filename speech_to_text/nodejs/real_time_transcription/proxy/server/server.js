require('dotenv').config()

const WebSocket = require('ws');
const http = require('http');

const server = http.createServer();
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
  console.log('Browser client connected');

  // create a message queue to store client messages received before
  // Soniox Real-time API connection is ready, so we don't loose any
  const messageQueue = [];

  let sonioxWs = null;
  let sonioxWsReady = false;

  function initSonioxConnection() {
    sonioxWs = new WebSocket('wss://stt-rt.soniox.com/transcribe-websocket');

    sonioxWs.on('open', () => {
      console.log('Connected to Soniox STT Real-time API');

      // send initial configuration message
      const startMessage = JSON.stringify({
        api_key: process.env.SONIOX_API_KEY,
        audio_format: "auto",
        model: "stt-rt-preview"
      });
      sonioxWs.send(startMessage);
      console.log('Sent start message to Soniox');

      // mark connection as ready
      sonioxWsReady = true;

      // process any queued messages
      while (messageQueue.length > 0 && sonioxWsReady) {
        const data = messageQueue.shift();
        forwardData(data);
      }
    });

    // receive messages from Soniox STT Real-time API
    sonioxWs.on('message', (data) => {
      // note:
      // at this point we could manipulate and enhance the transcribed data
      try {
        ws.send(data.toString());
      } catch (err) {
        console.error("Error forwarding Soniox response:", err);
      }
    });

    sonioxWs.on('error', (error) => {
      console.log('Soniox WebSocket error:', error);
      sonioxWsReady = false;
    });

    sonioxWs.on('close', (code, reason) => {
      console.log('Soniox WebSocket closed:', code, reason);
      sonioxWsReady = false;
    });
  }

  // forward message data to Soniox STT Real-time API
  function forwardData(data) {
    try {
      sonioxWs.send(data);
    } catch (err) {
      console.error("Error forwarding data to Soniox:", err);
    }
  }

  // initialize Soniox connection
  initSonioxConnection();

  // receive messages from browser client
  ws.on('message', (data) => {
    if (sonioxWsReady) {
      // forward messages instantly
      forwardData(data);
    } else {
      // queue the message to be processed
      // as soon as connection to Soniox STT Real-time API is ready
      messageQueue.push(data);
    }
  });

  ws.on('close', () => {
    console.log('Browser client disconnected');
    if (sonioxWs) {
      try {
        sonioxWs.close();
      } catch (err) {
        console.error("Error closing Soniox connection:", err);
      }
    }
  });
});

server.listen(process.env.PORT, () => {
  console.log(`WebSocket proxy server listening on port ${process.env.PORT}`);
});
