import sqlalchemy.orm

from api import CityModel, UserModel
from api.models import PermissionTypeModel
from api.schemas.user import UserCreate


def test_create_city_model(
    session: sqlalchemy.orm.Session, cities_collection: list[str]
):
    for city in cities_collection:
        city_model = CityModel.get_or_create(city=city)
        assert city_model.city == city


def test_permission_type_model(
    session: sqlalchemy.orm.Session, permission_types_collection: list[str]
):
    for permission_type in permission_types_collection:
        permission_type_model = PermissionTypeModel.get_or_create(
            permission_type=permission_type
        )
        assert permission_type_model.permission_type == permission_type


def test_user_model(
    session: sqlalchemy.orm.Session, users_collection: list[UserCreate]
):
    for user in users_collection:
        city_model = CityModel.get_or_create(city=user.city)
        user_model = UserModel.get_or_create(
            name=user.name,
            surname=user.surname,
            phone=user.phone,
            city_id=city_model.id,
            password=user.password
        )

        assert user_model.name == user.name
        assert user_model.surname == user.surname
        assert user_model.phone == user.phone
        assert city_model.city == user.city
        assert user_model.password == user.password
