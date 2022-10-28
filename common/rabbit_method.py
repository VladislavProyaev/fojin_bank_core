from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True)
class RabbitMQMethod:
    method_name: str
    method_function: Callable
