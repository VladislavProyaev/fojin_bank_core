import asyncio

import pytest

from services import amqp_connection_string, RabbitMQ
from services.rabbitmq_manager import RabbitMQMethod
from tests.test_rabbitmq.sample_methods import sample_methods


@pytest.fixture(scope='session')
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def rabbitmq_service() -> RabbitMQ:
    rabbitmq = RabbitMQ(amqp_connection_string, 'test_service_')
    return rabbitmq


@pytest.fixture
def rabbit_test_methods() -> list[RabbitMQMethod]:
    methods = []

    for method in sample_methods:
        methods.append(RabbitMQMethod(method['name'], method['function']))

    return methods
