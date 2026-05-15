# Speech-to-speech translation

A small demo that plays speech from an audio file (or from your microphone), transcribes and translates it in real time, and (optionally) plays the translation back as speech. Built directly on the [Soniox](https://soniox.com) STT and TTS WebSocket APIs (no SDK), with FastAPI on the backend and vanilla HTML/JS on the frontend.

The point of the project is to show how to wire the two Soniox WebSocket APIs together at the protocol level - useful if you want to see what an SDK does for you under the hood, or if you need to build something the SDKs don't cover.

## Requirements

- Python (managed via [uv](https://github.com/astral-sh/uv))
- A Soniox API key

## Setup

Create a `.env` file in the project root with your API key (in the format of .env.example):

```
SONIOX_API_KEY=your_key_here
```

Install dependencies:

```
uv sync
```

## Running it

```
uv run uvicorn main:app --reload --port 8000
```

Then open <http://localhost:8000> in your browser. Pick a target language and voice, choose an input mode using the toggle next to the action button, and run it:

- **Microphone** - click *Start talking* and speak.
- **Audio file** - paste a URL to an audio file (mp3, wav, etc.) and click *Play audio file*. The backend pulls the file and streams it to STT at real-time pace; the browser plays the source audio so you can follow along and hear the translation ducked over it. You can also pre-fill the URL via `?audio=<url>` in the page query string.

The original transcript appears on the left, the translation on the right. If *Enable spoken translation* is checked the translated audio plays through your speakers; uncheck it for a text-only run.

## How it works

The backend opens one WebSocket to Soniox STT and (when spoken translation is enabled) one to Soniox TTS, and proxies between them and the browser.

```
Browser              Python backend              Soniox
   │                       │                        │
   ├─ WS /ws/translate ──▶ │                        │
   │  audio bytes ───────▶ │ forwards to STT ─────▶ │   (mic mode)
   │                       │ ─ HTTP GET audio_url ─ │ ◀ (file mode)
   │                       │ forwards to STT ─────▶ │
   │                       │  ◀── token JSON ────── │
   │  ◀── token JSON ──    │                        │
   │                       │ ─ WS tts-rt ─────────▶ │
   │                       │  text chunks ────────▶ │
   │                       │  ◀── audio (base64) ── │
   │  ◀── PCM binary ──    │  (decoded)             │
```

The browser is a thin client: capture mic with `MediaRecorder` (or play the source file locally for follow-along), send bytes, receive token JSON and PCM audio. All the Soniox protocol work lives in [server/main.py](server/main.py).

The `/ws/translate` endpoint takes query params for `target_lang`, `voice`, `lang_id`, `diarize`, `tts` (toggle spoken translation), and optionally `audio_url` + `audio_duration` to put it in file mode.

Per browser connection the backend runs a handful of concurrent coroutines:

- **Input** - one of:
  - **`pipe_browser_audio_to_stt`** (mic mode) forwards mic audio bytes from browser to STT.
  - **`stream_url_to_stt`** (file mode) fetches `audio_url` over HTTP and feeds STT at real-time pace using `audio_duration` to compute the byte rate, so STT sees the file as if it were being spoken live.
- **`handle_stt`** - reads STT results, forwards them to the browser for UI rendering, and pushes translation tokens into a queue for TTS.
- **`tts_sender`** *(only when TTS enabled)* - pulls tokens from the queue, opens a new TTS stream per utterance, sends text chunks, closes the stream on `<end>`.
- **`pipe_tts_to_browser`** *(only when TTS enabled)* - reads audio from TTS, base64-decodes it, forwards it to the browser. Emits a `session_done` message once tts_sender has drained the queue and the last TTS stream has terminated, so the browser knows it's safe to stop.
- **`tts_keepalive`** *(only when TTS enabled)* - sends a keepalive message every 20 seconds so idle TTS streams don't get killed.

One TTS stream per utterance, sequential. The TTS connection is pre-warmed: the backend opens a TTS stream with a config message as soon as the browser connects, so the first translation token can skip the config round-trip and start producing audio sooner.

## Files

```
server/main.py     FastAPI + Soniox WebSocket plumbing
web/index.html     UI shell
web/styles.css     Dark theme
web/app.js         Mic capture + WebSocket + Web Audio playback
pyproject.toml     Dependencies
```

## A note on latency

The first audio after you start speaking takes roughly 0.5–1.5 seconds to play. Most of that is the TTS model's first-byte time - it needs to see a few tokens before producing audio. The pre-warm shaves about 400ms off the median. The backend pipeline itself adds under 5ms.
