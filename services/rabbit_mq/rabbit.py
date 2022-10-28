import asyncio
from functools import partial
from typing import Callable, Any

from aio_pika import connect_robust, IncomingMessage
from aio_pika.patterns import RPC
from aiormq.tools import awaitable
from fastapi import Request, Response

from common.rabbit_method import RabbitMQMethod
from settings import settings


class RabbitMQ:
    __slots__ = (
        '__connection_string',
        '__loop',
        '__rpc'
    )

    def __init__(self, connection_string: str) -> None:
        """
        RPC: Remote Procedure Call helper.
        """
        self.__connection_string = connection_string
        self.__loop: asyncio.AbstractEventLoop | None = None
        self.__rpc: RPC | None = None

    async def connect(
        self,
        loop: asyncio.AbstractEventLoop,
        methods: list[RabbitMQMethod]
    ) -> None:
        self.__loop = loop

        connection = await connect_robust(
            settings.ampq_connection_string, loop=loop
        )
        channel = await connection.channel()
        rpc = await RPC.create(channel)
        self.__rpc = rpc

        for method in methods:
            await self.register(
                rpc,
                method.method_name,
                method.method_function,
                auto_delete=True
            )

    async def register(
        self, rpc: RPC, method_name: str, func: Callable, **kwargs: Any
    ) -> Any:
        arguments = kwargs.pop("arguments", {})
        arguments.update({"x-dead-letter-exchange": rpc.DLX_NAME})

        kwargs["arguments"] = arguments

        queue = await rpc.channel.declare_queue(method_name, **kwargs)

        if func in rpc.consumer_tags:
            raise RuntimeError("Function already registered")

        if method_name in rpc.routes:
            raise RuntimeError(
                "Method name already used for %r" % rpc.routes[method_name],
            )

        rpc.consumer_tags[func] = await queue.consume(
            partial(self.on_call_message, method_name),
        )

        rpc.routes[method_name] = awaitable(func)
        rpc.queues[func] = queue

    async def on_call_message(
        self, method_name: str, message: IncomingMessage,
    ) -> None:
        method = self.__rpc.routes.get(method_name)
        if method is None:
            return

        result = await method(message)
        if result is not None:
            method = self.__rpc.routes.get(message.reply_to)
            if method is None:
                return

    async def rpc_middleware(
        self, request: Request, call_next: Callable
    ) -> Any:
        try:
            connection = await connect_robust(
                settings.ampq_connection_string, loop=self.__loop
            )
            channel = await connection.channel()
            request.state.rpc = await RPC.create(channel)
            response = await call_next(request)
        except Exception:
            response = Response("Internal server error", status_code=500)

        return response


rabbit_mq = RabbitMQ(settings.ampq_connection_string)
