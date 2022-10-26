from __future__ import annotations

from sqlalchemy import BigInteger, Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Boolean

from common.base_model import BaseModelInterface


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

    hashed_password = Column(String())

    available = Column(Boolean, default=True)
