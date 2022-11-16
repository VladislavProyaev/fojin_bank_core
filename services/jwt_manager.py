from dataclasses import dataclass
from datetime import datetime, timezone
from typing import ClassVar, Literal

from aio_pika import IncomingMessage
from jose import jwt
from jose.exceptions import JWTClaimsError, JWTError
from jwt import ExpiredSignatureError
from passlib.context import CryptContext

from api.models import UserModel
from api.schemas.token import Token
from api.schemas.user import AuthorizedUser
from common.constants.token_types import TokenTypes
from common.exceptions import CoreException
from services import sql
from settings import settings

exception = CoreException('Could not validate credentials')


class JWTManager:
    @dataclass
    class ParsedHeader:
        message: IncomingMessage
        is_valid: bool = False
        access_token: str | None = None

        def __post_init__(self) -> None:
            headers = self.message.headers
            authorization = headers.get('Authorization')
            self.refresh_token = headers.get('refresh')

            if authorization is not None:
                token_type, self.access_token = authorization.split(' ')
                if self.refresh_token is not None and token_type == 'Bearer':
                    self.is_valid = True

    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(
        self, plain_password: str | bytes, hashed_password: str | bytes
    ) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

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

    def __validate_token(
        self, message: IncomingMessage
    ) -> IncomingMessage:
        header = self.ParsedHeader(message)
        if not header.is_valid:
            raise exception

        datetime_now = datetime.now(timezone.utc)
        access_token = self.encode_token(message)
        if access_token['exp'] < datetime_now:
            refresh_token = self.encode_token(message, TokenTypes.REFRESH)
            if refresh_token['exp'] < datetime_now:
                raise Exception('Re-authorization required!')
            raise Exception('Access token needs to be updated')

        return message

    jwt_required: ClassVar[IncomingMessage] = __validate_token

    def encode_token(
        self,
        message: IncomingMessage,
        token_type: Literal['Access', 'Refresh'] = 'Access'
    ) -> dict:
        header = self.ParsedHeader(message)
        if token_type == 'Access':
            token = header.access_token
            access_token = None
        elif token_type == 'Refresh':
            token = header.refresh_token
            access_token = header.access_token
        else:
            raise exception

        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                access_token=access_token
            )
        except (JWTError, ExpiredSignatureError, JWTClaimsError):
            raise CoreException(
                'Incorrect access/refresh tokens. Need to reauthenticate!'
            )

        return payload

    def refresh_token(self, message: IncomingMessage) -> Token:
        access_token = self.encode_token(message)
        user_model = UserModel.get(
            sql,
            name=access_token['name'],
            surname=access_token['surname'],
            phone=access_token['phone'],
            password=access_token['password']
        )
        token = self.create_token(user_model)

        return token


jwt_manager = JWTManager()
