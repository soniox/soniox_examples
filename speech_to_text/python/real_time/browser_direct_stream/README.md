# Browser direct stream example

This example demonstrates how to set up a Python FastAPI server to serve an HTML page
that loads Soniox Web Library, authenticates using **GET temporary API key**
endpoint and starts a real-time transcription from browser client **directly**
to Soniox STT WebSocket API.

This approach minimizes the latency.

### Run Python server

Copy `.env.example` to `.env` and add your Soniox API key.

Create Python virtual environment and activate it:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```sh
pip install -r requirements.txt
```

Start the server:

```sh
python server.py
```
