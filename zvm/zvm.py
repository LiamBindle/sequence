from typing import List, Any, Union, Callable
from dataclasses import dataclass, field
import copy
import importlib
import urllib.parse
import re
import datetime


# static variables for keeping track of user functions registered by imports
_static_ops: dict[str, Union[dict, Callable]] = {}
_static_loaders: dict[str, dict[str, Callable]] = {}
_static_storers: dict[str, dict[str, Callable]] = {}
_static_deleters: dict[str, dict[str, Callable]] = {}


class State:
    def __init__(self, vm: 'ZVM', op_frame: 'OpFrame') -> None:
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

    def set(self, key: str, value: Any):
        self._set[key] = value

    def has(self, key) -> bool:
        return key in self._set

    def get(self, key: str) -> Any:
        if key not in self._set:
            raise RuntimeError(f"Variable has not been set: {key}")
        return self._set[key]


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
    _run: List[Union[str, dict]]
    _pc: int = 0
    _begins: List[int] = field(default_factory=list)

    def run(self, vm: 'ZVM'):
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
                    # op is an op
                    child = OpFrame(
                        _set=copy.copy(self._set),
                        _name=name,
                        _parent=self,
                        _run=op.get("run", [])
                    )
                    op_set = copy.copy(op.get("set", {}))
                    child._set.update(op_set)

                    child.run(vm=vm)
                    result = None  # child.run will have updated the stack
                elif callable(op):
                    # op is a function
                    result = op(state, **{k: v for k, v in ex.items() if k != "op"})
            else:
                # is a literal
                print_console_update(state, "put")
                result = ex

            if isinstance(result, list):
                vm._stack.extend(result)
            elif result is not None:
                vm._stack.append(result)

            self._pc += 1


@dataclass
class ZVM:
    _root_frame: OpFrame
    _started_at: datetime = field(default_factory=datetime.datetime.utcnow)
    _stack: List[Any] = field(default_factory=list)
    _globals: dict[str, Any] = field(default_factory=dict)

    def _include(self, name: str, url_or_op: Union[str, dict]):
        if isinstance(url_or_op, str):
            url = urllib.parse.urlparse(url_or_op)
            data = _static_loaders[url.scheme]['application/json'](url_or_op)
        elif isinstance(url_or_op, dict):
            data = url_or_op
        else:
            raise RuntimeError("include is not a url (str) or an op (dict)")
        _static_ops[name] = data

        for module in data.get("import", []):
            importlib.import_module(module)
        for name, url_or_op in data.get("include", {}).items():
            self._include(name, url_or_op)


def run(op: dict, init_stack: list = None):
    import zvm.std
    vm = ZVM(OpFrame(op.get("set", {}), "root", None, op.get("run", [])))
    if init_stack is not None:
        vm._stack.extend(init_stack)
    vm._include("root", op)
    vm._root_frame.run(vm)
    return vm._stack


def test(op: dict, tests_matching_re: str = None):
    tests: dict = op.get("tests", [])
    checks_passed = 0
    for test in tests:
        test_name = test.get("name", "unnamed-test")
        if tests_matching_re is not None and not re.match(tests_matching_re, test_name):
            continue

        init_stack = test.get("setup", [])
        result = run(op, init_stack=init_stack)

        if "checks" in test:
            for i, check in enumerate(test["checks"]):
                if "answer" in check:
                    assert result == check['answer'], f"check {i} of test '{test_name}' failed"
                    checks_passed += 1
    return checks_passed


def op(name):
    def inner(func: Callable):
        if func.__code__.co_argcount != 1:
            raise RuntimeError("function must take exactly one position argument (state: zvm.State)")
        _static_ops[name] = func
        return func
    return inner


def loader(*, schemes: str | list[str], media_type: str):
    global _static_loaders
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: Callable):
        global _static_loaders
        if func.__code__.co_argcount != 1:
            raise RuntimeError("function must take exactly one position argument (url: str)")
        for scheme in schemes:
            if scheme not in _static_loaders:
                _static_loaders[scheme] = {}
            _static_loaders[scheme][media_type] = func
        return func
    return inner


def storer(*, schemes: str | list[str], media_type: str):
    global _static_storers
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: Callable):
        global _static_storers
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position argument (data: Any, url: str)")
        for scheme in schemes:
            if scheme not in _static_storers:
                _static_storers[scheme] = {}
            _static_storers[scheme][media_type] = func
        return func
    return inner


def deleter(*, schemes: str | list[str], media_type: str = None):
    global _static_deleters
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: Callable):
        global _static_deleters
        if func.__code__.co_argcount != 1:
            raise RuntimeError("function must take exactly one position argument (url: str)")
        for scheme in schemes:
            if scheme not in _static_deleters:
                _static_deleters[scheme] = {}
            _static_deleters[scheme][media_type] = func
        return func
    return inner
