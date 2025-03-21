# Node.js proxy example

This example demonstrates how to set up a Node.js server as a WebSocket proxy to stream microphone audio from a browser frontend to the Soniox Real-time API.

### Run backend Node.js server

Open new terminal window:

1. Navigate to backend folder: `cd backend`
2. Create environment file: `cp .env.example .env` and add your Soniox API key.
3. Install dependencies: `npm install`
4. Start server: `npm run start`

### Run frontend

Open new terminal window:

1. Navigate to frontend folder: `cd frontend`
2. Start a simple server to serve the HTML file: `npx serve`
3. Open browser and click start button, confirm microphone audio permissions and start talking.
