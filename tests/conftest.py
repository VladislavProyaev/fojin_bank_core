import pytest

from api.schemas.user import UserCreate
from services import sql


@pytest.fixture(scope='session', name='session')
def session_transaction() -> None:
    connection = sql.client.connect()
    transaction = connection.begin()
    session = sql.session

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def cities_collection() -> list[str]:
    return ['New York', 'Moscow', 'Rostov-on-Don']


@pytest.fixture
def permission_types_collection() -> list[str]:
    return ['Admin', 'Moderator', 'User']


@pytest.fixture
def users_collection() -> list[UserCreate]:
    return [
        UserCreate(
            name='A',
            surname='B',
            phone='123',
            city='C',
            password='123',
            permission='D'
        ),
        UserCreate(
            name='E',
            surname='F',
            phone='456',
            city='G',
            password='456',
            permission='H'
        )
    ]
