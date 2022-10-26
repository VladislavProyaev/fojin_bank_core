from __future__ import annotations

import sqlalchemy
from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from common.base_model import BaseModelInterface


class TokenModel(BaseModelInterface):
    __tablename__ = 'token_model'

    id = Column(BigInteger, primary_key=True)

    token = Column(
        UUID(),
        unique=True,
        index=True,
        nullable=False,
        default=sqlalchemy.text("uuid_generate_v4()")
    )

    expires = Column(TIMESTAMP)

    user_id = Column(
        BigInteger, ForeignKey('user_model.id', ondelete='CASCADE')
    )
    user = relationship('UserModel', uselist=False)
