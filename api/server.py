import asyncio

from starlette.middleware.sessions import SessionMiddleware
from uvicorn import Config, Server

from api.app import app
from api.base_settings import base_settings
from api.methods.users import user_registration, user_handler_action, \
    user_authorization, refresh_access_token
from api.module_settings import event_loop
from api.support_functions.initialize_permission_types import \
    initialize_permission_types
from services.rabbitmq_manager import rabbit_mq, RabbitMQMethod

app.add_middleware(SessionMiddleware, secret_key=base_settings.jwt_secret)
app.middleware('http')(rabbit_mq.rpc_middleware)


@app.on_event('shutdown')
async def shutdown_event():
    pass


@app.on_event('startup')
async def startup_event():
    methods = [
        RabbitMQMethod('user_registration', user_registration),
        RabbitMQMethod('user_authorization', user_authorization),
        RabbitMQMethod('user_handler_action', user_handler_action),
        RabbitMQMethod('refresh_access_token', refresh_access_token),
    ]
    asyncio.ensure_future(rabbit_mq.connect(event_loop, methods))

    initialize_permission_types()


config = Config(
    app=app,
    loop=event_loop,
    reload=True,
    host=base_settings.server_address,
    port=base_settings.server_port
)

server = Server(config)
