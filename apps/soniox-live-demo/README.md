# Soniox Live

## Overview

Soniox Live is a **demo app** that shows how to stream audio from your microphone
directly to the Soniox [Real-time API](https://soniox.com/docs/stt/api-reference/websocket-api) for instant transcription and translation.

This is not the [Soniox App](https://soniox.com/soniox-app) (our end-user product). Instead, it is a
**reference implementation** for developers who want to learn how to embed
Soniox into their own web or mobile applications.

![Web and mobile demo apps](https://soniox.com/docs/_next/image?url=%2Fdocs%2Fdemo-apps%2Fsoniox-live.png&w=1080&q=75)

## Features

- Stream audio from your mic to Soniox in real time
- Low-latency, high-accuracy transcription in 60+ languages
- Low-latency speech translation to 60+ languages
- Runs in the browser (React) and mobile (React Native)
- Lightweight server issues temporary client keys for secure access

## Usage flow

1. Tap **Start** to begin streaming from your mic
1. **Live captions** appear word by word, then finalize
1. Toggle **Translation** and choose a target language for live translated captions
1. Tap **Stop** to end the session

## Architecture

- **Server (Python):** Stores your secret Soniox API key and issues **temporary API keys** to clients
- **Frontend (React & React Native):** Requests a temporary API key from your server,
  then streams microphone audio directly to Soniox servers for real-time transcription and translation

We provide all the implementations with links to GitHub:

- [Python server](./server)
- [React frontend](./react) (web)
- [React Native frontend](./react-native) (mobile)
