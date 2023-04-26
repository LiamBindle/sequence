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
def start_routine(*, exe: list, n: int = 0):
    zvm.state._routine_ops.append(copy.deepcopy(zvm.state.ops))
    zvm.state._routine_stacks.append([zvm.state.stack.pop() for _ in range(n)][::-1])
    zvm.state._routine_exes.append(exe)
    zvm.state.ops = zvm.state._routine_ops[-1]
    zvm.state.stack = zvm.state._routine_stacks[-1]
    exe = zvm.state._routine_exes[-1]


@op
def end_routine():
    zvm.state._routine_ops.pop()
    rv = zvm.state._routine_stacks.pop()
    zvm.state._routine_exes.pop()
    zvm.state.ops = zvm.state._routine_ops[-1]
    new_depth = len(zvm.state._routine_exes)
    if new_depth > 0:
        zvm.state.stack = zvm.state._routine_stacks[-1]
        zvm.state.exe = zvm.state._routine_exes[-1]
    else:
        zvm.state.stack = None
        zvm.state.exe = None
    return rv


@op
def load(*, code: dict[str, Any] = None):
    if code is not None:
        for op, func_def in code.pop("defs", {}).items():
            if "feval" in func_def:
                feval = func_def.pop("feval")
                f = eval(feval)
            elif "fexec" in func_def:
                fexec = func_def.pop("fexec")
                fname = func_def.pop("fname")
                exec(fexec)
                f = locals()[fname]
            else:
                f = None
            zvm.state.ops[op] = {'f': f, **func_def}
        for module in code.pop("imports", []):
            exec(f"import {module}")


@op
def eval_(*, exe: list = [], code: dict[str, Any] = None, n: int = 0):
    zvm.state.ops['start_routine']['f'](exe=exe, n=n)
    zvm.state.ops['load']['f'](code=code)

    for ex in exe:
        if isinstance(ex, list):
            result = zvm.state.ops['eval']['f'](exe=ex)
        elif isinstance(ex, dict):
            op = ex.pop('op', None)
            if op is not None:
                f = zvm.state.ops[op].get("f")
                n = zvm.state.ops[op].get("n", 0)
            else:
                f = None
                n = 0

            args = [zvm.state.stack.pop() for _ in range(n)][::-1]

            if f is not None:
                result = f(*args, **ex)
            else:
                result = None
        else:
            result = ex

        if result is not None:
            if isinstance(result, list):
                zvm.state.stack.extend(result)
            else:
                zvm.state.stack.append(result)

    return zvm.state.ops['end_routine']['f']()


@op
def if_(cond, /, *, true, false):
    return true if cond else false
