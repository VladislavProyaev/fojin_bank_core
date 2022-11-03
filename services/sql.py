import time

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from common.constants.sql import SQLConstant
from settings import settings


class SessionAreNotAvailable(Exception):
    ...


class SQL:
    __slots__ = ('__client', '__session')

    def __init__(self):
        self.__client: Engine | None = None
        self.__session: Session | None = None

    @property
    def client(self) -> Engine:
        if self.__client is None:
            self._create_engine()

        return self.__client

    @property
    def session(self) -> Session:
        if self.__session is None:
            self._create_session()

        return self.__session

    def _create_engine(self) -> None:
        self.__client = create_engine(
            settings.sql_connection_string,
            echo=False,
            pool_pre_ping=True
        )

    def _create_session(self) -> None:
        try_restarts_after_fail = 0

        def _attempt_create_session(tries: int):
            for _ in range(SQLConstant.MAX_CONNECT_TRIES):
                try:
                    self.__session = Session(self.client)
                    return
                except SQLAlchemyError:
                    time.sleep(SQLConstant.SECONDS_SLEEP_AFTER_TRY)

            if (
                self.__session is None
                and tries != SQLConstant.MAX_TRIES_AFTER_FAIL
            ):
                tries += 1
                time.sleep(SQLConstant.SECONDS_SLEEP_AFTER_TRY)
                _attempt_create_session(tries)

        _attempt_create_session(try_restarts_after_fail)
        if self.__session is None:
            raise SessionAreNotAvailable(
                'SQL session are not available after '
                f'{SQLConstant.MAX_TRIES_AFTER_FAIL} tries.'
            )


sql = SQL()
