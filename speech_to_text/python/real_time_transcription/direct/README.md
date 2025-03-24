# Node.js direct stream example

This example demonstrates how to set up a FastAPI server to serve a HTML page that loads Soniox Web Library, authenticates using **GET temporary API key** endpoint and starts a real-time transcription from browser client **directly** to Soniox STT Real-time API.

This approach minimizes the latency.

### Run FastAPI server

Open new terminal window:

1. Create environment file: `cp .env.example .env` and add your Soniox API key.
2. Create python environment: `python3 -m venv .venv`
3. Load python environment: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start server: `python server.py`
