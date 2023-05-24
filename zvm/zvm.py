from typing import List, Any, Union, Callable, Generator
from dataclasses import dataclass, field
import copy
import importlib
import urllib.parse
import re
import datetime
import ast
import sys
import json
import requests
import urllib.parse
import json
import copy
import string
import pathlib


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
            raise RuntimeError(f"Global variable has not been set: {key}")
        return self._set[key]

    @staticmethod
    def op(name) -> Union[dict, Callable]:
        return _static_ops[name]

    def set_global(self, key: str, value: Any):
        self._vm._globals[key] = value

    def has_global(self, key) -> bool:
        return key in self._vm._globals

    def get_global(self, key: str) -> Any:
        if key not in self._vm._globals:
            raise RuntimeError(f"Global variable has not been set: {key}")
        return self._vm._globals[key]


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

    def run(self, vm: 'ZVM', _run: List[Union[str, dict]]):
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
                    # op is an op
                    child = OpFrame(
                        _set=copy.copy(self._set),
                        _name=name,
                        _parent=self,
                    )
                    op_set = copy.copy(op.get("set", {}))
                    child._set.update(op_set)
                    op_run = op.get("run", [])
                    child.run(vm, op_run)
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


class ZVM:
    def __init__(self, init_stack: list = None) -> None:
        self._root_frame: OpFrame = OpFrame({}, "root", None)
        self._started_at = datetime.datetime.utcnow()
        self._stack = init_stack if init_stack is not None else []
        self._globals = {}

    @property
    def stack(self) -> List[Any]:
        return self._stack

    def _include(self, name: str, url_or_op: Union[str, dict]):
        global _static_ops
        if callable(url_or_op):
            print('here')
        if isinstance(url_or_op, str):
            url = urllib.parse.urlparse(url_or_op)
            data = _static_loaders[url.scheme]['application/json'](self, url_or_op)
        elif isinstance(url_or_op, dict):
            data = url_or_op
        else:
            raise RuntimeError("include is not a url (str) or an op (dict)")
        _static_ops[name] = data

        self._import(data.get("import", []))
        for name, url_or_op in data.get("include", {}).items():
            self._include(name, url_or_op)

    def _import(self, imports: list):
        for module in imports:
            importlib.import_module(module)

    def eval(self, line: str):
        url = urllib.parse.urlparse(line)
        if line.startswith("import "):
            self._import([line.removeprefix("import ")])
        elif bool(url.scheme) and bool(url.netloc):
            op = _static_loaders[url.scheme]['application/json'](self, line)
            self.exec(op)
        else:
            op = ast.literal_eval(line)
            self._root_frame.run(self, [op])

    def exec(self, op: dict[str, Any]):
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
        vm = ZVM(init_stack=init_stack)
        vm.exec(op)
        if "checks" in test:
            for i, check in enumerate(test["checks"]):
                if "answer" in check:
                    assert vm.stack == check['answer'], f"check {i} of test '{test_name}' failed"
                    checks_passed += 1
    return checks_passed


def op(name):
    global _static_ops
    def inner(func: Callable):
        global _static_ops
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
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position arguments (state: zvm.State, url: str)")
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
        if func.__code__.co_argcount != 3:
            raise RuntimeError("function must take exactly three position argument (state: zvm.State, data: Any, url: str)")
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
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position argument (state: zvm.State, url: str)")
        for scheme in schemes:
            if scheme not in _static_deleters:
                _static_deleters[scheme] = {}
            _static_deleters[scheme][media_type] = func
        return func
    return inner


# operators
@op("/")
def divide(state: State):
    x, y = state.popn(2)
    return x / y


@op("*")
def multiply(state: State):
    x, y = state.popn(2)
    return x * y


@op("-")
def minus(state: State):
    x, y = state.popn(2)
    return x - y


@op("+")
def plus(state: State):
    x, y = state.popn(2)
    return x + y


