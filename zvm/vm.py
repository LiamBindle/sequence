# dont need modes because operations can be raster/pixel independently
# question: how to track multiple things
# question: how to represent diagnostics (debugging)
import copy
import re
from typing import Any, Union, List
from urllib.parse import urlparse
from functools import partial
import sys
from dataclasses import dataclass

import importlib
import zvm.state
import zvm.std
import datetime


# def print_console_update(name, local_vars: dict):
#     lpad = "  " * (len(zvm.state._routine_pc) - 1)
#     rpad = " " * max(0, 10 - len(lpad))
#     if local_vars.get("logging", True):
#         pc_str = f"{zvm.state._routine_pc[-1]:02d}"[-2:]
#         name = name[-12:]
#         elapsed = datetime.datetime.utcnow() - zvm.state.start_datetime
#         t = elapsed.total_seconds()
#         seconds = t % 60
#         minutes = int(t//60) % 60
#         hours = int(t//3600)
#         elapsed = ""
#         if hours:
#             elapsed += f"{hours:d}h"
#         if minutes:
#             elapsed += f"{minutes: 2d}m"
#         elapsed += f"{seconds: 6.3f}"[:6] + "s"
#         print(f"{lpad}{pc_str}{rpad} {len(zvm.state.stack):2d} {name:14s}{elapsed:>18s}")


# def _start_routine(*, ops: list, args: list, includes: list, local_vars: dict):
#     # push new frame
#     zvm.state._routine_ops.append(copy.copy(zvm.state.ops))
#     zvm.state._routine_stacks.append(list(args))
#     zvm.state._routine_instructions.append(ops)
#     zvm.state._routine_locals.append(copy.copy(zvm.state.local_vars))
#     zvm.state._routine_imports.append(copy.copy(zvm.state._routine_imports[-1]))
#     zvm.state._routine_begin_stacks.append([])
#     zvm.state._routine_pc.append(0)
#     # update frame pointers
#     zvm.state.ops = zvm.state._routine_ops[-1]
#     zvm.state.stack = zvm.state._routine_stacks[-1]
#     zvm.state.ops = zvm.state._routine_instructions[-1]
#     zvm.state.local_vars = zvm.state._routine_locals[-1]

#     # handle locals
#     zvm.state.local_vars.update(local_vars)

#     code: dict = {}
#     # handle includes


#     # load code
#     if code:
#         _load(code=code)


# def _end_routine():
#     zvm.state._routine_ops.pop()
#     rv = zvm.state._routine_stacks.pop()
#     zvm.state._routine_instructions.pop()
#     zvm.state._routine_locals.pop()
#     zvm.state._routine_imports.pop()
#     zvm.state._routine_pc.pop()
#     begin_stack = zvm.state._routine_begin_stacks.pop()
#     assert len(begin_stack) == 0, "Begin stack is not empty"
#     zvm.state.ops = zvm.state._routine_ops[-1]
#     zvm.state.local_vars = zvm.state._routine_locals[-1]
#     new_depth = len(zvm.state._routine_instructions)
#     if new_depth > 0:
#         zvm.state.stack = zvm.state._routine_stacks[-1]
#         zvm.state.ops = zvm.state._routine_instructions[-1]
#     else:
#         zvm.state.stack = None
#         zvm.state.ops = None
#     return rv


def fetch_op(url: str):
    url = urlparse(url)
    loader = zvm.state.loaders[url.scheme]['application/json']
    op = loader(url)
    return op
    # for module in data.get("imports", []):
    #     importlib.import_module(module)

    # ops.update(data.get("ops", {}))
    # local_vars.update(data.get("local_vars", {}))
    # for url in data.get("includes", []):
    #     include(url, ops, local_vars)







#     def start(self, run: list):



#         while self._frames[-1]._pc < len(run):
#             ex = copy.copy(run[self._frames[-1]._pc])
#             if isinstance(ex, dict):
#                 # is op
#                 if "op" not in ex:
#                     raise RuntimeError("operation is missing 'op' key")
#                 op = self._ops[ex["op"]]

#                 if isinstance(op, dict):
#                     # add frame
#                     pass
#                 elif callable(op):
#                     result = op()
#             else:
#                 result = ex


#             if isinstance(ex, list):
#                 print_console_update("", local_vars)
#                 result = _run(ops=ex, local_vars=local_vars)
#             elif isinstance(ex, dict) and 'op' in ex:
#                 ex = copy.copy(ex)
#                 op = ex.pop('op')
#                 print_console_update(op, local_vars)

#                 # start zvm.call -- runs function in current stack
#                 if op == 'run':
#                     # anonymous routine
#                     f = _run
#                     n = ex.pop('n', 0)
#                     if 'locals' in ex:
#                         # rename locals -> local_vars
#                         ex['local_vars'] = ex.pop('locals')
#                 else:
#                     f = zvm.state.ops[op].get("f")
#                     n = zvm.state.ops[op].get("n", 0)

#                 argc = ex.pop("argc", None)
#                 if argc is not None:
#                     n = argc

#                 args = [zvm.state.stack.pop() for _ in range(n)][::-1]

#                 result = f(*args, **ex)
#             else:
#                 print_console_update("put", local_vars)
#                 result = ex

