import asyncio

from aio_pika import connect_robust
from aio_pika.patterns import RPC
from fastapi import Request, Response

from settings import settings


def remote_method():
    return 'It works!'


async def consume(loop: asyncio.AbstractEventLoop):
    connection = await connect_robust(
        settings.ampq_connection_string, loop=loop
    )
    channel = await connection.channel()
    rpc = await RPC.create(channel)

    await rpc.register('remote_method', remote_method, auto_delete=True)
    return connection


async def rpc_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)

    try:
        loop = asyncio.get_event_loop()
        connection = await connect_robust(
            settings.ampq_connection_string, loop=loop
        )
        channel = await connection.channel()
        request.state.rpc = await RPC.create(channel)
        response = await call_next(request)
    finally:
        await request.state.rpc.close()

    return response


def get_rpc(request: Request):
    rpc = request.state.rpc
    return rpc
