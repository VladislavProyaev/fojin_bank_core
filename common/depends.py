from functools import wraps
from typing import Callable


class Depends:
    def __init__(self, depends_function: Callable) -> None:
        self.depends_function = depends_function

    def __call__(self, function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args, **kwargs) -> None:
            self.depends_function(*args, **kwargs)
            return function(*args, **kwargs)

        return wrapper
