from __future__ import annotations

from sqlalchemy import BigInteger, Column, String

from common.base_model import BaseModelInterface
from services import sql


class CityModel(BaseModelInterface):
    __tablename__ = 'city_model'

    id = Column(BigInteger, primary_key=True)
    city = Column(String(256))

    @staticmethod
    def get_or_create(city: str) -> CityModel:
        city = city.lower().capitalize()

        instance = sql.session.query(CityModel).filter(
            CityModel.city == city
        ).first()

        if instance is None:
            with sql.session.begin():
                instance = CityModel(city=city)
                sql.session.add(instance)

        return instance
