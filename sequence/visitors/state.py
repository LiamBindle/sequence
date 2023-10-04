import datetime
from typing import Any


class State:
    def __init__(self, frame) -> None:
        # frame is a visitor -- usually a sequence runner
        self._frame = frame
        self._started_at = datetime.datetime.utcnow()

    def push(self, value: Any):
        self._frame.stack.append(value)

    def pop(self) -> Any:
        if len(self._frame.stack) == 0:
            raise RuntimeError("Cannot pop from empty stack")
        return self._frame.stack.pop()

    def popn(self, n: int) -> tuple[Any]:
        if n > len(self._frame.stack):
            raise RuntimeError("Cannot pop from empty stack")
        return tuple([self._frame.stack.pop() for _ in range(n)][::-1])

    def set(self, key: str, value: Any):
        self._frame.variables[key] = value

    def has(self, key) -> bool:
        return key in self._frame.variables

    def get(self, key: str) -> Any:
        if key not in self._frame.variables:
            raise RuntimeError(f"Variable has not been set: {key}")
        return self._frame.variables[key]

    def delete(self, key):
        del self._frame.variables[key]
