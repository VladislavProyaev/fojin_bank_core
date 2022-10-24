import time

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from settings import settings


class SQL:
    def __init__(self):
        self._max_connect_tries = 5
        self._max_tries_after_fail = 3
        self._sleep_after_try = 30
        self._client = None
        self._session = None

        self._create_engine()
        self._create_session()

    def _create_engine(self) -> None:
        self._client = create_engine(
            settings.sql_connection_string,
            echo=False,
            pool_pre_ping=True
        )

    def _create_session(self) -> None:
        try_restarts_after_fail = 0

        def _attempt_create_session(tries: int):
            for _ in range(self._max_connect_tries):
                try:
                    self._session = Session(self.client)
                    return
                except Exception:
                    self._session = None
                    time.sleep(self._sleep_after_try)

            if self.session is None and tries != self._max_tries_after_fail:
                tries += 1
                time.sleep(self._sleep_after_try)
                _attempt_create_session(tries)

        _attempt_create_session(try_restarts_after_fail)
        if self.session is None:
            raise Exception(
                'SQL session are not available after '
                f'{self._max_tries_after_fail} tries. Bot loop is closed!'
            )

    @property
    def client(self) -> Engine:
        return self._client

    @property
    def session(self) -> Session:
        return self._session


sql = SQL()
