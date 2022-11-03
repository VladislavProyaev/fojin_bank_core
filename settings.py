import re
import socket
from datetime import timedelta

import dotenv
import pydantic

dotenv.load_dotenv()


class Settings(pydantic.BaseSettings):
    service_name: str = 'core'
    external_server_port: int
    external_server_address: str

    internal_server_port: int
    internal_server_address: str

    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expires = timedelta(minutes=15)
    jwt_refresh_token_expires = timedelta(days=30)

    local_files_root: str
    docker_files_root: str

    run_alembic: bool
    sql_connection_string: str

    @pydantic.validator('sql_connection_string')
    def resolve_host(cls, v: str):
        host_regex = (
            r'(?:\@)((\w+)|(((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b)+))(?:\:)'
        )
        word_regex = r'\w+'

        host = re.search(host_regex, v).group(1)

        if re.match(word_regex, host):
            host = socket.gethostbyname(host)

        connection_string = re.sub(host_regex, '@{0}:'.format(host), v)
        return connection_string

    ampq_connection_string: str

    alembic_debug: bool = True
    auto_apply_migrations: bool = True
    is_first_start: bool = False

    local_files_root: str
    docker_files_root: str

    @property
    def files_root(self) -> str:
        if self.alembic_debug:
            return self.local_files_root
        else:
            return self.docker_files_root

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False


settings = Settings()
