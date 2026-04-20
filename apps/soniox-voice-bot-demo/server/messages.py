import json


class Message:
    pass


class SessionStartMessage(Message):
    def json(self):
        return json.dumps({"type": "session_start"})


class UserAudioMessage(Message):
    def __init__(self, audio_data: bytes):
        self._audio_data = audio_data

    def audio_data(self):
        return self._audio_data


class TranscriptionMessage(Message):
    def __init__(self, final_tokens: list, non_final_tokens: list):
        self._final_tokens = final_tokens
        self._non_final_tokens = non_final_tokens

    def final_text(self):
        return "".join(token["text"] for token in self._final_tokens)

    def non_final_text(self):
        return "".join(token["text"] for token in self._non_final_tokens)

    def text(self):
        return self.final_text() + self.non_final_text()

    def json(self):
        return json.dumps(
            {
                "type": "transcription",
                "final_text": self.final_text(),
                "non_final_text": self.non_final_text(),
            }
        )


class TranscriptionEndpointMessage(Message):
    pass


class TextMessage(Message):
    """Text message that can be set programmatically instead of coming from the LLM."""

    def __init__(self, text: str):
        self._text = text

    def text(self):
        return self._text

    def json(self):
        return json.dumps(
            {
                "type": "llm_response",
                "text": self._text,
            }
        )


class LLMChunkMessage(Message):
    def __init__(self, text: str):
        self._text = text

    def text(self):
        return self._text

    def json(self):
        return json.dumps(
            {
                "type": "llm_response",
                "text": self._text,
            }
        )


class LLMFullMessage(Message):
    def __init__(self, text: str):
        self._text = text

    def text(self):
        return self._text


class TTSAudioMessage(Message):
    def __init__(self, audio_data: bytes):
        self._audio_data = audio_data

    def audio_data(self):
        return self._audio_data


class ErrorMessage(Message):
    """Critical error that terminates the session."""

    def __init__(self, error: str):
        self._error = error

    def error(self):
        return self._error

    def json(self):
        return json.dumps(
            {
                "type": "error",
                "error": self._error,
            }
        )


class MetricsMessage(Message):
    def __init__(self, metric_type: str, value_ms: float):
        self._metric_type = metric_type
        self._value_ms = value_ms

    def json(self):
        return json.dumps(
            {
                "type": "metric",
                "metric_type": self._metric_type,
                "value_ms": self._value_ms,
            }
        )


class UserSpeechStartMessage(Message):
    def json(self):
        return json.dumps({"type": "user_speech_start"})


class UserSpeechEndMessage(Message):
    def json(self):
        return json.dumps({"type": "user_speech_end"})
