import json
from datetime import datetime, timezone
from typing import ClassVar

from aio_pika import IncomingMessage
from jose import jwt
from passlib.context import CryptContext

from api import UserModel
from api.schemas.token import Token
from api.schemas.user import AuthorizedUser
from common.exceptions import CoreException
from settings import settings


class JWTManager:
    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def create_token(self, user_model: UserModel) -> Token:
        access_token = self.__create_access_token(user_model)
        refresh_token = self.__create_refresh_token(user_model, access_token)

        token = Token(
            access_token=access_token, refresh_token=refresh_token
        )

        return token

    @staticmethod
    def __get_jwt_data(user_model: UserModel) -> dict:
        authorized_user = AuthorizedUser.from_orm(user_model)
        jwt_data = authorized_user.dict()

        return jwt_data

    def __create_access_token(self, user_model: UserModel) -> str:
        jwt_data = self.__get_jwt_data(user_model)

        expire = datetime.now(timezone.utc) + settings.jwt_access_token_expires
        jwt_data.update({"exp": expire})

        access_token = jwt.encode(
            jwt_data,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        return access_token

    def __create_refresh_token(
        self, user_model: UserModel, access_token: str
    ) -> str:
        jwt_data = self.__get_jwt_data(user_model)

        expire = datetime.now(timezone.utc) + settings.jwt_refresh_token_expires
        jwt_data.update({"exp": expire})

        refresh_token = jwt.encode(
            jwt_data,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            access_token=access_token
        )

        return refresh_token

    @staticmethod
    def validate_access_token(message: IncomingMessage) -> IncomingMessage:
        exception = CoreException('Could not validate credentials')

        headers = message.headers
        auth_header = headers.get('Authorization')
        if auth_header is None:
            raise exception

        token_type, access_token = auth_header.split(' ')
        if token_type != 'Bearer':
            raise exception

        return message

    jwt_required: ClassVar[bool] = validate_access_token

    @staticmethod
    def encode_access_token(message: IncomingMessage) -> str:
        headers = message.headers
        auth_header = headers.get('Authorization')
        _, access_token = auth_header.split(' ')

        payload = jwt.decode(
            access_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        payload.pop('exp', None)

        payload = json.dumps(payload)

        return payload


jwt_manager = JWTManager()
