import pydantic

from settings import settings


class BaseSettings(pydantic.BaseSettings):
    server_address: str = settings.external_server_address
    server_port: int = settings.external_server_port

    jwt_secret: str = settings.jwt_secret
    jwt_algorithm: str = settings.jwt_algorithm
    jwt_expiration: int = settings.jwt_expiration


base_settings = BaseSettings(
    _env_file='.env',
    _env_file_encoding='utf-8'
)
