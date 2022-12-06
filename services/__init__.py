from settings import settings
from .rabbitmq_manager import RabbitMQ
from .sql import SQL

sql_connection_string = (
    'postgresql://{user}:{password}@{host}:{port}/{database}'.format(
        user=settings.sql_user,
        password=settings.sql_password,
        host=settings.sql_host,
        port=settings.sql_port,
        database=settings.sql_database
    )
)
amqp_connection_string = (
    'amqp://{user}:{password}@{host}:{port}/'.format(
        user=settings.amqp_user,
        password=settings.amqp_password,
        host=settings.amqp_host,
        port=settings.amqp_port
    )
)

sql = SQL(sql_connection_string)
rabbit_mq = RabbitMQ(
    amqp_connection_string, settings.service_name, settings.core_channel_number
)
