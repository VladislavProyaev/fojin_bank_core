from aio_pika import IncomingMessage
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from api.behavior.user_manager import UserManager
from api.models import UserModel
from api.schemas.token import Token
from api.schemas.user import UserCreate, AuthorizedUser, UserAuthorization
from common.depends import Depends
from common.transaction import Transaction
from services import sql
from services.jwt_manager import jwt_manager

authorization_router = APIRouter(prefix='/admin')


class Admin(BaseModel):
    name: str
    surname: str
    password: str


@authorization_router.post(
    path='/',
    status_code=200,
    tags=['admin-authorization'],
    description='admin-authorization'
)
async def authorization(admin: Admin) -> Response:
    user_model = UserModel.get(
        sql, name=admin.name, surname=admin.surname, password=admin.password
    )
    if user_model is None:
        raise HTTPException(status_code=401, detail='Incorrect Data')

    token = jwt_manager.create_token(user_model)
    access_token = f"{token.token_type} {token.access_token}"

    response = Response()
    response.set_cookie('refresh_token', token.refresh_token)
    response.set_cookie('Authorization', access_token)

    return response


def user_registration(message: IncomingMessage) -> dict[str, Token | int]:
    payload = message.body.decode('utf8')
    user = UserCreate.parse_raw(payload)

    with Transaction(sql) as transaction:
        user_model = UserManager(transaction.sql).user_registration_handler(
            user
        )

    token = jwt_manager.create_token(user_model)

    return {
        'access_token': token.access_token,
        'refresh_token': token.refresh_token,
        'token_type': token.token_type,
        'user_id': user_model.id
    }


def user_authorization(message: IncomingMessage) -> Token:
    payload = message.body.decode('utf8')
    user = UserAuthorization.parse_raw(payload)

    with Transaction(sql) as transaction:
        user_model = UserManager(transaction.sql).user_authorization_handler(
            user
        )

    token = jwt_manager.create_token(user_model)
    return token


@Depends(jwt_manager.jwt_required)
def user_handler_action(message: IncomingMessage) -> bool:
    payload = jwt_manager.encode_token(message)
    authorized_user = AuthorizedUser.parse_obj(payload)

    with Transaction(sql) as transaction:
        user_manager = UserManager(transaction.sql)
        action = user_manager.get_action(message)
        is_action_valid = user_manager.is_action_valid(authorized_user, action)

    return is_action_valid


@Depends(jwt_manager.jwt_required)
def refresh_access_token(message: IncomingMessage) -> Token:
    return jwt_manager.refresh_token(message)
