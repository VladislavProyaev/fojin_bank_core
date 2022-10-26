import hashlib
import random
import string
from datetime import datetime, timedelta

from api import UserModel, CityModel
from api.models import TokenModel
from api.schemas.user import UserCreate, TokenBase


def get_salt(length: int = 12) -> str:
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


def hash_password(password: str, salt: str = None) -> str:
    if salt is None:
        salt = get_salt()

    hashed_password = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100_000
    )
    return hashed_password.hex()


def validate_password(password: str, hashed_password: str) -> bool:
    salt, hashed = hashed_password.split("$")
    return hash_password(password, salt) == hashed


def get_user_by_token(token: str) -> UserModel | None:
    token_model = TokenModel.get(token=token)
    if token_model is None:
        raise Exception('User not found!')

    return token_model.user


async def create_user(user: UserCreate) -> TokenBase:
    salt = get_salt()
    hashed_password = hash_password(user.password, salt)

    city = CityModel.get_or_create(city=user.city)

    user_model = UserModel.get_or_create(
        name=user.name,
        surname=user.surname,
        phone=user.phone,
        city=city,
        hashed_password=f'{salt}${hashed_password}'
    )

    token_model = TokenModel.get_or_create(
        expires=datetime.now() + timedelta(weeks=2), user=user_model
    )

    token_response = TokenBase(
        token=token_model.token,
        expires=token_model.expires,

    )

    return token_response
