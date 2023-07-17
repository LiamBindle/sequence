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
import urllib.request
import urllib.parse
import json
import copy
import string
import pathlib

try:
    import json5
    ENABLE_JSON5 = True
except ImportError:
    ENABLE_JSON5 = False

try:
    import hjson
    ENABLE_HJSON = True
except ImportError:
    ENABLE_HJSON = False


# TODO: add linter with callbacks so procedures can be inspected


# static variables for keeping track of user functions registered by imports
_static_ops: dict[str, Union[dict, Callable]] = {}
_static_getters: dict[str, dict[str, Callable]] = {}
_static_putters: dict[str, dict[str, Callable]] = {}
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

    def delete(self, key):
        del self._set[key]

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

    def delete_global(self, key):
        del self._vm._globals[key]


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
                    params = self._next_params
                    params.update({k: v for k, v in ex.items() if k != "op"})
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
            if url.path.endswith(".json5"):
                data = _static_getters[url.scheme]['application/json5'](self, url_or_op)
            elif url.path.endswith(".hjson"):
                data = _static_getters[url.scheme]['application/hjson'](self, url_or_op)
            else:
                data = _static_getters[url.scheme]['application/json'](self, url_or_op)
            # TODO: add callback for translator so file uris can be replaced with s3 uris and
            # files uploaded to s3 with appropriate key
            # scheme_translation = url.scheme equals target scheme
            #
            # This could be accomplished with a basic callback at the end of _include.

        elif isinstance(url_or_op, dict):
            data = url_or_op
        else:
            raise RuntimeError("include is not a url (str) or an op (dict)")
        _static_ops[name] = data

        self._import(data.get("import", []))
        for name, url_or_op in data.get("include", {}).items():
            self._include(name, url_or_op)

        # if scheme_translation:
        #   scheme_translation_callback(scheme, url_or_op)  # url_or_op is url

    def _import(self, imports: list):
        for module in imports:
            importlib.import_module(module)

    def eval(self, line: str):
        url = urllib.parse.urlparse(line)
        if line.startswith("import "):
            self._import([line.removeprefix("import ")])
        elif bool(url.scheme) and bool(url.path):
            op = _static_getters[url.scheme]['application/json'](self, line)
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
    # todo: add hints for pop order + type
    global _static_ops
    def inner(func: Callable):
        global _static_ops
        if func.__code__.co_argcount != 1:
            raise RuntimeError("function must take exactly one position argument (state: zvm.State)")
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
            raise RuntimeError("function must take exactly two position arguments (state: zvm.State, url: str)")
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
            raise RuntimeError("function must take exactly three position argument (state: zvm.State, data: Any, url: str)")
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
            raise RuntimeError("function must take exactly two position argument (state: zvm.State, url: str)")
        for scheme in schemes:
            if scheme not in _static_deleters:
                _static_deleters[scheme] = {}
            _static_deleters[scheme][media_type] = func
        return func
    return inner


_static_copiers = {}


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


# operators
@op("/")
def divide(state: State):
    """
    Divides the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '/' is applied to the
    objects.

    Inputs
    ------
    y: number, Any
        The denominator.
    x: number, Any
        The numerator.

    Outputs
    -------
    result: number, Any
        The result of the division.
    """
    x, y = state.popn(2)
    return x / y


@op("*")
def multiply(state: State):
    """
    Multiplies the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '*' is applied to the
    objects.

    Inputs
    ------
    y: number, Any
        The second term.
    x: number, Any
        The first term.

    Outputs
    -------
    result: number, Any
        The result of the multiplication.
    """
    x, y = state.popn(2)
    return x * y


@op("-")
def minus(state: State):
    """
    Subtracts the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '-' is applied to the
    objects.

    Inputs
    ------
    y: number, Any
        The second term.
    x: number, Any
        The first term.

    Outputs
    -------
    result: number, Any
        The result of the subtraction.
    """
    x, y = state.popn(2)
    return x - y


@op("+")
def plus(state: State):
    """
    Adds the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '+' is applied to the
    objects.

    Inputs
    ------
    y: number, Any
        The second term.
    x: number, Any
        The first term.

    Outputs
    -------
    result: number, Any
        The result of the addition.
    """
    x, y = state.popn(2)
    return x + y


