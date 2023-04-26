# dont need modes because operations can be raster/pixel independently
# question: how to track multiple things
# question: how to represent diagnostics (debugging)
import copy
from typing import Any
from functools import partial
import zvm.std
import zvm.state


def _start_routine(*, instr: list, args: list):
    zvm.state._routine_ops.append(copy.deepcopy(zvm.state.ops))
    zvm.state._routine_stacks.append(list(args))
    zvm.state._routine_instructions.append(instr)
    zvm.state.ops = zvm.state._routine_ops[-1]
    zvm.state.stack = zvm.state._routine_stacks[-1]
    zvm.state.instr = zvm.state._routine_instructions[-1]


def _end_routine():
    zvm.state._routine_ops.pop()
    rv = zvm.state._routine_stacks.pop()
    zvm.state._routine_instructions.pop()
    zvm.state.ops = zvm.state._routine_ops[-1]
    new_depth = len(zvm.state._routine_instructions)
    if new_depth > 0:
        zvm.state.stack = zvm.state._routine_stacks[-1]
        zvm.state.instr = zvm.state._routine_instructions[-1]
    else:
        zvm.state.stack = None
        zvm.state.instr = None
    return rv


def _load(*, code: dict = None):
    if code is not None:
        for op, func_def in code.get('defs', {}).items():
            if "eval" in func_def:
                feval = func_def.pop("eval")
                f = eval(feval)
            elif "exec" in func_def:
                fexec = func_def.pop("exec")
                fname = func_def.pop("name")
                exec(fexec)
                f = locals()[fname]
            elif "instr" in func_def:
                f = partial(_run, instr=func_def.pop("instr"), code=func_def.pop("code", None))
            else:
                f = None
            zvm.state.ops[op] = {'f': f, **func_def}
        for module in code.get("imports", []):
            exec(f"import {module}")


def _run(*args, instr: list = [], code: dict[str, Any] = None):
    _start_routine(instr=instr, args=args)
    _load(code=code)

    for ex in instr:
        if isinstance(ex, list):
            result = _run(instr=ex)
        elif isinstance(ex, dict):
            op = ex.pop('op', None)
            if op is not None:
                if op == 'run':
                    # anonymous routine
                    f = _run
                    n = ex.pop('n', 0)
                else:
                    f = zvm.state.ops[op].get("f")
                    n = zvm.state.ops[op].get("n", 0)
            else:
                f = None
                n = 0

            args = [zvm.state.stack.pop() for _ in range(n)][::-1]

            if f is not None:
                result = f(*args, **ex)
            else:
                # handle stack routine
                result = None
        else:
            result = ex

        if result is not None:
            if isinstance(result, list):
                zvm.state.stack.extend(result)
            else:
                zvm.state.stack.append(result)

    return _end_routine()


def run(routine: dict):
    return _run(instr=routine.pop("instr", []), code=routine.pop("code", None))
