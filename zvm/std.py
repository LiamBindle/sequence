import inspect
import copy
from typing import Any

import zvm.state


def op(func: callable):
    name: str = func.__name__
    name = name.strip("_")
    signature = inspect.signature(func)
    # validate expression
    n = 0
    for param_name, param_value in signature.parameters.items():
        if param_value.kind == inspect.Parameter.POSITIONAL_ONLY:
            n += 1
            assert param_value.default == inspect.Parameter.empty, f"definition of '{func.__name__}' sets a default value for the positional argument '{param_name}' (not allowed)"
        else:
            break
    zvm.state.ops[name] = {'f': func, "n": n}
    return func


@op
def if_(cond, /, *, true, false):
    return true if cond else false


@op
def assert_(*, start: int = None, end: int = None, step: int = 1, size: int = None, eq: list = None, neq: list = None):
    if start is None:
        start = -1
    else:
        start = -start - 1
    if end is not None:
        end = -end - 1

    values = zvm.state.stack[start:end:-step]
    if size is not None:
        assert len(values) == size
    if eq is not None:
        assert values == eq
    if neq is not None:
        assert values != neq