@op("%")
def mod(state: State):
    """
    Returns the modulous the two numbers at the top of the stack. If the items at the top
    of the stack are  not numbers, the binary operator '%' is applied to the
    objects.

    Inputs
    ------
    y: number, Any
        The divisor.
    x: number, Any
        The dividend.

    Outputs
    -------
    result: number, Any
        The result of x mod y.
    """
    x, y = state.popn(2)
    return x % y


# bool ops
@op("not")
def not_(state: State):
    """
    Inverts the True/False value at the top of the stack. If the item at the
    top of the stack is not a boolean value, it is coerced to a boolean and
    then inverted.

    Inputs
    ------
    x: bool, Any
        The boolean value to be inverted.

    Outputs
    -------
    x_inv: bool
        The inverse boolean value of x.
    """
    x = state.pop()
    return not x


@op("and")
def and_(state: State):
    """
    Logical AND of the two boolean values at the top of the stack.
    If the items at the top of the stack are not booleans, they are coerced to
    booleans.

    Inputs
    ------
    y: bool, Any
        The second term.
    x: bool, Any
        The first term.

    Outputs
    -------
    z: bool
        The result of the logical AND operation.
    """
    x, y = state.popn(2)
    return x and y


@op("or")
def or_(state: State):
    """
    Logical OR of the two boolean values at the top of the stack.
    If the items at the top of the stack are not booleans, they are coerced to
    booleans.

    Inputs
    ------
    y: bool, Any
        The second term.
    x: bool, Any
        The first term.

    Outputs
    -------
    z: bool
        The result of the logical OR operation.
    """
    x, y = state.popn(2)
    return x or y


@op("xor")
def xor_(state: State):
    """
    Logical XOR of the two boolean values at the top of the stack.
    If the items at the top of the stack are not booleans, they are coerced to
    booleans.

    Inputs
    ------
    y: bool, Any
        The second term.
    x: bool, Any
        The first term.

    Outputs
    -------
    z: bool
        The result of the logical XOR operation.
    """
    x, y = state.popn(2)
    return bool(x) != bool(y)


@op("asbool")
def asbool_(state: State):
    """
    Coerces the item at the top of the stack to a boolean value.

    Inputs
    ------
    x: Any
        The item to be converted to a boolean value.

    Outputs
    -------
    x_bool: bool
        x as a boolean value.
    """
    x = state.pop()
    return bool(x)


@op("asint")
def asint_(state: State):
    """
    Coerces the item at the top of the stack to an integer.

    Inputs
    ------
    x: Any
        The item to be converted to an integer.

    Outputs
    -------
    x_int: int
        x as an integer.
    """
    x = state.pop()
    return int(x)


@op("asfloat")
def asfloat_(state: State):
    """
    Coerces the item at the top of the stack to a float.

    Inputs
    ------
    x: Any
        The item to be converted to a float.

    Outputs
    -------
    x_float: float
        x as an float.
    """
    x = state.pop()
    return float(x)


# comparison
@op("eq")
def equal(state: State):
    """
    Checks if x == y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    xy_eq: bool
        The result of x == y.
    """
    x, y = state.popn(2)
    return x == y


@op("neq")
def not_equal(state: State):
    """
    Checks if x is not equal to y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    xy_neq: bool
        The result of x != y.
    """
    x, y = state.popn(2)
    return x != y


@op("gt")
def greater_than(state: State):
    """
    Checks if x is greater than y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    x_gt_y: bool
        The result of x > y.
    """
    x, y = state.popn(2)
    return x > y


@op("ge")
def greater_than_or_equal_to(state: State):
    """
    Checks if x is greater than or equal to y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    x_ge_y: bool
        The result of x >= y.
    """
    x, y = state.popn(2)
    return x >= y


@op("lt")
def less_than(state: State):
    """
    Checks if x is less than y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    x_lt_y: bool
        The result of x < y.
    """
    x, y = state.popn(2)
    return x < y


@op("le")
def less_than_or_equal_to(state: State):
    """
    Checks if x is less than or equal to y.

    Inputs
    ------
    y: Any
        The RHS operand.
    x: Any
        The LHS operand.

    Outputs
    -------
    x_le_y: bool
        The result of x <= y.
    """
    x, y = state.popn(2)
    return x <= y


