import pytest

from api.behavior.user_manager import UserManager
from api.models import UserModel
from api.schemas.user import UserCreate, UserAuthorization, AuthorizedUser
from common.exceptions import UserManagementException
from services import SQL


def test_create_user(
    sqlite_db: SQL, create_users_collection: list[UserCreate]
):
    with UserManager(sqlite_db) as transaction:
        for user in create_users_collection:
            user_model = transaction.user_registration_handler(user)
            assert user_model.name == user.name
            assert user_model.surname == user.surname
            assert user_model.city.city == user.city
            assert user_model.phone == user.phone
            assert user_model.available is True


@pytest.mark.xfail(raises=UserManagementException, strict=True)
def test_again_create_user(
    sqlite_db: SQL, create_users_collection: list[UserCreate]
):
    with UserManager(sqlite_db) as transaction:
        for user in create_users_collection:
            transaction.user_registration_handler(user)


def test_get_user(
    sqlite_db: SQL, create_users_collection: list[UserCreate]
):
    for user in create_users_collection:
        user_model = UserModel.get(
            sqlite_db,
            name=user.name,
            surname=user.surname,
            phone=user.phone
        )
        assert user_model.city.city == user.city


def test_authorization(
    sqlite_db: SQL, authorization_users_collection: list[UserAuthorization]
):
    with UserManager(sqlite_db) as transaction:
        for user in authorization_users_collection:
            user_model = transaction.user_authorization_handler(user)
            assert user_model.name == user.name
            assert user_model.surname == user.surname
            assert user_model.phone == user.phone
            assert user_model.available is True


def test_delete_users(
    sqlite_db: SQL, all_users_from_bd: list[UserModel]
):
    for user in all_users_from_bd:
        user.delete(sqlite_db)
        assert user.available is False


def test_restore_users(
    sqlite_db: SQL, all_users_from_bd: list[UserModel]
):
    for user in all_users_from_bd:
        user.restore()
        assert user.available is True


def test_validate_action(
    sqlite_db: SQL,
    permission_users_collection: list[tuple[AuthorizedUser, str]]
):
    with UserManager(sqlite_db) as manager:
        for request in permission_users_collection:
            user = request[0]
            action = request[1]
            is_action_valid = manager.is_action_valid(user, action)
            assert is_action_valid is True
