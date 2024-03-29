from __future__ import annotations

from sqlalchemy import BigInteger, Column, String

from common.base_model import BaseModelInterface


class CityModel(BaseModelInterface):
    __tablename__ = 'city_model'

    id = Column(BigInteger, primary_key=True)
    city = Column(String(256))