#             if result is not None:
#                 if isinstance(result, list):
#                     zvm.state.stack.extend(result)
#                 else:
#                     zvm.state.stack.append(result)
#             zvm.state._routine_pc[-1] += 1

#         return _end_routine()






# def include(url_or_op: Union[str, dict], _import: list = [], _set: dict[str, Any] = {}, state: State):
#     for module in _import:
#         importlib.import_module(module)

#     if isinstance(url_or_op, str):
#         url = url_or_op
#         loader = zvm.state.loaders[url.scheme]['application/json']
#         op = loader(url)
#     elif isinstance(url_or_op, dict):
#         op = url_or_op
#         pass
#     else:
#         raise RuntimeError("include is not a url or an op")

#     _set # current set. need to copy into next include

#     for name, _url_or_op in op.get("include", {}):

#         include()






# def run(_include: dict[str, Union[str, dict]] = {}, _import: list = [], _set: dict[str, Any] = {}, _run: list[Any]):
#     for name, include in _include.items():
#         if isinstance(include, str):
#             url = include

#             loader = zvm.state.loaders[url.scheme]['application/json']
#             data = loader(url)


#         elif isinstance(include, dict):
#             data = include
#             pass


# def _run(*args, imports: list = [], ops: dict[str, Any] = {}, local_vars: dict[str, Any] = {}, includes: dict[str, str] = []):
#     _start_routine(ops=ops, args=args, local_vars=local_vars, includes=includes)

#     for module in imports:
#         importlib.import_module(module)

#     for url, ns_url in includes.items():




#         zvm.state.local_vars.update(data.get('locals', {}))
#         if 'ops' in data:
#             zvm.state.ops = data['ops']
#         code.update(data.get('code', {}))


#         _load(code=code)

#     while zvm.state._routine_pc[-1] < len(zvm.state.ops):
#         ex = copy.copy(zvm.state.ops[zvm.state._routine_pc[-1]])
#         if isinstance(ex, list):
#             print_console_update("", local_vars)
#             result = _run(ops=ex, local_vars=local_vars)
#         elif isinstance(ex, dict) and 'op' in ex:
#             ex = copy.copy(ex)
#             op = ex.pop('op')
#             print_console_update(op, local_vars)

#             # start zvm.call -- runs function in current stack
#             if op == 'run':
#                 # anonymous routine
#                 f = _run
#                 n = ex.pop('n', 0)
#                 if 'locals' in ex:
#                     # rename locals -> local_vars
#                     ex['local_vars'] = ex.pop('locals')
#             else:
#                 f = zvm.state.ops[op].get("f")
#                 n = zvm.state.ops[op].get("n", 0)

#             argc = ex.pop("argc", None)
#             if argc is not None:
#                 n = argc

#             args = [zvm.state.stack.pop() for _ in range(n)][::-1]

#             result = f(*args, **ex)
#         else:
#             print_console_update("put", local_vars)
#             result = ex

#         if result is not None:
#             if isinstance(result, list):
#                 zvm.state.stack.extend(result)
#             else:
#                 zvm.state.stack.append(result)
#         zvm.state._routine_pc[-1] += 1

#     return _end_routine()


# def run2(routine: dict):
#     timestamp = datetime.datetime.utcnow().strftime('%F%T.%f')[:-2] + 'Z'
#     local_vars = routine.pop("locals", {})
#     if local_vars.get("logging", True):
#         print(f"""--- Starting zvm at {timestamp} ---""")
#     routine = copy.deepcopy(routine)
#     zvm.state.restart()
#     importlib.reload(zvm.std)
#     result = _run(
#         ops=routine.pop("ops", []),
#         code=routine.pop("code", {}),
#         local_vars=local_vars,
#         includes=routine.pop("includes", [])
#     )
#     zvm.state.finished = True
#     if local_vars.get("logging", True):
#         timestamp = datetime.datetime.now().strftime('%F %T.%f')[:-3] + 'Z'
#         result_size_str = f"{len(result):2d}"[-2:] if result is not None else "-"
#         print(f"{' ' * 12} {result_size_str} {timestamp:>32s}\n")
#     return result


# def run2_test(routine: dict, name: str = None) -> int:
#     tests: dict = routine.pop("tests", [])
#     checks_passed = 0
#     for test in tests:
#         test_name = test.get("name", "unnamed-test")
#         if name is not None and not re.match(name, test_name):
#             continue
#         setup_code = copy.deepcopy(routine.get("code", {}))
#         test_routine = {
#             "code": {
#                 "defs": {
#                     "setup_test": {"code":  setup_code, "ops": [test.get("setup", [])], "locals": {"logging": False}}
#                 }
#             },
#             "ops": [
#                 {"op": "setup_test"},
#                 {"op": "run", **routine}
#             ]
#         }
#         result = run(test_routine)
#         assert zvm.state.finished, f"test '{test_name}' failed to finish"

#         if "checks" in test:
#             for i, check in enumerate(test["checks"]):
#                 if "eq" in check:
#                     eq_routine = {
#                         "locals": {'logging': False},
#                         "ops": [
#                             check["eq"]
#                         ]
#                     }
#                     answer = run(eq_routine)
#                     assert zvm.state.finished, f"eq routine of test '{test_name}' failed to finish"
#                     assert result == answer, f"check {i} of test '{test_name}' failed"
#                     checks_passed += 1
#     return checks_passed
