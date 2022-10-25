from common.constants.base_constant import BaseConstant


class SQLConstant(BaseConstant):
    MAX_CONNECT_TRIES: int = 5
    MAX_TRIES_AFTER_FAIL: int = 3

    SECONDS_SLEEP_AFTER_TRY: int = 10
