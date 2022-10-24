from logging.config import fileConfig

from alembic import context

from common.base_model import BaseModelInterface
from services import sql
from settings import settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def target_metadata():
    return BaseModelInterface.metadata


def run_migrations_offline() -> None:
    ...


def run_migrations_online() -> None:
    config.set_main_option(
        'sqlalchemy.url',
        settings.sql_connection_string
    )
    metadata = target_metadata()

    with sql.client.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=metadata,
            transaction_per_migration=True
        )
        with connection.begin():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
