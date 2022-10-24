from typing import Any

from sqlalchemy.orm import registry, DeclarativeMeta

mapper_registry = registry()


class BaseModelInterface(metaclass=DeclarativeMeta):
    __abstract__ = True

    registry = mapper_registry
    metadata = mapper_registry.metadata

    __init__ = mapper_registry.constructor


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
