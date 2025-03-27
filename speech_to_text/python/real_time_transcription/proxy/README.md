# Node.js proxy stream example

This example demonstrates how to set up a Python server as a WebSocket proxy
to stream microphone audio from a HTML client to the Soniox Speech-to-Text Real-time API.

### Run Node.js server

Open new terminal window:

1. Navigate to server folder: `cd server`
2. Create Python env: `python -m venv .venv` and activate it `source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Start server: `python server.py`

### Run client

Open new terminal window:

1. Navigate to client folder: `cd client`
2. Start a HTTP server to serve the HTML file: `npx serve` (or use a HTTP server of your choice to serve it)
3. Open client in browser and click start button, confirm microphone audio permissions and start talking.
