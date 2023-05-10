# dont need modes because operations can be raster/pixel independently
# question: how to track multiple things
# question: how to represent diagnostics (debugging)
import copy
import re
from typing import Any
from urllib.parse import urlparse
from functools import partial
import sys

import importlib
import zvm.state
import zvm.std


def _start_routine(*, instr: list, args: list, includes: list, conf: dict):
    # push new frame
    zvm.state._routine_ops.append(copy.copy(zvm.state.ops))
    zvm.state._routine_stacks.append(list(args[::-1]))
    zvm.state._routine_instructions.append(instr)
    zvm.state._routine_confs.append(copy.copy(zvm.state.conf))
    zvm.state._routine_imports.append(copy.copy(zvm.state._routine_imports[-1]))
    zvm.state._routine_begin_stacks.append([])
    zvm.state._routine_pc.append(0)
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
        loader = zvm.state.loaders[url.scheme]['application/json']
        data = loader(include)
        zvm.state.conf.update(data.get('conf', {}))
        if 'instr' in data:
            zvm.state.instr = data['instr']
        code.update(data.get('code', {}))

    # load code
    if code:
        _load(code=code)


def _end_routine():
    zvm.state._routine_ops.pop()
    rv = zvm.state._routine_stacks.pop()
    zvm.state._routine_instructions.pop()
    zvm.state._routine_confs.pop()
    zvm.state._routine_imports.pop()
    zvm.state._routine_pc.pop()
    begin_stack = zvm.state._routine_begin_stacks.pop()
    assert len(begin_stack) == 0, "Begin stack is not empty"
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
    # is subroutine decides if the routine should be called with its own stack or operate in the calling stack (idea: to facilitate routines like foreach which wrap "break" and "repeat")
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
        elif "uri" in func_def:
            uri = urlparse(func_def['uri'])
            loader = zvm.state.loaders[uri.scheme]['application/json']
            zvm.state.ops[op] = loader(func_def['uri'])
            continue
        else:
            raise RuntimeError(f"The definition of routine '{op}' is missing its definition")
        zvm.state.ops[op] = {'f': f, **func_def}
    for module in code.get("imports", []):
        import_module = module not in sys.modules
        reload_module = (not import_module) and (module not in zvm.state._routine_imports[-1])
        if import_module:
            # exec(f"import {module}")
            importlib.import_module(module)
        elif reload_module:
            importlib.reload(sys.modules[module])
        zvm.state._routine_imports[-1].add(module)


def _run(*args, instr: list = [], code: dict[str, Any] = {}, conf: dict = {}, includes: list[str] = []):
    _start_routine(instr=instr, args=args, conf=conf, includes=includes)
    if code:
        _load(code=code)

    while zvm.state._routine_pc[-1] < len(zvm.state.instr):
        ex = copy.copy(zvm.state.instr[zvm.state._routine_pc[-1]])
        if isinstance(ex, list):
            result = _run(instr=ex)
            result_reversed = False
        elif isinstance(ex, dict) and 'op' in ex:
            ex = copy.copy(ex)
            op = ex.pop('op')

            # start zvm.call -- runs function in current stack
            if op == 'run':
                # anonymous routine
                f = _run
                n = ex.pop('n', 0)
                result_reversed = False
            else:
                f = zvm.state.ops[op].get("f")
                n = zvm.state.ops[op].get("n", 0)
                result_reversed = True

            argc = ex.pop("argc", None)
            if argc is not None:
                n = argc

            args = [zvm.state.stack.pop() for _ in range(n)]

            result = f(*args, **ex)
        else:
            result = ex
            result_reversed = False

        if result is not None:
            if isinstance(result, list):
                if result_reversed:
                    zvm.state.stack.extend(reversed(result))
                else:
                    zvm.state.stack.extend(result)  # types should be wrapped in a custom type (for custom repr, hash, etc.)
            else:
                zvm.state.stack.append(result)
        zvm.state._routine_pc[-1] += 1

    return _end_routine()


def run(routine: dict):
    routine = copy.deepcopy(routine)
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
        setup_code = copy.deepcopy(routine.get("code", {}))
        test_routine = {
            "instr": [
                {"op": "run", "code":  setup_code, "instr": [test.get("setup", [])]},
                {"op": "run", **routine}
            ]
        }
        result = run(test_routine)
        assert zvm.state.finished, f"test '{test_name}' failed to finish"

        if "checks" in test:
            for i, check in enumerate(test["checks"]):
                if "eq" in check:
                    eq_routine = {
                        "instr": [
                            check["eq"]
                        ]
                    }
                    answer = run(eq_routine)
                    assert zvm.state.finished, f"eq routine of test '{test_name}' failed to finish"
                    assert result == answer, f"check {i} of test '{test_name}' failed"
                    checks_passed += 1
    return checks_passed
