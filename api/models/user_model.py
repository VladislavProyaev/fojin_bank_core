from __future__ import annotations

from dataclasses import dataclass
from typing import overload

from sqlalchemy import BigInteger, Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Boolean

from api.models.city_model import CityModel
from common.base_model import BaseModelInterface
from services import sql


@dataclass
class UserCommonGet:
    name: str
    surname: str
    phone: int
    city: str


@dataclass
class UserIDGet:
    user_model_id: int


class UserModel(BaseModelInterface):
    __tablename__ = 'user_model'

    id = Column(BigInteger, primary_key=True)

    name = Column(String(256))
    surname = Column(String(256))

    phone = Column(BigInteger)

    city_id = Column(
        BigInteger, ForeignKey('city_model.id', ondelete='CASCADE')
    )
    city = relationship('CityModel', uselist=False, backref='cities')

    available = Column(Boolean, default=True)

    @staticmethod
    @overload
    def get_or_create(user_info: UserCommonGet) -> UserModel:
        ...

    @staticmethod
    @overload
    def get_or_create(user_info: UserIDGet) -> UserModel | None:
        ...

    @staticmethod
    def get_or_create(
        user_info: UserCommonGet | UserIDGet
    ) -> UserModel:
        if isinstance(user_info, UserCommonGet):
            with sql.session.begin():
                city = CityModel.get_or_create(city=user_info.city)

                instance = UserModel(
                    name=user_info.name,
                    surname=user_info.surname,
                    phone=user_info.phone,
                    city=city
                )
                sql.session.add(instance)
        else:
            instance = sql.session.query(UserModel).filter(
                CityModel.id == user_info.user_model_id
            ).first()

        return instance
