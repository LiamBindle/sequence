from typing import List, Any, Union, Callable
from dataclasses import dataclass, field
import copy
import importlib
import urllib.parse
import re
import datetime
import ast
import sys
import urllib.request
import urllib.parse


_static_ops: dict[str, Union[dict, Callable]] = {}
_static_getters: dict[str, dict[str, Callable]] = {}
_static_putters: dict[str, dict[str, Callable]] = {}
_static_deleters: dict[str, dict[str, Callable]] = {}
_static_copiers = {}


class State:
    def __init__(self, vm: 'VirtualMachine', op_frame: 'OpFrame') -> None:
        self._stack = vm._stack
        self._set = op_frame._set
        self._op_frame = op_frame
        self._vm = vm

    def push(self, value: Any):
        self._stack.append(value)

    def pop(self) -> Any:
        if len(self._stack) == 0:
            raise RuntimeError("Cannot pop from empty stack")
        return self._stack.pop()

    def popn(self, n: int) -> List[Any]:
        if n > len(self._stack):
            raise RuntimeError("Cannot pop from empty stack")
        return [self._stack.pop() for _ in range(n)][::-1]

    def set(self, key: str, value: Any, global_var: bool = False):
        if global_var:
            self._vm._globals[key] = value
        else:
            self._set[key] = value

    def has(self, key, global_var: bool = False) -> bool:
        if global_var:
            return key in self._vm._globals
        else:
            return key in self._set

    def get(self, key: str, global_var: bool = False) -> Any:
        if global_var:
            if key not in self._vm._globals:
                raise RuntimeError(f"Global variable has not been set: {key}")
            return self._vm._globals[key]
        else:
            if key not in self._set:
                raise RuntimeError(f"Global variable has not been set: {key}")
            return self._set[key]

    def delete(self, key, global_var: bool = False):
        if global_var:
            del self._vm._globals[key]
        else:
            del self._set[key]

    @staticmethod
    def op(name) -> Union[dict, Callable]:
        return _static_ops[name]

    def _dereference(self, data: Union[str, list, dict]):
        if isinstance(data, str):
            if ref := re.match(r"^\$\{([a-zA-Z0-9\+\-\.]+):([^}]+)\}$", data):
                scheme = ref.group(1)
                uri = f'{scheme}:{ref.group(2)}'
                return _static_getters[scheme][None](self, uri)
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


def calc_depth(state: State) -> int:
    depth = 0
    frame = state._op_frame
    parent = frame._parent
    while parent is not None:
        parent = parent._parent
        depth += 1
    return depth


