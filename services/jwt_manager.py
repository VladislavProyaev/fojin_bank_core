import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import ClassVar, Literal

from aio_pika import IncomingMessage
from jose import jwt
from passlib.context import CryptContext

from api import UserModel
from api.schemas.token import Token
from api.schemas.user import AuthorizedUser
from common.constants.token_types import TokenTypes
from common.exceptions import CoreException
from settings import settings

exception = CoreException('Could not validate credentials')


class JWTManager:
    @dataclass
    class ParsedHeader:
        message: IncomingMessage

        def __post_init__(self) -> None:
            headers = self.message.headers
            self.header = headers.get('Authorization')

            if self.header is not None:
                self.token_type, self.access_token = self.header.split(' ')
            else:
                self.token_type, self.access_token = (None, None)

    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_token(self, user_model: UserModel) -> Token:
        access_token = self.__create_token(user_model, TokenTypes.ACCESS)
        refresh_token = self.__create_token(
            user_model, TokenTypes.REFRESH, access_token=access_token
        )

        token = Token(
            access_token=access_token, refresh_token=refresh_token
        )

        return token

    @staticmethod
    def __get_jwt_data(user_model: UserModel) -> dict:
        authorized_user = AuthorizedUser.from_orm(user_model)
        jwt_data = authorized_user.dict()

        return jwt_data

    def __create_token(
        self,
        user_model: UserModel,
        token_type: Literal['Access', 'Refresh'], *,
        access_token: str | None = None
    ) -> str:
        if token_type == TokenTypes.ACCESS:
            expire = (
                datetime.now(timezone.utc) + settings.jwt_access_token_expires
            )
        elif token_type == TokenTypes.REFRESH:
            expire = (
                datetime.now(timezone.utc) + settings.jwt_refresh_token_expires
            )
        else:
            raise CoreException('Wrong token type!')

        jwt_data = self.__get_jwt_data(user_model)
        jwt_data.update({"exp": expire})

        token = jwt.encode(
            jwt_data,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            access_token=access_token
        )

        return token

    def __validate_access_token(
        self, message: IncomingMessage
    ) -> IncomingMessage:
        header = self.ParsedHeader(message)
        if header.header is None or header.token_type != 'Bearer':
            raise exception

        return message

    jwt_required: ClassVar[IncomingMessage] = __validate_access_token

    def encode_access_token(self, message: IncomingMessage) -> str:
        header = self.ParsedHeader(message)

        payload = jwt.decode(
            header.access_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        payload.pop('exp', None)
        payload = json.dumps(payload)

        return payload


jwt_manager = JWTManager()
