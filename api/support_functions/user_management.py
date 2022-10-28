"""
In the future, I made into classes, but for now, just funcs
"""
import json
from json import JSONDecodeError

from aio_pika import IncomingMessage

from api import UserModel, CityModel
from api.models import PermissionTypeModel, PermissionUserModel
from api.schemas.user import UserCreate, AuthorizedUser
from common.constants.permissions import Permissions
from common.exceptions import UserManagementException, CoreException
from services import sql
from services.jwt_manager import jwt_manager


def create_user(user: UserCreate, password: str) -> UserModel:
    """
    Redesign in future
    """
    try:
        city = CityModel.get_or_create(city=user.city)

        user_model = UserModel.get_or_create(
            name=user.name,
            surname=user.surname,
            phone=user.phone,
            city_id=city.id,
            password=password
        )

        permission_type = PermissionTypeModel.get_or_create(
            permission_type=user.permission
        )
        PermissionUserModel.get_or_create(
            user_id=user_model.id,
            permission_type_id=permission_type.id
        )
    except Exception:
        sql.session.rollback()
        raise Exception('Something went wrong! Please, try again!')

    return user_model


def user_registration_handler(user: UserCreate) -> UserModel:
    user_model = UserModel.get(
        name=user.name, surname=user.surname
    )
    if user_model is not None:
        raise UserManagementException('This user already registered"')

    all_phones = sql.session.query(UserModel.phone).all()
    if user.phone in all_phones:
        raise UserManagementException('Phone is already in use')

    password = jwt_manager.get_password_hash(user.password)
    user_model = create_user(user, password)

    return user_model


def get_current_user(authorized_user: AuthorizedUser) -> UserModel:
    user_model = UserModel.get(
        name=authorized_user.name,
        surname=authorized_user.surname,
        phone=authorized_user.phone,
        city_id=authorized_user.city_id,
        password=authorized_user.password
    )
    return user_model


def get_user_permission(user_model: UserModel) -> PermissionUserModel:
    user_permissions: list[PermissionUserModel] = [
        permission for permission in user_model.permissions
        if permission.available
    ]
    return user_permissions[0]


def is_action_valid(user_model: UserModel, message: IncomingMessage) -> bool:
    message_payload = message.body.decode('utf8')
    try:
        action = json.loads(message_payload)['action']
    except (JSONDecodeError, KeyError):
        raise CoreException('Incorrect action credentials!')

    user_permission = get_user_permission(user_model)
    permission = Permissions.get_permission(
        user_permission.permission_type.permission_type
    )

    if action in permission.permission_actions:
        return True

    return False
