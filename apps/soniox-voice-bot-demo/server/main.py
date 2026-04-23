#!/usr/bin/env python

import asyncio
import os
from typing import List
from urllib.parse import parse_qs, urlparse

import dotenv
import pydantic
import structlog
import websockets
from websockets import ServerConnection
from websockets.asyncio.server import serve

from languages import LANGUAGES, LANGUAGES_MAP
from messages import ErrorMessage
from processors.llm import LLMProcessor
from processors.message_processor import MessageProcessor
from processors.stt import STTProcessor
from processors.tts import TTSProcessor
from processors.vad import VADProcessor
from session import Session
from tools import (
    get_system_message,
    get_tools,
)

dotenv.load_dotenv()
log = structlog.get_logger()

WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "localhost")
WEBSOCKET_PORT = int(os.getenv("WEBSOCKET_PORT", "8765"))

SONIOX_API_KEY = os.getenv("SONIOX_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

SONIOX_API_KEY_TTS = os.getenv("SONIOX_API_KEY_TTS", "")
SONIOX_API_HOST_TTS = os.getenv("SONIOX_API_HOST_TTS", "")


class QueryParams(pydantic.BaseModel):
    language: str
    voice: str

    audio_in_format: str = "pcm_s16le"
    audio_in_sample_rate: int = 16000
    audio_in_num_channels: int = 1
    audio_out_sample_rate: int = 24000

    @pydantic.model_validator(mode="before")
    @classmethod
    def unwrap_single_item_lists(cls, values):
        unwrapped = {}
        for key, value in values.items():
            if isinstance(value, list) and len(value) == 1:
                unwrapped[key] = value[0]
            else:
                unwrapped[key] = value
        return unwrapped


async def send_error_and_close(websocket: ServerConnection, error: str):
    log.error(
        "Error occurred, sending error message and closing connection", error=error
    )
    try:
        await websocket.send(ErrorMessage(error).json())
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await websocket.close()


async def handle(websocket: ServerConnection):
    # Get query parameters
    request = websocket.request
    if not request:
        await send_error_and_close(websocket, "No request found in websocket")
        return

    parsed_url = urlparse(request.path)
    query_params = parse_qs(parsed_url.query, keep_blank_values=True)

    try:
        params = QueryParams.model_validate(query_params)
    except pydantic.ValidationError as e:
        log.error("Invalid query parameters", query_params=query_params, error=e)
        await send_error_and_close(websocket, "Invalid query parameters")
        return

    if params.language not in LANGUAGES:
        await send_error_and_close(websocket, "Invalid language")
        return

    processors: List[MessageProcessor] = [
        VADProcessor(
            sample_rate=params.audio_in_sample_rate,
        ),
        STTProcessor(
            api_key=SONIOX_API_KEY,
            audio_format=params.audio_in_format,
            audio_sample_rate=params.audio_in_sample_rate,
            num_channels=params.audio_in_num_channels,
            language_hints=[params.language],
            context="Soniox",
        ),
        LLMProcessor(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            system_message=get_system_message(LANGUAGES_MAP[params.language]),
            tools=get_tools(),
        ),
        TTSProcessor(
            api_key=SONIOX_API_KEY_TTS,
            api_host=SONIOX_API_HOST_TTS,
            language=params.language,
            sample_rate=params.audio_out_sample_rate,
            voice=params.voice,
        ),
    ]

    session = Session(
        processors,
        websocket,
    )
    await session.run()


async def main():
    log.info("Warming up VAD model...")
    VADProcessor.warmup()
    log.info("Starting WebSocket server", host=WEBSOCKET_HOST, port=WEBSOCKET_PORT)
    async with serve(handle, WEBSOCKET_HOST, WEBSOCKET_PORT) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
