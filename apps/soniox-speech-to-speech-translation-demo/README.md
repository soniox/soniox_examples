# Speech-to-speech translation

A small demo that plays speech from an audio file (or from your microphone), transcribes and translates it in real time, and (optionally) plays the translation back as speech. Built directly on the [Soniox](https://soniox.com) STT and TTS WebSocket APIs (no SDK), with FastAPI on the backend and vanilla HTML/JS on the frontend.

The point of the project is to show how to wire the two Soniox WebSocket APIs together at the protocol level - useful if you want to see what an SDK does for you under the hood, or if you need to build something the SDKs don't cover.

Speech-to-text always uses Soniox. The spoken translation (TTS) can be produced by either **Soniox** or **[60db](https://60db.ai)**, selected with the `TTS_PROVIDER` env var. Both backends live behind a common interface in [tts.py](tts.py) and emit the same raw 16-bit PCM at 24 kHz, so the rest of the app doesn't care which one is used.

## Requirements

- Python (managed via [uv](https://github.com/astral-sh/uv))
- A Soniox API key (for STT, and for TTS when `TTS_PROVIDER=soniox`)
- A 60db API key + voice id (for TTS when `TTS_PROVIDER=sixtydb`, the default)

## Setup

Create a `.env` file in the project root (see `.env.example`):

```
SONIOX_API_KEY=your_key_here

# TTS provider: "sixtydb" (default) or "soniox"
TTS_PROVIDER=sixtydb

# Only needed when TTS_PROVIDER=sixtydb
SIXTYDB_API_KEY=your_60db_key
SIXTYDB_VOICE_ID=your_60db_voice_id
```

> 60db's voice is chosen with `SIXTYDB_VOICE_ID`; the on-page voice dropdown only
> applies to the Soniox provider.

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

The backend opens one WebSocket to Soniox STT and (when spoken translation is enabled) drives a TTS backend, proxying between them and the browser. The diagram below shows the Soniox TTS backend; with `TTS_PROVIDER=sixtydb` the TTS leg is instead an HTTP `POST /tts-synthesize` per utterance against 60db, whose WAV response is unwrapped to PCM and streamed to the browser the same way.

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

The browser is a thin client: capture mic with `MediaRecorder` (or play the source file locally for follow-along), send bytes, receive token JSON and PCM audio. The STT plumbing lives in [main.py](main.py); the TTS backends live in [tts.py](tts.py).

The `/ws/translate` endpoint takes query params for `target_lang`, `voice`, `lang_id`, `diarize`, `tts` (toggle spoken translation), and optionally `audio_url` + `audio_duration` to put it in file mode.

Per browser connection the backend runs a few concurrent coroutines:

- **Input** - one of:
  - **`pipe_browser_audio_to_stt`** (mic mode) forwards mic audio bytes from browser to STT.
  - **`stream_url_to_stt`** (file mode) fetches `audio_url` over HTTP and feeds STT at real-time pace using `audio_duration` to compute the byte rate, so STT sees the file as if it were being spoken live.
- **`handle_stt`** - reads STT results, forwards them to the browser for UI rendering, and pushes translation tokens into a queue for TTS.
- **`TtsBackend.run`** *(only when TTS enabled)* - the selected TTS backend pulls translated text from the queue and streams PCM to the browser:
  - **`SonioxTtsBackend`** opens a pre-warmed Soniox TTS WebSocket, one stream per utterance, streams text chunks, and forwards decoded audio (plus a keepalive every 20s). It emits `session_done` once the queue is drained and the last stream has terminated.
  - **`SixtyDBTtsBackend`** accumulates each utterance's text and, on the utterance boundary, makes one `POST /tts-synthesize` call to 60db, unwraps the returned WAV to PCM, and streams it out. It emits `session_done` when the queue is exhausted.

## Files

```
main.py            FastAPI + Soniox STT WebSocket plumbing
tts.py             TTS backends (Soniox WebSocket / 60db HTTP) behind one interface
frontend/index.html  UI shell
frontend/styles.css  Dark theme
frontend/app.js      Mic capture + WebSocket + Web Audio playback
pyproject.toml     Dependencies
```

## A note on latency

With the Soniox provider, the first audio after you start speaking takes roughly 0.5–1.5 seconds to play. Most of that is the TTS model's first-byte time - it needs to see a few tokens before producing audio. The pre-warm shaves about 400ms off the median. The backend pipeline itself adds under 5ms.

The 60db provider uses the simple (non-streaming) `POST /tts-synthesize` endpoint, so it synthesizes a whole utterance per request: audio for an utterance starts only once that utterance's text is complete and the request returns. That's simpler but higher-latency than streaming; switch to Soniox if you need token-level streaming.
