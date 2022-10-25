from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Callable

from common.constants.base_constant import BaseConstant
from services import sql

if TYPE_CHECKING:
    from common.base_model import _BMI


class UnsuitableModel(Exception):
    ...


class ModelStatus(BaseConstant):
    attr_name: str = 'available'
    state: bool = False


class ModelInterface:
    def __init__(self, **kwargs) -> None:
        pass

    @staticmethod
    def transaction(function: Callable) -> Callable:
        def make_transaction() -> None:
            with sql.session.begin():
                function()

        return make_transaction

    @staticmethod
    def generate_filters(cls, **kwargs) -> list[bool]:
        return [
            getattr(cls, attr) == value for attr, value in kwargs.items()
        ]

    @classmethod
    def get(cls, **kwargs) -> Generic[_BMI]:
        filters = cls.generate_filters(cls, **kwargs)
        instance = sql.session.query(cls).filter(*filters).first()

        return instance

    @classmethod
    @transaction
    def get_or_create(cls, **kwargs) -> Generic[_BMI]:
        instance = cls.get(**kwargs)

        if instance is None:
            instance = cls(**kwargs)
            sql.session.add(instance)

        return instance

    @transaction
    def delete(self) -> None:
        if hasattr(self, ModelStatus.attr_name):
            setattr(self, ModelStatus.attr_name, ModelStatus.state)
        else:
            self_type = type(self)
            sql.session.query(self_type).filter(
                getattr(self_type, 'id') == getattr(self, 'id')
            ).delete()

    @transaction
    def restore(self) -> None:
        if hasattr(self, ModelStatus.attr_name):
            if getattr(self, ModelStatus.attr_name) is ModelStatus.state:
                setattr(self, ModelStatus.attr_name, True)
                return

        raise UnsuitableModel(
            f'{type(self)} does not have the ability to switch the '
            f'"available" state'
        )
