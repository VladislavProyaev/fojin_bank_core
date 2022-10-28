from datetime import timedelta

import pydantic

from settings import settings


class BaseSettings(pydantic.BaseSettings):
    server_address: str = settings.external_server_address
    server_port: int = settings.external_server_port

    jwt_secret: str = settings.jwt_secret_key
    jwt_algorithm: str = settings.jwt_algorithm
    jwt_access_token_expires: timedelta = settings.jwt_access_token_expires
    jwt_refresh_token_expires: timedelta = settings.jwt_refresh_token_expires


base_settings = BaseSettings(
    _env_file='.env',
    _env_file_encoding='utf-8'
)
