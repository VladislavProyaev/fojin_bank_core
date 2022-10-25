import asyncio

from starlette.middleware.sessions import SessionMiddleware
from uvicorn import Config, Server

from api.app import app
from api.base_settings import base_settings
from api.module_settings import event_loop
from api.support_functions.check_permission_types import check_permission_types
from services.rabbit_mq.rabbit import consume, rpc_middleware

app.add_middleware(SessionMiddleware, secret_key=base_settings.jwt_secret)
app.middleware('http')(rpc_middleware)


@app.on_event('shutdown')
async def shutdown_event():
    pass


@app.on_event('startup')
async def startup_event():
    asyncio.ensure_future(consume(event_loop))
    check_permission_types()


config = Config(
    app=app,
    loop=event_loop,
    reload=True,
    host=base_settings.server_address,
    port=base_settings.server_port
)

server = Server(config)
