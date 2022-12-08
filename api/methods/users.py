from aio_pika import IncomingMessage
from fastapi import APIRouter, HTTPException

from api.behavior.user_manager import UserManager
from api.models import UserModel
from api.schemas.token import Token
from api.schemas.user import UserCreate, AuthorizedUser, UserAuthorization, \
    User, TransferUser
from common.depends import Depends
from common.transaction import Transaction
from services import sql
from services.jwt_manager import jwt_manager

authorization_router = APIRouter(prefix='/auth')


@authorization_router.post(
    path='/',
    status_code=200,
    tags=['admin-authorization'],
    description='admin-authorization'
)
async def authorization(user: User) -> dict[str, str]:
    user_model = UserModel.get(
        sql, name=user.name, surname=user.surname
    )

    if user_model is None:
        raise HTTPException(status_code=401, detail='Incorrect Name/Surname')

    user_model_password = jwt_manager.verify_password(
        user.password, user_model.password
    )
    if not user_model_password:
        raise HTTPException(status_code=401, detail='Incorrect Password')

    token = jwt_manager.create_token(user_model)

    return {
        'access_token': token.access_token,
        'refresh_token': token.refresh_token
    }


@authorization_router.post(
    path='/upgrade',
    status_code=200,
    tags=['admin-upgrade-to-moderator'],
    description='admin-upgrade-to-moderator'
)
async def upgrade(user: TransferUser) -> dict[str, str]:
    user_model = UserModel.get(
        sql, name=user.name, surname=user.surname
    )
    if user_model is None:
        raise HTTPException(status_code=401, detail='Incorrect Name/Surname')

    with Transaction(sql) as transaction:
        UserManager(transaction.sql).user_permission_handler(
            user_model, 'upgrade'
        )

    return {'status': 'ok'}


@authorization_router.post(
    path='/downgrade',
    status_code=200,
    tags=['admin-downgrade-to-client'],
    description='admin-downgrade-to-client'
)
async def downgrade(user: TransferUser) -> dict[str, str]:
    user_model = UserModel.get(
        sql, name=user.name, surname=user.surname
    )
    if user_model is None:
        raise HTTPException(status_code=401, detail='Incorrect Name/Surname')

    with Transaction(sql) as transaction:
        UserManager(transaction.sql).user_permission_handler(
            user_model, 'downgrade'
        )

    return {'status': 'ok'}


@authorization_router.post(
    path='/user/registration',
    status_code=201,
    tags=['user-registration'],
    description='user-registration'
)
def registration(user: UserCreate) -> dict[str, str]:
    with Transaction(sql) as transaction:
        UserManager(transaction.sql).user_registration_handler(user)

    return {'status': 'ok'}


@authorization_router.post(
    path='/user/authorization',
    status_code=200,
    tags=['user-authorization'],
    description='user-authorization'
)
def authorization(user: UserAuthorization) -> dict[str, str]:
    with Transaction(sql) as transaction:
        t_sql = transaction.sql
        user_model = UserManager(t_sql).user_authorization_handler(user)

    token = jwt_manager.create_token(user_model)
    return {
        'access_token': token.access_token,
        'refresh_token': token.refresh_token
    }


def get_user(message: IncomingMessage) -> dict[str, Token | int]:
    encode_token = jwt_manager.encode_token(message)
    user_id = encode_token.get('id')
    with Transaction(sql) as transaction:
        t_sql = transaction.sql
        user_model = UserManager(t_sql).get_user(user_id)

    return {'user_id': user_model.id}


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
def user_super_permission(message: IncomingMessage) -> bool:
    payload = jwt_manager.encode_token(message)
    authorized_user = AuthorizedUser.parse_obj(payload)

    with Transaction(sql) as transaction:
        is_action_valid = (
            UserManager(transaction.sql).is_super_permission(authorized_user)
        )

    return is_action_valid


@Depends(jwt_manager.jwt_required)
def refresh_access_token(message: IncomingMessage) -> Token:
    return jwt_manager.refresh_token(message)
