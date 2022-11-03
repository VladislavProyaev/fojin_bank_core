import traceback

import loguru

from services.sql import SQL


class BaseManager:
    __slots__ = ('__sql',)

    def __init__(self, sql: SQL) -> None:
        self.__sql = sql

    def __enter__(self):
        self.__sql.session.begin()
        return self

    def __exit__(
        self,
        exception_type: str | None,
        exception_value: str | None,
        exception_traceback: traceback.TracebackException | None
    ):
        if not exception_value:
            self.__sql.session.commit()
            loguru.logger.exception(str(exception_value))
        else:
            self.__sql.session.rollback()
