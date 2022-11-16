import json
from json import JSONDecodeError

from aio_pika import IncomingMessage

from api.models import PermissionTypeModel, PermissionUserModel, UserModel, \
    CityModel
from api.schemas.user import UserCreate, AuthorizedUser, UserAuthorization
from common.base_manager import BaseManager
from common.constants.permissions import Permissions
from common.exceptions import UserManagementException, CoreException
from services.jwt_manager import jwt_manager


class UserManager(BaseManager):

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

        permission_type = PermissionTypeModel.get_or_create(
            self.sql, permission_type=user.permission
        )
        PermissionUserModel.get_or_create(
            self.sql, user=user_model, permission_type=permission_type
        )

        return user_model

    def user_registration_handler(self, user: UserCreate) -> UserModel:
        user_model = UserModel.get(
            self.sql, name=user.name, surname=user.surname
        )
        if user_model is not None:
            raise UserManagementException('This user already registered"')

        all_phones = self.sql.session.query(UserModel.phone).all()
        if user.phone in all_phones:
            raise UserManagementException('Phone is already in use')

        password = jwt_manager.get_password_hash(user.password)
        user_model = self.__create_user(user, password)

        return user_model

    def user_authorization_handler(self, user: UserAuthorization) -> UserModel:
        if user.password is None:
            raise UserManagementException(
                'Authorization is not possible without a password'
            )
        if (
            (user.name is not None and user.surname is None)
            or (user.name is None and user.surname is not None)
            or (
                user.name is None
                and user.surname is None
                and user.phone is None
            )
        ):
            raise UserManagementException(
                f'Incorrect authorization data: '
                f'Name: {user.name} | Surname: {user.surname} '
                f'| Phone: {user.phone}'
            )

        if user.phone is not None:
            user_model = UserModel.get(self.sql, phone=user.phone)
        else:
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

    @staticmethod
    def __get_user_permission(user_model: UserModel) -> PermissionUserModel:
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