# stack ops
@op("dup")
def duplicate(state: State, *, deep: bool = False, offset: int = 0):
    """
    Duplicates the item at the top of the stack. There are parameters
    to control if a shallow or deep copy is done, as well as control
    the TOS offset of the item to be duplicated.

    Parameters
    ----------
    [deep]: bool (default: false)
        Controls if the copy is a shallow or deep copy.
    [offset]: int (default: 0)
        The offset (from TOS) of the item you want to duplicate.

    Outputs
    -------
    item_copy: Any
        A copy of the requested item.
    """
    global _static_copiers
    offset = -1 - offset
    item = state._stack[offset]
    item_type = type(item)
    if item_type in _static_copiers:
        return _static_copiers[item_type](item, deep)
    else:
        if deep:
            return copy.deepcopy(item)
        else:
            return copy.copy(item)


@op("swap")
def swap(state: State, *, order: list = [1, 0]):
    """
    Swaps the order of the items at the top of the stack.

    Parameters
    ----------
    [order]: list (default: [1, 0])
        The new order of the TOS. The first integer is the list is TOS
        offset of the item that should be moved to the TOS. The length
        of the list controls the number of items that are reordered.
    """
    size = len(order)
    items = state.popn(size)
    new_items = [items[size-1-i] for i in reversed(order)]
    return new_items


@op("drop")
def drop(state: State):
    """
    Drops the item at the top of the stack.
    """
    state.pop()


@op("size")
def stack_size(state: State):
    """
    Returns the current size (depth) of the stack.

    Outputs
    -------
    stack_size: int
        The size of the stack.
    """
    return len(state._stack)


# looping
@op("begin")
def begin_(state: State):
    """
    Marks the beginning of a loop.
    """
    state._op_frame._begins.append(state._op_frame._pc)


@op("repeat")
def repeat_(state: State):
    """
    Marks the end of a loop.
    """
    state._op_frame._pc = state._op_frame._begins[-1]


@op("break")
def break_(state: State):
    """
    Breaks out of a loop (terminates the loop).
    """
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
    """
    Restarts the current procedure.
    """
    state._op_frame._pc = -1


@op("while")
def while_(state: State):
    """
    Continues the loop if the item at the top of the stack is true. If the
    item at the top of the stack is not true, it terminates the loop.

    This method is useful for constructing traditional while-loops in a
    procedure.

    This method MUST be placed between `{"op": "begin"}` and `{"op": "repeat"}`.

    Inputs
    ------
    cond: bool, Any
        If true, the loop continues. If false, the loop terminates.
    """
    cond = state.pop()
    if not cond:
        break_(state)


# branching
@op("if")
def if_(state: State):
    """
    Marks the beginning of an if-block. An if statment MUST be terminated by `{"op": "endif"}`.

    Inputs
    ------
    cond: bool, Any
        If true, the if-block is evaluated. If false, the else-block is
        evaluated if it exists.
    """
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
    """
    Marks the beginning of an else-block. This method MUST be placed between
    `{"op": "if"}` and `{"op": "endif"}`.
    """
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
    """
    Marks the end of an if statement.
    """
    # noop
    pass


# state
@op("get")
def load(state: State, *, uri: str, mediaType: str = None, **params):
    """
    Loads an resource from a URI and places it as the top of the stack.

    Parameters
    ----------
    uri: str
        The URI of the resource you want to load.
    [mediaType]: str
        The media type of the resource you want to load.
    [**params]:
        Additional parameters are passed to the getter.

    Outputs
    -------
    item: Any
        The loaded resource.
    """
    global _static_getters
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_getter = _static_getters[parsed_uri.scheme][mediaType]
    return uri_media_getter(state, uri, **params)


@op("put")
def store(state: State, *, uri: str, mediaType: str = None, **params):
    """
    Stores the item at the top of the stack.

    Parameters
    ----------
    uri: str
        The desination where you want to store the item.
    [mediaType]: str
        The media type of the resource you want to store.
    [**params]:
        Additional parameters are passed to the putter.

    Inputs
    -------
    item: Any
        The item to be stored.
    """
    global _static_putters
    data = state.pop()
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_putter = _static_putters[parsed_uri.scheme][mediaType]
    uri_media_putter(state, data, uri, **params)


@op("del")
def delete(state: State, *, uri: str, mediaType: str = None, **params):
    """
    Deletes a resource.

    Parameters
    ----------
    uri: str
        The URI of the resource to be deleted.
    [mediaType]: str
        The media type of the resource you want to delete.
    [**params]:
        Additional parameters are passed to the deleter.
    """
    global _static_deleters
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_deleter = _static_deleters[parsed_uri.scheme][mediaType]
    uri_media_deleter(state, uri, **params)

