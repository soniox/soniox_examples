# Soniox Voice Bot Demo

## Overview

This project is a complete reference implementation for building a real-time, voice-to-voice conversational AI assistant. It demonstrates how to integrate streaming speech-to-text, a large language model (LLM), and streaming text-to-speech (TTS) into a seamless, low-latency application.

The demo bot is pre-configured as an appointment booking assistant for a fictional car repair shop, "Soniox AutoWorks." It can book appointments for services such as oil changes and car repairs, collect customer names and vehicle information, provide available appointment slots, and interactively guide users through the booking process. It leverages modular tools that can call external functions or APIs, enabling real-world actions and dynamic responses.

The entire voice bot codebase is designed for easy customization and extension to other domains. You can quickly adapt the bot to different business needs, integrate new tools, or change its persona, making it a flexible starting point for any conversational AI application.

![Voice bot screenshot](./frontend/screenshot.png)

## Interactive demo

There are two ways to try out the voice bot:

- Web ([frontend/](./frontend/)): The included web frontend provides a simple user interface for interacting with the voice bot.
- Phone call ([twilio/](./twilio/)): You can also connect the bot to a phone number. Note that telephony providers like Twilio naturally introduce additional audio latency compared to a direct web connection.

### Example conversation

> **Bot:** Hello, thank you for calling Soniox AutoWorks! How can I help you today? You can speak in any language.
>
> **User:** Hi, I was wondering what services you offer.
>
> **Bot:** `search_knowledge_base(query="What services do you offer?")`
>
> **Bot:** We offer oil changes, tire rotations, brake inspections, engine diagnostics, and more. What can I help you with?
>
> **User:** I need an oil change. Do you have anything available for this Friday?
>
> **Bot:** `check_availability(service_type="oil_change", date="2025-09-12")`
>
> **Bot:** Yes, for this Friday, September 12th, we have several openings in the morning at 9, 9:30, 10, and 10:30, or in the afternoon at 2:30 and 3 PM.
>
> **User:** Let's do 10:30 AM. My name is Alex Smith, phone is 555-123-4567, and I have a 2022 Toyota Camry.
>
> **Bot:** `create_appointment(full_name="Alex Smith", phone_number="555-123-4567", service_type="oil_change", date="2025-09-12", time="10:30", vehicle_info="2022 Toyota Camry")`
>
> **Bot:** Perfect. I've booked you in for an oil change for your 2022 Toyota Camry this Friday, September 12th, at 10:30 AM. We'll see you then!

## Features

- End-to-end real-time: Fully streaming architecture (voice-in, voice-out) for natural, low-latency conversations.
- Multilingual: Understands and responds to users in multiple languages.
- Customizable AI: The bot's persona and business logic are defined in a single, easy-to-edit file.
- Extensible tools: Connect the LLM to your own APIs and databases to perform real-world actions.
- Multiple ways to interact: Web frontend, Twilio phone call, or any other WebSocket-based connection.

## How it works

The system is built on a modular, asynchronous architecture. When a user connects, a Session is created to orchestrate the entire conversation, managing the flow of data between three core processors.

- **Speech-to-Text (STT)**: The user's voice is captured by a client (web app or phone call) and streamed to the backend. The STT Processor uses the Soniox API to transcribe the audio into text in real-time.
- **Large Language Model (LLM)**: The transcribed text is sent to the LLM Processor. It maintains the conversation history, determines the user's intent, and decides whether to generate a direct response or use a predefined tool (like checking available slots).
- **Text-to-Speech (TTS)**: The LLM's final text response is sent to the TTS Processor, which converts it back into audio and streams it to the user, completing the conversational turn.

## Project components

This repository contains three main packages:

- [server/](./server/) (Python): The core backend that orchestrates the conversation. It defines the bot's persona, its tools, and manages the WebSocket connection.
- [frontend/](./frontend/) (React): A web-based user interface that captures microphone audio, streams it to the backend, and plays back the audio response. It also displays the live transcription.
- [twilio/](./twilio/) (Python): An optional proxy server that bridges phone calls from Twilio to the voice bot backend, enabling real-time AI phone support.

## Getting started

1. **Run the backend**: Navigate to the [server/](./server/) directory. Follow its [README.md](./server/README.md) to install dependencies, set your API keys in a `.env` file, and run the backend server.

2. **Run a frontend or phone integration**:

   - For the web interface: Navigate to the [frontend/](./frontend/) directory, follow its [README.md](./frontend/README.md) to install dependencies, and run the development server. Open your browser to the frontend URL (typically [http://localhost:5173](http://localhost:5173)) and begin speaking.
   - For phone integration: Navigate to the [twilio/](./twilio/) directory and follow its [README.md](./twilio/README.md).

## Next steps & customization

Use this application as a starting point to build your own custom voice assistant. The primary file for customization is [server/tools.py](./server/tools.py).

- **Change the persona**: Edit the `get_system_message()` function to define your bot's personality, role, and instructions.
- **Implement your own tools**: Replace the mock logic in the tool functions (`search_knowledge_base`, `check_availability`, `create_appointment`) with your own business logic and API calls.
- **Do whatever you want**: Everything in this project is completely open-source and customizable. Customize the backend, frontend, or phone integration to fit your needs.
