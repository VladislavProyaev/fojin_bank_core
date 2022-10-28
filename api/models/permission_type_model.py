from __future__ import annotations

from sqlalchemy import BigInteger, Column, String

from common.base_model import BaseModelInterface


class PermissionTypeModel(BaseModelInterface):
    __tablename__ = 'permission_type_model'

    id = Column(BigInteger, primary_key=True)

    permission_type = Column(String(256))
