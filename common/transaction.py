from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

import loguru

if TYPE_CHECKING:
    from services.sql import SQL


class Transaction:
    __slots__ = ('__sql', '__savepoint')

    def __init__(self, sql: SQL) -> None:
        self.__sql = sql

    @property
    def sql(self) -> SQL:
        return self.__sql

    def __enter__(self):
        return self

    def __exit__(
        self,
        exception_type: str | None,
        exception_value: str | None,
        exception_traceback: traceback.TracebackException | None
    ):
        if not exception_value:
            self.__sql.session.commit()
        else:
            self.__sql.session.rollback()
            # loguru.logger.exception(str(exception_value))
