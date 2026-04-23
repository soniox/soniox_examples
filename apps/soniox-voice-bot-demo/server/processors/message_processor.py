import abc
from typing import Any, Awaitable, Callable

import structlog

from messages import Message


class MessageProcessor(abc.ABC):
    @abc.abstractmethod
    async def start(
        self,
        send_message: Callable[[Message], Awaitable[Any]],
        log: structlog.BoundLogger,
    ) -> None:
        pass

    @abc.abstractmethod
    async def process(self, message: Message) -> None:
        pass

    @abc.abstractmethod
    async def cleanup(self) -> None:
        pass
