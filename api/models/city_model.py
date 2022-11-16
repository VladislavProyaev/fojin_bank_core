from __future__ import annotations

from sqlalchemy import Column, String, Integer

from common.base_model import BaseModelInterface


class CityModel(BaseModelInterface):
    __tablename__ = 'city_model'
    sqlite_autoincrement = True

    id = Column(Integer, primary_key=True)
    city = Column(String(256))
