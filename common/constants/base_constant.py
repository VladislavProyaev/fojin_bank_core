from typing import TypeVar

_BC_V = TypeVar('_BC_V')


class BaseConstant:
    @classmethod
    def values(cls) -> list[_BC_V]:
        constant_list = []
        for name_attr, value_attr in cls.__dict__.items():
            if name_attr.isupper():
                constant_list.append(value_attr)

        return constant_list
