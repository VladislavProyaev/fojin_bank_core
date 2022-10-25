from typing import Any, TypeVar

from sqlalchemy.orm import registry, DeclarativeMeta

from common.model_interface import ModelInterface

mapper_registry = registry()


class BaseModelInterface(metaclass=DeclarativeMeta, ModelInterface):
    __abstract__ = True

    registry = mapper_registry
    metadata = mapper_registry.metadata

    __init__ = mapper_registry.constructor


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
