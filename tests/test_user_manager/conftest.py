import pytest
from sqlalchemy.util import FacadeDict

from api.models import UserModel
from api.schemas.user import UserCreate, UserAuthorization, AuthorizedUser
from common.base_model import BaseModelInterface
from common.constants.permissions import Permissions
from tests.test_user_manager.sample_users import sample_users
from services import SQL


@pytest.fixture(scope='session')
def sqlite_db() -> SQL:
    sql = SQL('sqlite://')
    return sql


@pytest.fixture(scope='session', autouse=True)
def create_tables(sqlite_db: SQL) -> None:
    new_tables = dict(BaseModelInterface.metadata.tables)
    for name, table in new_tables.items():
        table._init_existing(sqlite_autoincrement=True)

    BaseModelInterface.metadata.tables = FacadeDict(new_tables)
    BaseModelInterface.metadata.create_all(sqlite_db.client)


@pytest.fixture
def all_users_from_bd(sqlite_db: SQL) -> list[UserModel]:
    return sqlite_db.session.query(UserModel).all()


@pytest.fixture(scope='session')
def create_users_collection() -> list[UserCreate]:
    users = []
    for user in sample_users:
        users.append(UserCreate.parse_obj(user))
    return users


@pytest.fixture(scope='session')
def authorization_users_collection(
    create_users_collection: list[UserCreate]
) -> list[UserAuthorization]:
    users = []
    for user in sample_users:
        users.append(UserAuthorization.parse_obj(user))
    return users


@pytest.fixture
def permission_users_collection(
    all_users_from_bd: list[UserModel]
) -> list[tuple[AuthorizedUser, str]]:
    users = []
    for user in all_users_from_bd:
        user_permission = user.permissions[0].permission_type.permission_type
        actions = Permissions.get_permission(user_permission).permission_actions
        for action in actions:
            users.append((AuthorizedUser.from_orm(user), action))
    return users
