from __future__ import annotations

from sqlalchemy import BigInteger, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Boolean

from common.base_model import BaseModelInterface


class PermissionUserModel(BaseModelInterface):
    __tablename__ = 'permission_user_model'

    id = Column(Integer, primary_key=True)

    user_id = Column(
        BigInteger, ForeignKey('user_model.id', ondelete='CASCADE')
    )
    user = relationship('UserModel', uselist=False, backref='permissions')

    permission_type_id = Column(
        BigInteger, ForeignKey('permission_type_model.id', ondelete='CASCADE')
    )
    permission_type = relationship(
        'PermissionTypeModel', uselist=False, backref='users'
    )

    available = Column(Boolean, default=True)
