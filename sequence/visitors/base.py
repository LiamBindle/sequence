import re
from dataclasses import dataclass, field
from typing import Union, Any
import sequence.static

from .state import State


@dataclass(frozen=True)
class Sequence:
    toolkits: list[str] = field(default_factory=list)
    include: dict[str, Union[str, dict]] = field(default_factory=dict)
    run: list[Any] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    tests: list[dict] = field(default_factory=list)


class Visitor:
    def _dereference(self, data: Union[str, list, dict]):
        if isinstance(data, str):
            if ref := re.match(r"^\$\{([a-zA-Z0-9\+\-\.]+):([^}]+)\}$", data):
                scheme = ref.group(1)
                uri = f'{scheme}:{ref.group(2)}'
                state = State(self)
                return sequence.static.getters[scheme][None](state, uri)
            else:
                return data
        elif isinstance(data, list):
            for i, v in enumerate(data):
                data[i] = self._dereference(v)
            return data
        elif isinstance(data, dict):
            for k, v in data.items():
                data[k] = self._dereference(v)
            return data
        else:
            return data

    def visit(self, sequence: 'Sequence'):
        pass
