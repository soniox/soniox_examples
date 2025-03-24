# Node.js direct stream example

This example demonstrates how to set up a Node.js server to serve a HTML page that loads Soniox Web Library, authenticates using **GET temporary API key** endpoint and starts a real-time transcription from browser client **directly** to Soniox STT Real-time API.

This approach minimizes the latency.

### Run Node.js server

Open new terminal window:

1. Create environment file: `cp .env.example .env` and add your Soniox API key.
2. Install dependencies: `npm install`
3. Start server: `npm run start`