# misc


@op("fstring")
def format_string(state: State, *, fmt: str, **params):
    """
    Formats a string.

    Parameters
    ----------
    fmt: str
        The format string (a python f-string). See the Python documentation of
        f-strings details.
    [**params]:
        Named arguments for the f-string.

    Inputs
    ------
    ...: Any
        The top N items are poped from the stack where N is the number of
        positional arguments in the f-string.

    Outputs
    -------
    result: str
        The formatted string.
    """
    formatter = string.Formatter()
    parsed_fmt = formatter.parse(fmt)
    format_nargs = 0
    format_params = set()
    for (_, field_name, _, _) in parsed_fmt:
        if field_name is None:
            # no replacement field
            continue
        if field_name == '' or field_name.isnumeric():
            format_nargs += 1
        else:
            format_params.add(field_name)
    args = state.popn(format_nargs)
    return fmt.format(*args, **params)


@op("assert")
def assert_(state: State, *, error: str = '', negate: bool = False):
    """
    Asserts that the item at the top of the stack is true. Terminates
    execution if false.

    Parameters
    ----------
    [error]: str
        The error message to print if the assertion fails.
    [negate]: bool (default: false)
        Assert that the item at the top of the stack if false (rather than
        true).

    Inputs
    ------
    cond: bool
        The boolean value to check.
    """
    x = state.pop()
    if negate:
        assert not x, error
    else:
        assert x, error


@op("pack")
def pack_(state: State, *, n: int, forward: bool = True, keys: List[str] = None):
    """
    Packs N items from the top of the stack into a single array at the top of
    the stack.

    Parameters
    ----------
    n: int
        The number of items at the top of the stack to pack into the array.
    [forward]: bool (default: true)
        If false, the items are packed in reverse order.
    [keys]: list
        If provided, the items are packed as key-value pairs. The first key
        applies to the TOS item.

    Inputs
    ------
    ...: Any
        n items are consumed from the top of the stack.

    Outputs
    -------
    arr: Array
        An array of items.
    """
    items = state.popn(n)
    if not forward:
        items.reverse()
    if keys is not None:
        items = {k: v for k, v in zip(reversed(keys), items)}
    else:
        items = tuple(items)
    return items


@op("unpack")
def unpack_(state: State, *, keys: List[str] = None):
    """
    Packs N items from the top of the stack into a single array at the top of
    the stack.

    Parameters
    ----------
    [keys]: list
        Required to unpack a list of key-value pairs. The first key refers to the
        new TOS item.

    Outputs
    -------
    ...: Any
        The unpacked items.
    """
    items = state.pop()
    if keys is not None:
        items = [items[k] for k in keys]
    else:
        items = list(items)
    return items


@op("set_next_params")
def set_next_params(state: State):
    """
    Initializes the next op's parameters to the key-value array at the top-of-the-stack.

    This is useful to set parameters dynamically.

    Parameters
    ----------
    kv_arr: key-value array
        Parameters for the next op.
    """
    params = state.pop()
    if not isinstance(params, dict):
        raise TypeError(f"Top-of-stack expected to be 'dict' but got '{type(params)}'")
    state._op_frame._next_params = params


@getter(schemes=['http', 'https'], media_type='application/json')
def fetch_json_http(state: State, url: str):
    """
    Loads a JSON file from a remote HTTP/HTTPS source.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    response = urllib.request.urlopen(url)
    if response.code != 200:
        raise RuntimeError(f"Error reading {url}")
    return json.loads(response.read())


@getter(schemes=['file'], media_type='application/json')
def fetch_json_file(state: State, url: str):
    """
    Loads a JSON file from a local file.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    path = urllib.parse.urlparse(url).path
    path = urllib.parse.unquote(path)
    with open(path, 'r') as f:
        data = json.load(f)
    return data


@putter(schemes=['file'], media_type='application/json')
def store_json_file(state: State, data, uri: str):
    """
    Loads a JSON file from a local file.

    Inputs
    ------
    data: key-value array
        The key-value array to be saved.
    """
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    with open(path, 'w') as f:
        json.dump(data, f)


