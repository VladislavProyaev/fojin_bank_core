import asyncio

from api.app import init_routers
from api.module_settings import event_loop
from api.server import server
from common.base_model import BaseModelInterface
from services import sql
from services.alembic.alembic_handler import AlembicHandler
from settings import settings


class WebServer:

    def __init__(self) -> None:
        self._loop = event_loop

    def run(self) -> None:
        init_routers()

        if settings.run_alembic:
            alembic_handler = AlembicHandler(
                sql.session, sql.client, BaseModelInterface.metadata
            )
            sorted_metadata_tables = alembic_handler.execute()
            BaseModelInterface.metadata.tables = sorted_metadata_tables

        BaseModelInterface.metadata.create_all(sql.client)

        self._loop.create_task(server.serve())

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop


web_server = WebServer()
web_server.run()
web_server.loop.run_forever()
