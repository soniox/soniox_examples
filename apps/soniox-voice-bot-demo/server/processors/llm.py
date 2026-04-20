import asyncio
import json
import time
from typing import Any, Awaitable, Callable, List, Tuple

import openai
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolUnionParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall

from messages import (
    ErrorMessage,
    LLMChunkMessage,
    LLMFullMessage,
    MetricsMessage,
    SessionStartMessage,
    TranscriptionEndpointMessage,
    TranscriptionMessage,
    UserSpeechStartMessage,
)
from processors.message_processor import MessageProcessor


def _update_tool_calls(
    tool_calls: list,
    delta: List[ChoiceDeltaToolCall],
):
    for tool_chunk in delta:
        index = tool_chunk.index
        if len(tool_calls) <= index:
            tool_calls.append(
                {
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                }
            )
        tc = tool_calls[index]
        if tool_chunk.id:
            tc["id"] += tool_chunk.id
        if tool_chunk.function and tool_chunk.function.name:
            tc["function"]["name"] += tool_chunk.function.name
        if tool_chunk.function and tool_chunk.function.arguments:
            tc["function"]["arguments"] += tool_chunk.function.arguments

    return tool_calls


class LLMProcessor(MessageProcessor):
    """Processor that handles LLM interactions with streaming support and tool calling."""

    def __init__(
        self,
        api_key: str,
        model: str,
        system_message: str,
        base_url: str | None = None,
        tools: List[
            Tuple[ChatCompletionToolUnionParam, Callable[..., Awaitable[Any]]]
        ] = [],
    ):
        """Initialize the LLM processor.

        Args:
            api_key: The API key for the LLM service.
            model: The model name to use (e.g., "gpt-4.1-mini").
            system_message: The system prompt to initialize the conversation.
            base_url: Optional custom base URL for the OpenAI-compatible API.
            tools: Optional list of (tool_description, tool_function) tuples for tool calling.
        """
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

        # Prepare tools for LLM
        self._tool_descriptions = []
        self._tool_functions = {}
        for tool in tools:
            self._tool_descriptions.append(tool[0])

            if tool[0]["type"] == "function":
                self._tool_functions[tool[0]["function"]["name"]] = tool[1]

        self._active_task: asyncio.Task | None = None
        self._messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=system_message,
            )
        ]

        self._llm_start_time: float | None = None
        self._first_token_sent: bool = False

    async def start(self, send_message, log):
        self.log = log.bind(processor="llm")
        self._send_message = send_message

    async def process(self, message):
        if isinstance(message, TranscriptionMessage):
            self._append_user_message(message)
        elif isinstance(message, SessionStartMessage):
            self.log.debug("Session start message")

            # Start LLM generation as a background task
            # If you want user to start the conversation, simply remove this condition
            self._active_task = asyncio.create_task(self._generate_llm_response())

        elif isinstance(message, TranscriptionEndpointMessage):
            self.log.debug("Transcription endpoint message")
            # Start LLM generation as a background task
            self._active_task = asyncio.create_task(self._generate_llm_response())

        elif isinstance(message, UserSpeechStartMessage):
            self.log.debug("User speech start detected - cancelling LLM generation")
            if self._active_task and not self._active_task.done():
                self._active_task.cancel()

    async def cleanup(self):
        if self._active_task and not self._active_task.done():
            self.log.debug("Cleaning up and cancelling active LLM task")
            self._active_task.cancel()
            try:
                await self._active_task
            except asyncio.CancelledError:
                pass

    def _append_user_message(
        self,
        message: TranscriptionMessage,
    ):
        # Cancel any ongoing LLM generation
        if self._active_task and not self._active_task.done():
            self._active_task.cancel()

        text = message.final_text()
        if not text:
            # No need to create a new message if there is no final text
            return

        if self._messages and self._messages[-1]["role"] == "user":
            # If last message is a user message, just extend the list
            if not isinstance(self._messages[-1]["content"], str):
                self._messages[-1]["content"] = ""
            self._messages[-1]["content"] += text

        else:
            # Add new message to the list and cancel any ongoing LLM generation
            self._messages.append(
                ChatCompletionUserMessageParam(
                    role="user",
                    content=text.lstrip(),
                )
            )

    def _append_llm_message(
        self,
        message: LLMChunkMessage,
    ):
        if self._messages and self._messages[-1]["role"] == "assistant":
            # If last message is an assistant message, just extend the list
            if not isinstance(self._messages[-1].get("content"), str):
                self._messages[-1]["content"] = ""
            self._messages[-1]["content"] += message.text()  # type: ignore

        else:
            # Add new message to the list
            self._messages.append(
                ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=message.text().lstrip(),
                )
            )

    async def _generate_llm_response(self):
        # If there was no new user text, cancel the task
        # (but allow assistant message to be just after system message)
        if not self._messages or self._messages[-1]["role"] == "assistant":
            self.log.debug("No new user text, cancelling LLM generation task")
            return

        self.log.debug("Starting LLM generation task", messages=self._messages)

        self._llm_start_time = time.perf_counter()
        self._first_token_sent = False

        try:
            full_text = ""

            async def stream_response():
                nonlocal full_text

                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=self._messages,
                    stream=True,
                    tools=self._tool_descriptions,
                    tool_choice="auto",
                )
                tool_calls = []

                async for chunk in response:
                    if chunk.choices[0].delta.tool_calls:
                        # Tool calls
                        tool_calls = _update_tool_calls(
                            tool_calls, chunk.choices[0].delta.tool_calls
                        )
                    elif chunk.choices[0].delta.content:
                        # Content - streaming to user
                        text = chunk.choices[0].delta.content
                        if text:
                            if not self._first_token_sent and self._llm_start_time:
                                self._first_token_sent = True
                                first_token_ms = (
                                    time.perf_counter() - self._llm_start_time
                                ) * 1000
                                await self._send_message(
                                    MetricsMessage("llm_first_token_ms", first_token_ms)
                                )

                            message = LLMChunkMessage(text)
                            await self._send_message(message)
                            self._append_llm_message(message)

                            full_text += text

                # Call tools
                if tool_calls:
                    self.log.debug("Calling tools", tool_calls=tool_calls)
                    self._messages.append(
                        ChatCompletionAssistantMessageParam(
                            role="assistant",
                            tool_calls=tool_calls,
                        )
                    )

                for tool_call in tool_calls:
                    response = await self._call_tool(tool_call)
                    self.log.debug(
                        "Got tool call response", tool=tool_call, response=response
                    )

                    self._messages.append(
                        ChatCompletionToolMessageParam(
                            role="tool",
                            tool_call_id=tool_call["id"],
                            content=response,
                        )
                    )

                # If there were any tool calls, call the LLM again
                if tool_calls:
                    return await stream_response()

            await stream_response()

            # Send the full aggregated response
            if full_text:
                await self._send_message(LLMFullMessage(full_text))
                total_ms = (time.perf_counter() - self._llm_start_time) * 1000
                await self._send_message(MetricsMessage("llm_total_ms", total_ms))

        except asyncio.CancelledError:
            self.log.debug("LLM generation task was cancelled")
        except Exception as e:
            self.log.error(f"Error during LLM generation: {e}")
            if self._send_message:
                await self._send_message(ErrorMessage("Failed to generate response."))
        finally:
            self._active_task = None

    async def _call_tool(
        self,
        tool_call: Any,
    ) -> str:
        name = tool_call["function"]["name"]
        arguments = tool_call["function"]["arguments"]

        try:
            parsed_arguments = json.loads(arguments)
            function_output = await self._tool_functions[name](**parsed_arguments)
            if not isinstance(function_output, str):
                return json.dumps(function_output)
            return function_output

        except Exception as e:
            self.log.error(f"Error calling tool: {e}")
            # Also tell the LLM that the tool call failed and continue.
            return f"Error calling tool: {e}"
