# dont need modes because operations can be raster/pixel independently
# question: how to track multiple things
# question: how to represent diagnostics (debugging)
import copy
import re
from typing import Any
from urllib.parse import urlparse
from functools import partial
import importlib
import zvm.state
import zvm.std


def _start_routine(*, instr: list, args: list, includes: list, conf: dict):
    # push new frame
    zvm.state._routine_ops.append(copy.deepcopy(zvm.state.ops))
    zvm.state._routine_stacks.append(list(args))
    zvm.state._routine_instructions.append(instr)
    zvm.state._routine_confs.append(copy.deepcopy(zvm.state.conf))
    # update frame pointers
    zvm.state.ops = zvm.state._routine_ops[-1]
    zvm.state.stack = zvm.state._routine_stacks[-1]
    zvm.state.instr = zvm.state._routine_instructions[-1]
    zvm.state.conf = zvm.state._routine_confs[-1]

    # handle conf
    zvm.state.conf.update(conf)

    code: dict = {}
    # handle includes
    for include in includes:
        url = urlparse(include)
        fetcher = zvm.state.fetchers[url.scheme]['application/json']
        data = fetcher(include)
        zvm.state.conf.update(data.get('conf', {}))
        if 'instr' in data:
            zvm.state.instr = data['instr']
        code.update(data.get('code', {}))

    # load code
    _load(code=code)


def _end_routine():
    zvm.state._routine_ops.pop()
    rv = zvm.state._routine_stacks.pop()
    zvm.state._routine_instructions.pop()
    zvm.state._routine_confs.pop()
    zvm.state.ops = zvm.state._routine_ops[-1]
    zvm.state.conf = zvm.state._routine_confs[-1]
    new_depth = len(zvm.state._routine_instructions)
    if new_depth > 0:
        zvm.state.stack = zvm.state._routine_stacks[-1]
        zvm.state.instr = zvm.state._routine_instructions[-1]
    else:
        zvm.state.stack = None
        zvm.state.instr = None
    return rv


def _load(*, code: dict = {}):
    # handle setup/teardown
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
            f = partial(
                _run,
                instr=func_def.pop("instr", []),
                code=func_def.pop("code", {}),
                conf=func_def.pop("conf", {}),
                includes=func_def.pop("includes", [])
            )
        else:
            f = None
        zvm.state.ops[op] = {'f': f, **func_def}
    for module in code.get("imports", []):
        exec(f"import {module}")


def _run(*args, instr: list = [], code: dict[str, Any] = {}, conf: dict = {}, includes: list[str] = []):
    # setup/teardown
    _start_routine(instr=instr, args=args, conf=conf, includes=includes)
    _load(code=code)

    for ex in zvm.state.instr:
        if isinstance(ex, list):
            result = _run(instr=ex)
        elif isinstance(ex, dict):
            op = ex.pop('op', None)

            # start zvm.call -- runs function in current stack
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

            argc = ex.pop("argc", None)
            if argc is not None:
                n = argc

            args = [zvm.state.stack.pop() for _ in range(n)][::-1]

            if f is not None:
                result = f(*args, **ex)
            else:
                # todo: is this needed?
                result = None

            # end zvm.call
        else:
            result = ex

        if result is not None:
            if isinstance(result, list):
                zvm.state.stack.extend(result)  # types should be wrapped in a custom type (for custom repr, hash, etc.)
            else:
                zvm.state.stack.append(result)

    return _end_routine()


def run(routine: dict):
    zvm.state.restart()
    importlib.reload(zvm.std)
    result = _run(
        instr=routine.pop("instr", []),
        code=routine.pop("code", {}),
        conf=routine.pop("conf", {}),
        includes=routine.pop("includes", [])
    )
    zvm.state.finished = True
    return result


def run_test(routine: dict, name: str = None) -> int:
    tests: dict = routine.pop("tests", [])
    checks_passed = 0
    for test in tests:
        test_name = test.get("name", "unnamed-test")
        if name is not None and not re.match(name, test_name):
            continue
        test_routine = {
            "instr": [
                test.get("setup", []),
                {"op": "run", **routine}
            ]
        }
        result = run(test_routine)[::-1]
        assert zvm.state.finished, f"test {test_name} failed to finish"

        if "checks" in test:
            for i, check in enumerate(test["checks"]):
                if "eq" in check:
                    eq_routine = {
                        "instr": [
                            check["eq"]
                        ]
                    }
                    answer = run(eq_routine)[::-1]
                    assert zvm.state.finished, f"eq routine of test {test_name} failed to finish"
                    assert result == answer, f"check {i} of test {test_name} failed"
                    checks_passed += 1
    return checks_passed
