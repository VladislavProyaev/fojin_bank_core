from asyncio import AbstractEventLoop

import pytest

from services import RabbitMQ
from services.rabbitmq_manager import RabbitMQMethod


@pytest.mark.asyncio
async def test_rabbit_connection(
    rabbitmq_service: RabbitMQ, event_loop: AbstractEventLoop
):
    await rabbitmq_service.connect(event_loop, [])
    assert rabbitmq_service.connection.is_closed is False
    await rabbitmq_service.connection.close()


@pytest.mark.asyncio
async def test_rabbit_adding_methods(
    rabbitmq_service: RabbitMQ,
    event_loop: AbstractEventLoop,
    rabbit_test_methods: list[RabbitMQMethod]
):
    service_name = 'test_service_'

    await rabbitmq_service.connect(event_loop, rabbit_test_methods)

    for index, route in enumerate(rabbitmq_service.rpc.routes):
        assert service_name + rabbit_test_methods[index].method_name == route

    await rabbitmq_service.connection.close()