@getter(schemes=['http', 'https'], media_type='application/json5')
def fetch_json5_http(state: State, url: str):
    """
    Loads a JSON5 file from a remote HTTP/HTTPS source.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    if not ENABLE_JSON5:
        raise RuntimeError("json5 support not enabled")
    response = urllib.request.urlopen(url)
    if response.code != 200:
        raise RuntimeError(f"Error reading {url}")
    return json5.loads(response.read())


@getter(schemes=['file'], media_type='application/json5')
def fetch_json5_file(state: State, url: str):
    """
    Loads a JSON5 file from a local file.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    if not ENABLE_JSON5:
        raise RuntimeError("json5 support not enabled")
    path = urllib.parse.urlparse(url).path
    path = urllib.parse.unquote(path)
    with open(path, 'r') as f:
        data = json5.load(f)
    return data


@putter(schemes=['file'], media_type='application/json5')
def store_json5_file(state: State, data, uri: str):
    """
    Loads a JSON5 file from a local file.

    Inputs
    ------
    data: key-value array
        The key-value array to be saved.
    """
    if not ENABLE_JSON5:
        raise RuntimeError("json5 support not enabled")
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    with open(path, 'w') as f:
        json5.dump(data, f)


@getter(schemes=['http', 'https'], media_type='application/hjson')
def fetch_hjson_http(state: State, url: str):
    """
    Loads a HJSON file from a remote HTTP/HTTPS source.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    if not ENABLE_HJSON:
        raise RuntimeError("hjson support not enabled")
    response = urllib.request.urlopen(url)
    if response.code != 200:
        raise RuntimeError(f"Error reading {url}")
    return hjson.loads(response.read())


@getter(schemes=['file'], media_type='application/hjson')
def fetch_hjson_file(state: State, url: str):
    """
    Loads a HJSON file from a local file.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    if not ENABLE_HJSON:
        raise RuntimeError("hjson support not enabled")
    path = urllib.parse.urlparse(url).path
    path = urllib.parse.unquote(path)
    with open(path, 'r') as f:
        data = hjson.load(f)
    return data


@putter(schemes=['file'], media_type='application/hjson')
def store_hjson_file(state: State, data, uri: str):
    """
    Loads a HJSON file from a local file.

    Inputs
    ------
    data: key-value array
        The key-value array to be saved.
    """
    if not ENABLE_HJSON:
        raise RuntimeError("hjson support not enabled")
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    with open(path, 'w') as f:
        hjson.dump(data, f)


@deleter(schemes=['file'])
def delete_generic_file(state: State, uri: str, *, missing_ok: bool = False):
    """
    Deletes a local file.
    """
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    pathlib.Path(path).unlink(missing_ok)


@getter(schemes='locals', media_type=None)
def load_local_variable(state: State, key, *, default: Any = None):
    """
    Loads a local variable and places the result at the top of the stack.

    Parameters
    ----------
    [default]: Any (default: None)
        The default value if the variable doesn't exist.

    Outputs
    -------
    data: Any
        The local variable.
    """
    path = urllib.parse.urlparse(key).path
    return state._op_frame._set.get(path, default)


@putter(schemes='locals', media_type=None)
def store_local_variable(state: State, data, key):
    """
    Saves a local variable (procedure-scope).
    """
    path = urllib.parse.urlparse(key).path
    state._op_frame._set[path] = data


@deleter(schemes='locals')
def delete_local_variable(state: State, key):
    """
    Deletes a local variable.
    """
    path = urllib.parse.urlparse(key).path
    del state._op_frame._set[path]


@getter(schemes='globals', media_type=None)
def load_global_variable(state: State, key, *, default: Any = None):
    """
    Loads a global variable and places the result at the top of the stack.

    Parameters
    ----------
    [default]: Any (default: None)
        The default value if the variable doesn't exist.

    Outputs
    -------
    data: Any
        The global variable.
    """
    path = urllib.parse.urlparse(key).path
    return state._vm._globals.get(path, default)


@putter(schemes='globals', media_type=None)
def store_global_variable(state: State, data, key):
    """
    Saves a global variable.
    """
    path = urllib.parse.urlparse(key).path
    state._vm._globals[path] = data


@deleter(schemes='globals')
def delete_global_variable(state: State, key):
    """
    Deletes a global variable.
    """
    path = urllib.parse.urlparse(key).path
    del state._vm._globals[path]


# notes:
# - there needs to be a place to store metadata in the op (e.g., model name, provider name for QGIS model, details about inputs/outputs)
