# Node.js proxy stream example

This example demonstrates how to set up a Node.js server as a WebSocket proxy
to stream microphone audio from a browser client to the Soniox Speech-to-Text Real-time API.

### Run Node.js server

Open new terminal window:

1. Navigate to server folder: `cd server`
2. Create environment file: `cp .env.example .env` and add your Soniox API key.
3. Install dependencies: `npm install`
4. Start server: `npm run start`

### Run client

Open new terminal window:

1. Navigate to client folder: `cd client`
2. Start a HTTP server to serve the HTML file: `npx serve` (or use a HTTP server of your choice to serve it)
3. Open client in browser and click start button, confirm microphone audio permissions and start talking.
