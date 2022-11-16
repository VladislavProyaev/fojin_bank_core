import asyncio
import json
from dataclasses import dataclass
from functools import partial
from typing import Callable, Any

import loguru
from aio_pika import connect_robust, IncomingMessage, Message, DeliveryMode
from aio_pika.abc import AbstractRobustConnection
from aio_pika.patterns import RPC
from aiormq.tools import awaitable
from fastapi import Request, Response


@dataclass(slots=True)
class RabbitMQMethod:
    method_name: str
    method_function: Callable


class RabbitMQ:
    __slots__ = (
        '__connection_string',
        '__loop',
        '__rpc',
        '__connection',
        '__service_name'
    )

    def __init__(
        self, connection_string: str, service_name: str
    ) -> None:
        self.__connection_string = connection_string
        self.__service_name: str = service_name
        self.__loop: asyncio.AbstractEventLoop | None = None
        self.__connection: AbstractRobustConnection | None = None
        self.__rpc: RPC | None = None

    @property
    def connection(self) -> AbstractRobustConnection | None:
        return self.__connection

    @property
    def rpc(self) -> RPC | None:
        return self.__rpc

    async def connect(
        self,
        loop: asyncio.AbstractEventLoop,
        methods: list[RabbitMQMethod]
    ) -> None:
        self.__loop = loop

        connection = await connect_robust(self.__connection_string, loop=loop)
        channel = await connection.channel()
        rpc = await RPC.create(channel)

        self.__connection = connection
        self.__rpc = rpc

        for method in methods:
            await self.__register(
                rpc,
                method.method_name,
                method.method_function,
                auto_delete=True
            )

    async def __register(
        self, rpc: RPC, method_name: str, func: Callable, **kwargs: Any
    ) -> Any:
        method_name = self.__service_name + method_name
        arguments = kwargs.pop("arguments", {})
        arguments.update({"x-dead-letter-exchange": self.__service_name})

        kwargs["arguments"] = arguments

        queue = await rpc.channel.declare_queue(method_name, **kwargs)

        if func in rpc.consumer_tags:
            raise RuntimeError("Function already registered")

        if method_name in rpc.routes:
            raise RuntimeError(
                "Method name already used for %r" % rpc.routes[method_name],
            )

        rpc.consumer_tags[func] = await queue.consume(
            partial(self.__on_call_message, method_name),
        )

        rpc.routes[method_name] = awaitable(func)
        rpc.queues[func] = queue

    async def __on_call_message(
        self, method_name: str, message: IncomingMessage,
    ) -> None:
        method = self.__rpc.routes.get(method_name)
        if method is None:
            return

        try:
            result = await method(message)
            result_message = {'status': True, 'answer': result}
        except Exception as exception:
            result_message = {'status': False, 'error': str(exception)}

        if message.reply_to is not None:
            result_message = json.dumps(result_message).encode('utf-8')
            new_message = Message(
                result_message, delivery_mode=DeliveryMode.NOT_PERSISTENT
            )
            await self.__rpc.channel.default_exchange.publish(
                new_message, message.reply_to
            )

    async def rpc_middleware(
        self, request: Request, call_next: Callable
    ) -> Any:
        try:
            connection = await connect_robust(
                self.__connection_string, loop=self.__loop
            )
            channel = await connection.channel()
            request.state.rpc = await RPC.create(channel)
            response = await call_next(request)
        except Exception as exception:
            response = Response("Internal server error", status_code=500)
            loguru.logger.exception(str(exception))

        return response
