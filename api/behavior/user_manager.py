import json
from json import JSONDecodeError

from aio_pika import IncomingMessage

from api.models import PermissionTypeModel, PermissionUserModel, UserModel, \
    CityModel
from api.schemas.user import UserCreate, AuthorizedUser, UserAuthorization
from common.constants.permissions import Permissions
from common.exceptions import UserManagementException, CoreException
from services import SQL
from services.jwt_manager import jwt_manager

BASE_PERMISSION = Permissions.CLIENT.permission_type


class UserManager:

    def __init__(self, sql: SQL) -> None:
        self.sql = sql

    def __create_user(self, user: UserCreate, password: str) -> UserModel:
        city = CityModel.get_or_create(self.sql, city=user.city)

        user_model = UserModel.get_or_create(
            self.sql,
            name=user.name,
            surname=user.surname,
            phone=user.phone,
            city=city,
            password=password
        )

        permission_type = PermissionTypeModel.get(
            self.sql, permission_type=BASE_PERMISSION
        )
        PermissionUserModel.get_or_create(
            self.sql,
            user_id=user_model.id,
            permission_type_id=permission_type.id,
            available=True
        )

        return user_model

    def user_registration_handler(self, user: UserCreate) -> UserModel:
        user_model = UserModel.get(
            self.sql, name=user.name, surname=user.surname
        )
        if user_model is not None:
            raise UserManagementException('This user already registered')

        all_phones = self.sql.session.query(UserModel.phone).all()
        if user.phone in all_phones:
            raise UserManagementException('Phone is already in use')

        password = jwt_manager.get_password_hash(user.password)
        user_model = self.__create_user(user, password)

        return user_model

    def user_authorization_handler(self, user: UserAuthorization) -> UserModel:
        user_model = UserModel.get(
            self.sql, name=user.name, surname=user.surname
        )

        if user_model is None:
            raise UserManagementException('The user was not found!')

        if not jwt_manager.verify_password(user.password, user_model.password):
            raise UserManagementException('Incorrect login or password!')

        return user_model

    def __get_current_user(self, authorized_user: AuthorizedUser) -> UserModel:
        user_model = UserModel.get(
            self.sql,
            name=authorized_user.name,
            surname=authorized_user.surname,
            phone=authorized_user.phone,
            city_id=authorized_user.city_id,
            password=authorized_user.password
        )
        return user_model

    def get_user(self, user_id: int) -> UserModel:
        user_model = UserModel.get(self.sql, id=user_id)
        if user_model is None:
            raise Exception('User not found')

        return user_model

    def __get_user_permission(
        self,
        user_model: UserModel
    ) -> PermissionUserModel:
        user_permissions = PermissionUserModel.get(
            self.sql, user_id=user_model.id, available=True
        )
        print(user_permissions, 'HERE')
        user_permissions: list[PermissionUserModel] = [
            permission for permission in user_model.permissions
            if permission.available
        ]
        return user_permissions[0]

    @staticmethod
    def get_action(message: IncomingMessage) -> str:
        message_payload = message.body.decode('utf8')
        try:
            action = json.loads(message_payload)['action']
            return action
        except (JSONDecodeError, KeyError):
            raise CoreException('Incorrect action credentials!')

    def is_action_valid(
        self, authorized_user: AuthorizedUser, action: str
    ) -> bool:
        user_model = self.__get_current_user(authorized_user)
        user_permission = self.__get_user_permission(user_model)
        permission = Permissions.get_permission(
            user_permission.permission_type.permission_type
        )
        if action in permission.permission_actions:
            return True

        return False
