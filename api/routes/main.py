from functools import wraps
from typing import Callable

from aio_pika import IncomingMessage
from fastapi import APIRouter

from api.schemas.token import Token
from api.schemas.user import UserCreate, AuthorizedUser
from api.support_functions.user_management import user_registration_handler, \
    get_current_user, is_action_valid
from services.jwt_manager import jwt_manager

main_router = APIRouter()


class Depends:
    def __init__(self, depends_function: Callable) -> None:
        self.depends_function = depends_function

    def __call__(self, function: Callable):
        @wraps(function)
        def wrapper(*args, **kwargs):
            self.depends_function(*args, **kwargs)
            function(*args, **kwargs)

        return wrapper


def user_registration(message: IncomingMessage) -> Token:
    payload = message.body.decode('utf8')
    user = UserCreate.parse_raw(payload)
    user_model = user_registration_handler(user)

    token = jwt_manager.create_token(user_model)

    return token


@Depends(jwt_manager.jwt_required)
def user_handler_action(message: IncomingMessage) -> bool:
    payload = jwt_manager.encode_access_token(message)

    authorized_user = AuthorizedUser.parse_raw(payload)
    user = get_current_user(authorized_user)

    return is_action_valid(user, message)