@op("%")
def mod(state: State):
    x, y = state.popn(2)
    return x % y


# bool ops
@op("not")
def not_(state: State):
    x = state.pop()
    return not x


@op("and")
def and_(state: State):
    x, y = state.popn(2)
    return x and y


@op("or")
def or_(state: State):
    x, y = state.popn(2)
    return x or y


@op("xor")
def xor_(state: State):
    x, y = state.popn(2)
    return bool(x) != bool(y)


@op("asbool")
def asbool_(state: State):
    x = state.pop()
    return bool(x)


@op("asint")
def asint_(state: State):
    x = state.pop()
    return int(x)


@op("asfloat")
def asfloat_(state: State):
    x = state.pop()
    return float(x)


# comparison
@op("eq")
def equal(state: State):
    x, y = state.popn(2)
    return x == y


@op("neq")
def not_equal(state: State):
    x, y = state.popn(2)
    return x != y


@op("gt")
def greater_than(state: State):
    x, y = state.popn(2)
    return x > y


@op("ge")
def greater_than_or_equal_to(state: State):
    x, y = state.popn(2)
    return x >= y


@op("lt")
def less_than(state: State):
    x, y = state.popn(2)
    return x < y


@op("le")
def less_than_or_equal_to(state: State):
    x, y = state.popn(2)
    return x <= y


# stack ops
@op("dup")
def duplicate(state: State, *, deep: bool = False, offset: int = 0):
    offset = -1 - offset
    item = state._stack[offset]
    if deep:
        return copy.deepcopy(item)
    else:
        return copy.copy(item)


@op("swap")
def swap(state: State):
    x, y = state.popn(2)
    return [y, x]


@op("drop")
def drop(state: State):
    state.pop()


@op("reorder")
def reorder(state: State, *, order: list = []):
    size = len(order)
    items = state.popn(size)
    new_items = [items[size-1-i] for i in order]
    return new_items


@op("size")
def stack_size(state: State):
    return len(state._stack)


# looping
@op("begin")
def begin_(state: State):
    state._op_frame._begins.append(state._op_frame._pc)


@op("repeat")
def repeat_(state: State):
    state._op_frame._pc = state._op_frame._begins[-1]


@op("break")
def break_(state: State):
    nested_loops = 0
    pc = state._op_frame._pc
    while pc < len(state._op_frame._run):
        pc += 1
        ex = state._op_frame._run[pc]
        if not isinstance(ex, dict):
            continue
        if 'op' not in ex:
            continue
        op = ex["op"]
        if op == 'begin':  # or any loop-start
            nested_loops += 1
        elif op == 'repeat':  # or any loop-end
            if nested_loops == 0:
                state._op_frame._pc = pc
                state._op_frame._begins.pop()
                return
            else:
                nested_loops -= 1

    # continue until repeat
    raise RuntimeError("Unterminated begin statement")


@op("recurse")
def recurse(state: State):
    state._op_frame._pc = -1


# branching
@op("if")
def if_(state: State):
    cond = state.pop()
    if cond:
        return
    # set PC to address to else/endif
    nested_branches = 0
    pc = state._op_frame._pc
    while pc < len(state._op_frame._run):
        pc += 1
        ex = state._op_frame._run[pc]
        if not isinstance(ex, dict):
            continue
        if 'op' not in ex:
            continue
        op = ex["op"]
        if op == 'if':
            nested_branches += 1
        elif nested_branches == 0 and (op == 'else' or op == 'endif'):
            state._op_frame._pc = pc
            return
        elif op == 'endif':
            nested_branches -= 1

    raise RuntimeError("Unterminated if statement")


