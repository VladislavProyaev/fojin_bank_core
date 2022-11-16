from aio_pika import IncomingMessage

from api.behavior.user_manager import UserManager
from api.schemas.token import Token
from api.schemas.user import UserCreate, AuthorizedUser, UserAuthorization
from common.depends import Depends
from services import sql
from services.jwt_manager import jwt_manager


def user_registration(message: IncomingMessage) -> Token:
    payload = message.body.decode('utf8')
    user = UserCreate.parse_raw(payload)

    with UserManager(sql) as transaction:
        user_model = transaction.user_registration_handler(user)

    token = jwt_manager.create_token(user_model)

    return token


def user_authorization(message: IncomingMessage) -> Token:
    payload = message.body.decode('utf8')
    user = UserAuthorization.parse_raw(payload)

    with UserManager(sql) as transaction:
        user_model = transaction.user_authorization_handler(user)

    token = jwt_manager.create_token(user_model)

    return token


@Depends(jwt_manager.jwt_required)
def user_handler_action(message: IncomingMessage) -> bool:
    payload = jwt_manager.encode_token(message)
    authorized_user = AuthorizedUser.parse_obj(payload)

    with UserManager(sql) as transaction:
        action = transaction.get_action(message)
        is_action_valid = transaction.is_action_valid(authorized_user, action)

    return is_action_valid


@Depends(jwt_manager.jwt_required)
def refresh_access_token(message: IncomingMessage) -> Token:
    return jwt_manager.refresh_token(message)
