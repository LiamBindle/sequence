import requests
import urllib.parse
import json
import copy
import string
import pathlib
import zvm.zvm
from zvm.zvm import op, loader, storer, deleter, State
# @uri_scheme -- function is passed urlparse objected and expected to return dict resulting from loading json object


# x format string
# x looping (see forth)
# x conditionals
# x reodering (see stack machine)
# x asserts
# x save/load/delete
# x add local and global variables
# logging
# x recurse
# x ppop from stack (so anonymous routines can have arguments)
# continue
# for loop (should use local variable to avoid interfering with the stack)
# while loop (begin...while...repeat avoid code duplication by putting condition logic in begin...while section)
# pack/unpack to pack n items into a tuple or unpack a tuple onto the stack
# switch statement

# need decorator to register copy (shallow/deep), store, load, delete for arbitrary data types

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
    parsed_uri = urllib.parse.urlparse(uri)
    extra_kwargs = {}
    if parsed_uri.scheme == 'locals' or parsed_uri.scheme == 'globals':
        extra_kwargs['state'] = state
    uri_media_loader = zvm.zvm._static_loaders[parsed_uri.scheme][mediaType]
    return uri_media_loader(uri, **extra_kwargs, **kwargs)


@op("store")
def store(state: State, *, uri: str, mediaType: str = None, **kwargs):
    data = state.pop()
    parsed_uri = urllib.parse.urlparse(uri)
    extra_kwargs = {}
    if parsed_uri.scheme == 'locals' or parsed_uri.scheme == 'globals':
        extra_kwargs['state'] = state
    uri_media_storer = zvm.zvm._static_storers[parsed_uri.scheme][mediaType]
    uri_media_storer(data, uri, **extra_kwargs, **kwargs)


@op("delete")
def delete(state: State, *, uri: str, mediaType: str = None, **kwargs):
    parsed_uri = urllib.parse.urlparse(uri)
    extra_kwargs = {}
    if parsed_uri.scheme == 'locals' or parsed_uri.scheme == 'globals':
        extra_kwargs['state'] = state
    uri_media_deleter = zvm.zvm._static_deleters[parsed_uri.scheme][mediaType]
    uri_media_deleter(uri, **extra_kwargs, **kwargs)

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
def fetch_json_http(url: str):
    response = requests.get(url=url)
    return response.json()


@loader(schemes=['file'], media_type='application/json')
def fetch_json_file(url: str):
    path = urllib.parse.urlparse(url).path
    with open(path, 'r') as f:
        data = json.load(f)
    return data


@storer(schemes=['file'], media_type='application/json')
def store_json_file(data, uri: str):
    path = urllib.parse.urlparse(uri).path
    with open(path, 'w') as f:
        json.dump(data, f)


@deleter(schemes=['file'])
def delete_generic_file(uri: str, *, missing_ok: bool = False):
    path = urllib.parse.urlparse(uri).path
    pathlib.Path(path).unlink()


@loader(schemes='locals', media_type=None)
def load_local_variable(key, *, state: State):
    path = urllib.parse.urlparse(key).path
    return state._op_frame._set[path]


@storer(schemes='locals', media_type=None)
def store_local_variable(data, key, *, state: State):
    path = urllib.parse.urlparse(key).path
    state._op_frame._set[path] = data


@deleter(schemes='locals')
def delete_local_variable(key, *, state: State):
    path = urllib.parse.urlparse(key).path
    del state._op_frame._set[path]


@loader(schemes='globals', media_type=None)
def load_global_variable(key, *, state: State):
    path = urllib.parse.urlparse(key).path
    return state._vm._globals[path]


@storer(schemes='globals', media_type=None)
def store_global_variable(data, key, *, state: State):
    path = urllib.parse.urlparse(key).path
    state._vm._globals[path] = data


@deleter(schemes='globals')
def delete_global_variable(key, *, state: State):
    path = urllib.parse.urlparse(key).path
    del state._vm._globals[path]
