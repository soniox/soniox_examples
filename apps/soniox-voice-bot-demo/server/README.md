# Soniox Voice Bot backend

## Overview

This project is a backend for a real-time, voice-to-voice conversational assistant built with the [Soniox real-time API](https://soniox.com/). It listens to users in any language, transcribes their speech, and provides instant, AI-driven answers, removing language barriers in customer service.

The bot is designed to be highly customizable and flexible, allowing developers to easily adapt it to their specific business needs.
This demo implementation acts as an appointment booking bot for a car repair shop ("Soniox AutoWorks"), but can be easily adapted to any business.

## How it works

The service is built around a modular architecture where different "processors" handle specific tasks. When a user connects, a Session is created to manage the entire conversation lifecycle.

### System architecture

The service consists of four main components that process messages concurrently:

- **Voice Activity Detection (VAD) Processor**: Uses Silero VAD to detect speech boundaries in incoming audio. Emits `UserSpeechStartMessage` and `UserSpeechEndMessage` events to interrupt TTS when the user starts speaking.
- **Speech-to-Text (STT) Processor**: Receives the raw audio from the user and uses the Soniox API to convert it into text tokens in real-time. It generates `TranscriptionMessage` events as the user speaks.
- **Language Model (LLM) Processor**: Receives transcription messages, manages the conversation history, and uses a large language model to decide what to do next. It can either generate a direct text response or use one of the provided tools.
- **Text-to-Speech (TTS) Processor**: Receives streaming text chunks from the LLM and uses the Soniox API to convert them into audible speech in real-time, streaming audio back to the user as it's generated.

### Data & session flow

A user connects to the server via a WebSocket. A new Session instance is created for them.

All incoming audio and internal events (like a finished transcription) are placed on a central message queue.
The Session pulls a message from the queue and broadcasts it to all active processors (STT, LLM, TTS).
Each processor inspects the message and acts if it's relevant. For example:

- The STT processor only acts on `UserAudioMessage` to generate a transcription.
- LLM processors acts on `TranscriptionMessage` to aggregate the transcript text and on `TranscriptionEndpointMessage` to generate a response.
- The TTS processor acts on streaming `LLMChunkMessage` and `LLMFullMessage` to generate audio in real-time.

Messages intended for the user (like transcription updates, LLM text chunks, or TTS audio bytes) are streamed back to the user over the WebSocket.

## Quick start

1. **Clone the repository:**

   ```sh
   git clone https://github.com/soniox/soniox_examples.git
   cd apps/soniox-voice-bot-demo/server
   ```

2. **Install Python dependencies:**

   ```sh
   # Create a virtual environment and activate it
   uv venv
   source .venv/bin/activate

   # Install Python dependencies
   uv sync
   ```

3. **Set up environment variables:**

   Copy `.env.example` to `.env` and fill in your API keys:

   ```sh
   # Soniox is used for speech-to-text and text-to-speech
   SONIOX_API_KEY=your_soniox_key
   # OpenAI is used for the large language model
   OPENAI_API_KEY=your_openai_key
   ```

4. **Run the backend server:**

   ```sh
   uv run main.py
   ```

5. **Run the frontend:**  
   Connect a Frontend or Twilio Proxy: This server is now running and waiting for a WebSocket connection. To interact with it, you need a client. See the [frontend/](../frontend/) or [twilio/](../twilio/) directories for examples.

## Customization guide

### 1. Customizing the AI persona

Open `tools.py` and find the `get_system_message()` function. Edit the f-string to change the assistant's persona, instructions, and company information.

### 2. Customizing the tools

The LLM uses tools to interact with the outside world. This demo includes three mock tools you should replace with your own backend logic.

- `search_knowledge_base`: Takes a user's query (e.g., "what are your hours?") and should return relevant information from your knowledge base, FAQ, or database. You can search your internal knowledge base here.
- `check_availability`: Takes a `service_type` and a `date` and should query your scheduling system or calendar to find available time slots for the service.
- `create_appointment`: Takes all the necessary customer and vehicle details (`full_name`, `phone_number`, `service_type`, `date`, `time`, etc.) and should create an entry in your scheduling system.

## Deployment

This application is ready for containerized deployment using Docker. A Dockerfile which can be used as a base for your own containerized deployment is provided.

1. Build the Docker Image

   ```sh
   docker build -t soniox-voice-bot-server .
   ```

2. Run the Docker Container

   When running the container, you must set the `SONIOX_API_KEY` and `OPENAI_API_KEY` environment variables.

   ```sh
   docker run -d \
     -e SONIOX_API_KEY="your_soniox_key" \
     -e OPENAI_API_KEY="your_openai_key" \
     -p 8765:8765 \
     soniox-voice-bot-server
   ```