def print_console_update(state: State, name):
    lpad = "  " * calc_depth(state)
    rpad = " " * max(0, 10 - len(lpad))
    if not state.has("logging") or (state.has("logging") and state.get("logging")):
        pc_str = f"{state._op_frame._pc:02d}"[-2:]
        name = name[-12:]
        elapsed = datetime.datetime.utcnow() - state._vm._started_at
        t = elapsed.total_seconds()
        seconds = t % 60
        minutes = int(t//60) % 60
        hours = int(t//3600)
        elapsed = ""
        if hours:
            elapsed += f"{hours:d}h"
        if minutes:
            elapsed += f"{minutes: 2d}m"
        elapsed += f"{seconds: 6.3f}"[:6] + "s"
        print(f"{lpad}{pc_str}{rpad} {len(state._vm._stack):3d} {name:14s}{elapsed:>18s}")


@dataclass
class OpFrame:
    _set: dict[str, Any]
    _name: str
    _parent: 'OpFrame'
    _run: List[Union[str, dict]] = None
    _pc: int = None
    _begins: List[int] = field(default_factory=list)
    _next_params: dict = field(default_factory=dict)
    _parameters: dict = field(default_factory=dict)

    def run(self, vm: 'VirtualMachine', _run: List[Union[str, dict]]):
        self._run = _run
        self._pc = 0
        while self._pc < len(self._run):
            ex = self._run[self._pc]
            state = State(vm, self)

            # execute expression
            if isinstance(ex, dict) and "op" in ex:
                # is an op
                name = ex['op']
                op = _static_ops[name]
                print_console_update(state, name)

                if isinstance(op, dict):
                    params = self._next_params
                    missing_parameters = []
                    for param_name, param_def in op.get("metadata", {}).get("parameters", {}).items():
                        required_param = param_def.get("optional", False) or ("default" not in param_def)
                        if required_param and param_name not in ex and param_name not in params:
                            missing_parameters.append(param_name)
                        if param_name in ex:
                            params[param_name] = ex[param_name]
                        elif param_name in params:
                            # e.g., set by _next_params
                            pass
                        elif "default" in param_def:
                            params[param_name] = param_def["default"]
                    if missing_parameters:
                        raise TypeError(f'procedure "{name}" missing {len(missing_parameters)} required keyword-only argument: {", ".join([f"{p}" for p in param_name])}')
                    self._next_params = {}
                    params = state._dereference(params)

                    # op is an op
                    child = OpFrame(
                        _set=copy.copy(self._set),
                        _name=name,
                        _parent=self,
                        _parameters=params,
                    )
                    op_set = copy.copy(op.get("set", {}))
                    child._set.update(op_set)
                    op_run = op.get("run", [])
                    child.run(vm, op_run)
                    result = None  # child.run will have updated the stack
                elif callable(op):
                    # op is a function
                    params = self._next_params
                    params.update({k: v for k, v in ex.items() if k != "op"})
                    params = state._dereference(params)
                    self._next_params = {}
                    result = op(state, **params)
            else:
                # is a literal
                print_console_update(state, "put")
                result = ex

            if isinstance(result, list):
                vm._stack.extend(result)
            elif result is not None:
                vm._stack.append(result)

            self._pc += 1


class VirtualMachine:
    def __init__(self, init_stack: list = None) -> None:
        import sequence.standard
        self._root_frame: OpFrame = OpFrame({}, "root", None)
        self._started_at = datetime.datetime.utcnow()
        self._stack = init_stack if init_stack is not None else []
        self._globals = {}

    @property
    def stack(self) -> List[Any]:
        return self._stack

    def _include(self, name: str, url_or_op: Union[str, dict], *, parameters: dict = None, breadth_first_callback: Callable = None, depth_first_callback: Callable = None):
        global _static_ops
        if parameters:
            self._root_frame._parameters = parameters
        state = State(self, self._root_frame)
        if isinstance(url_or_op, str):
            url_or_op = state._dereference(url_or_op)
        if isinstance(url_or_op, str):
            url = urllib.parse.urlparse(url_or_op)
            if url.path.endswith(".json5"):
                data = _static_getters[url.scheme]['application/json5'](state, url_or_op)
            elif url.path.endswith(".hjson"):
                data = _static_getters[url.scheme]['application/hjson'](state, url_or_op)
            else:
                data = _static_getters[url.scheme]['application/json'](state, url_or_op)

            # breadth-first callback
            if breadth_first_callback:
                breadth_first_callback(url_or_op)

        elif isinstance(url_or_op, dict):
            data = url_or_op
        else:
            raise RuntimeError("include is not a url (str) or an op (dict)")
        _static_ops[name] = data

        self._import(data.get("import", []))
        for name, url_or_op in data.get("include", {}).items():
            self._include(name, url_or_op, breadth_first_callback=breadth_first_callback, depth_first_callback=depth_first_callback)

        # depth-first callback
        if depth_first_callback:
            depth_first_callback(url_or_op)

    def _import(self, imports: list):
        for module in imports:
            importlib.import_module(module)

    def eval(self, line: str, parameters: dict = None):
        url = urllib.parse.urlparse(line)
        if line.startswith("import "):
            self._import([line.removeprefix("import ")])
        elif bool(url.scheme) and bool(url.path):
            state = State(self, self._root_frame)
            if url.path.endswith(".json5"):
                op = _static_getters[url.scheme]['application/json5'](state, line)
            elif url.path.endswith(".hjson"):
                op = _static_getters[url.scheme]['application/hjson'](state, line)
            else:
                op = _static_getters[url.scheme]['application/json'](state, line)
            self.exec(op, parameters=parameters)
        else:
            op = ast.literal_eval(line)
            self._root_frame.run(self, [op])

    def exec(self, op: dict[str, Any], parameters: dict = None):
        if parameters:
            self._root_frame._parameters.update(parameters)
        self._import(op.get("import", []))
        for name, url_or_op in op.get("include", {}).items():
            self._include(name, url_or_op)
        self._root_frame._set.update(op.get("set", {}))
        self._root_frame.run(self, op.get("run", []))

    def repl(self):
        def readline():
            line = sys.stdin.readline()
            while line:
                yield line
                line = sys.stdin.readline()
        for line in readline():
            self.eval(line)

    def run(self, url: str):
        self.eval(url)


def test(op: dict, tests_matching_re: str = None):
    tests: dict = op.get("tests", [])
    checks_passed = 0
    for test in tests:
        test_name = test.get("name", "unnamed-test")
        if tests_matching_re is not None and not re.match(tests_matching_re, test_name):
            continue
        init_stack = test.get("setup", [])
        vm = VirtualMachine(init_stack=init_stack)
        vm.exec(op)
        if "checks" in test:
            for i, check in enumerate(test["checks"]):
                if "answer" in check:
                    assert vm.stack == check['answer'], f"check {i} of test '{test_name}' failed"
                    checks_passed += 1
    return checks_passed


def method(name):
    global _static_ops
    def inner(func: Callable):
        global _static_ops
        if func.__code__.co_argcount != 1:
            raise RuntimeError("function must take exactly one position argument (state: svm.State)")
        _static_ops[name] = func
        return func
    return inner


def getter(*, schemes: Union[str, list[str]], media_type: str):
    global _static_getters
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: Callable):
        global _static_getters
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position arguments (state: svm.State, url: str)")
        for scheme in schemes:
            if scheme not in _static_getters:
                _static_getters[scheme] = {}
            _static_getters[scheme][media_type] = func
        return func
    return inner


def putter(*, schemes: Union[str, list[str]], media_type: str):
    global _static_putters
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: Callable):
        global _static_putters
        if func.__code__.co_argcount != 3:
            raise RuntimeError("function must take exactly three position argument (state: svm.State, data: Any, url: str)")
        for scheme in schemes:
            if scheme not in _static_putters:
                _static_putters[scheme] = {}
            _static_putters[scheme][media_type] = func
        return func
    return inner


def deleter(*, schemes: Union[str, list[str]], media_type: str = None):
    global _static_deleters
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: Callable):
        global _static_deleters
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position argument (state: svm.State, url: str)")
        for scheme in schemes:
            if scheme not in _static_deleters:
                _static_deleters[scheme] = {}
            _static_deleters[scheme][media_type] = func
        return func
    return inner


def copier(*, types: Union[type, List[type]]):
    global _static_copiers
    if isinstance(types, type):
        types = [types]

    def inner(func: Callable):
        global _static_copiers
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position argument (data: object, deep: bool)")
        for t in types:
            _static_copiers[t] = func
        return func
    return inner





























# notes:
# - there needs to be a place to store metadata in the op (e.g., model name, provider name for QGIS model, details about inputs/outputs)