@op("else")
def else_(state: State):
    # set PC to address to else/endif
    nested_branches = 0
    pc = state._op_frame._pc
    while pc < len(state._op_frame._run):
        pc += 1
        ex = state._op_frame._run[pc]
        if not isinstance(ex, dict):
            continue
        if 'op' not in ex:
            continue
        op = ex["op"]
        if op == 'if':
            nested_branches += 1
        elif op == 'else':
            if nested_branches == 0:
                raise RuntimeError("Unbound else")
            else:
                nested_branches -= 1
        elif op == 'endif' and nested_branches == 0:
            state._op_frame._pc = pc
            return
    raise RuntimeError("Unterminated if statement")


@op("endif")
def endif_(state: State):
    # noop
    pass


# state
@op("load")
def load(state: State, *, uri: str, mediaType: str = None, **kwargs):
    global _static_loaders
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_loader = _static_loaders[parsed_uri.scheme][mediaType]
    return uri_media_loader(state, uri, **kwargs)


@op("store")
def store(state: State, *, uri: str, mediaType: str = None, **kwargs):
    global _static_storers
    data = state.pop()
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_storer = _static_storers[parsed_uri.scheme][mediaType]
    uri_media_storer(state, data, uri, **kwargs)


@op("delete")
def delete(state: State, *, uri: str, mediaType: str = None, **kwargs):
    global _static_deleters
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_deleter = _static_deleters[parsed_uri.scheme][mediaType]
    uri_media_deleter(state, uri, **kwargs)

# misc


@op("fstring")
def format_string(state: State, *, fmt: str, **kwargs):
    formatter = string.Formatter()
    parsed_fmt = formatter.parse(fmt)
    format_nargs = 0
    format_kwargs = set()
    for (_, field_name, _, _) in parsed_fmt:
        if field_name is None:
            # no replacement field
            continue
        if field_name == '' or field_name.isnumeric():
            format_nargs += 1
        else:
            format_kwargs.add(field_name)
    args = state.popn(format_nargs)
    return fmt.format(*args, **kwargs)


@op("assert")
def assert_(state: State, *, error: str = '', negate: bool = False):
    x = state.pop()
    if negate:
        assert not x, error
    else:
        assert x, error


@loader(schemes=['http', 'https'], media_type='application/json')
def fetch_json_http(state: State, url: str):
    response = requests.get(url=url)
    return response.json()


@loader(schemes=['file'], media_type='application/json')
def fetch_json_file(state: State, url: str):
    path = urllib.parse.urlparse(url).path
    with open(path, 'r') as f:
        data = json.load(f)
    return data


@storer(schemes=['file'], media_type='application/json')
def store_json_file(state: State, data, uri: str):
    path = urllib.parse.urlparse(uri).path
    with open(path, 'w') as f:
        json.dump(data, f)


@deleter(schemes=['file'])
def delete_generic_file(state: State, uri: str, *, missing_ok: bool = False):
    path = urllib.parse.urlparse(uri).path
    pathlib.Path(path).unlink()


@loader(schemes='locals', media_type=None)
def load_local_variable(state: State, key):
    path = urllib.parse.urlparse(key).path
    return state._op_frame._set[path]


@storer(schemes='locals', media_type=None)
def store_local_variable(state: State, data, key):
    path = urllib.parse.urlparse(key).path
    state._op_frame._set[path] = data


@deleter(schemes='locals')
def delete_local_variable(state: State, key):
    path = urllib.parse.urlparse(key).path
    del state._op_frame._set[path]


@loader(schemes='globals', media_type=None)
def load_global_variable(state: State, key):
    path = urllib.parse.urlparse(key).path
    return state._vm._globals[path]


@storer(schemes='globals', media_type=None)
def store_global_variable(state: State, data, key):
    path = urllib.parse.urlparse(key).path
    state._vm._globals[path] = data


@deleter(schemes='globals')
def delete_global_variable(state: State, key):
    path = urllib.parse.urlparse(key).path
    del state._vm._globals[path]


# notes:
# - there needs to be a place to store metadata in the op (e.g., model name, provider name for QGIS model, details about inputs/outputs)
