from __future__ import annotations

from typing import Any, TypeVar, Callable, Generic

from sqlalchemy.orm import registry, DeclarativeMeta

from common.constants.base_constant import BaseConstant
from services import sql

mapper_registry = registry()


class UnsuitableModel(Exception):
    ...


class ModelStatus(BaseConstant):
    attr_name: str = 'available'
    state: bool = False


class BaseModelInterface(metaclass=DeclarativeMeta):
    __abstract__ = True

    registry = mapper_registry
    metadata = mapper_registry.metadata

    def __init__(self, **kwargs) -> None:
        mapper_registry.constructor(self, **kwargs)

    @staticmethod
    def transaction(function: Callable) -> Callable:
        def make_transaction(*args, **kwargs) -> None:
            with sql.session.begin(subtransactions=True):
                function(*args, **kwargs)

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


_BMI = TypeVar('_BMI', bound=BaseModelInterface)


def get_clss(module: Any) -> list[type]:
    return [
        cls
        for name, cls in module.__dict__.items()
        if isinstance(cls, type)
    ]


def init_models(module: Any) -> None:
    clss = get_clss(module)
    for cls in clss:
        if isinstance(cls, type(BaseModelInterface)) and hasattr(cls, 'init'):
            cls.init()
