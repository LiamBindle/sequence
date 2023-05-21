import requests
import urllib.parse
import json
import zvm.state
from zvm.utils import op, loader, storer, deleter
import copy
import string
import pathlib

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
def divide(y, x, /):
    return x / y


@op("*")
def multiply(y, x, /):
    return x * y


@op("-")
def minus(y, x, /):
    return x - y


@op("+")
def plus(y, x, /):
    return x + y


@op("%")
def mod(y, x, /):
    return x % y


# bool ops
@op("not")
def not_(x, /):
    return not x


@op("and")
def and_(y, x, /):
    return x and y


@op("or")
def or_(y, x, /):
    return x or y


@op("xor")
def xor_(y, x, /):
    return bool(x) != bool(y)


@op("asbool")
def asbool_(x, /):
    return bool(x)


# comparison
@op("eq")
def equal(y, x, /) -> bool:
    return x == y


@op("neq")
def not_equal(y, x, /) -> bool:
    return x != y


@op("gt")
def greater_than(y, x, /) -> bool:
    return x > y


@op("ge")
def greater_than_or_equal_to(y, x, /) -> bool:
    return x >= y


@op("lt")
def less_than(y, x, /) -> bool:
    return x < y


@op("le")
def less_than_or_equal_to(y, x, /) -> bool:
    return x <= y


# stack ops
def pop_from_current(*, n: int = 1):
    return [zvm.state.stack.pop() for _ in range(n)]


@op("ppop")
def pop_from_parent(*, n: int = 1):
    return [zvm.state._routine_stacks[-2].pop() for _ in range(n)]


@op("dup")
def duplicate(*, deep: bool = False, offset: int = 0):
    offset = -1 - offset
    item = zvm.state.stack[offset]
    if deep:
        return copy.deepcopy(item)
    else:
        return copy.copy(item)


@op("swap")
def swap(y, x, /):
    return [x, y]


@op("drop")
def drop(_, /):
    return []


@op("reorder")
def reorder(*, order: list = []):  # e.g., [2, 0, 1] puts current TOS+2 at TOS, current TOS at TOS+1, and current TOS+1 at TOS+2
    items = pop_from_current(n=len(order))
    new_items = [items[i] for i in reversed(order)]
    return new_items


@op("ssize")
def ssize():
    return len(zvm.state.stack)


# looping
@op("begin")
def begin_():
    zvm.state._routine_begin_stacks[-1].append(zvm.state._routine_pc[-1])


@op("repeat")
def repeat_():
    zvm.state._routine_pc[-1] = zvm.state._routine_begin_stacks[-1][-1]


@op("break")
def break_():
    nested_loops = 0
    pc = zvm.state._routine_pc[-1]
    while pc < len(zvm.state.instr):
        pc += 1
        ex = zvm.state.instr[pc]
        if not isinstance(ex, dict):
            continue
        if 'op' not in ex:
            continue
        op = ex["op"]
        if op == 'begin':  # or any loop-start
            nested_loops += 1
        elif op == 'repeat':  # or any loop-end
            if nested_loops == 0:
                zvm.state._routine_pc[-1] = pc
                zvm.state._routine_begin_stacks[-1].pop()
                return
            else:
                nested_loops -= 1

    # continue until repeat
    raise RuntimeError("Unterminated begin statement")


@op("recurse")
def recurse():
    zvm.state._routine_pc[-1] = -1


# branching
@op("if")
def if_(cond, /):
    if cond:
        return
    # set PC to address to else/endif
    nested_branches = 0
    pc = zvm.state._routine_pc[-1]
    while pc < len(zvm.state.instr):
        pc += 1
        ex = zvm.state.instr[pc]
        if not isinstance(ex, dict):
            continue
        if 'op' not in ex:
            continue
        op = ex["op"]
        if op == 'if':
            nested_branches += 1
        elif nested_branches == 0 and (op == 'else' or op == 'endif'):
            zvm.state._routine_pc[-1] = pc
            return
        elif op == 'endif':
            nested_branches -= 1

    raise RuntimeError("Unterminated if statement")


@op("else")
def else_():
    # set PC to address to else/endif
    nested_branches = 0
    pc = zvm.state._routine_pc[-1]
    while pc < len(zvm.state.instr):
        pc += 1
        ex = zvm.state.instr[pc]
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
            zvm.state._routine_pc[-1] = pc
            return
    raise RuntimeError("Unterminated if statement")


@op("endif")
def endif_():
    # noop
    pass


# state
@op("load")
def load(*, uri: str, mediaType: str = None, **kwargs):
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_loader = zvm.state.loaders[parsed_uri.scheme][mediaType]
    return uri_media_loader(uri, **kwargs)


@op("store")
def store(data, /, *, uri: str, mediaType: str = None, **kwargs):
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_storer = zvm.state.storers[parsed_uri.scheme][mediaType]
    uri_media_storer(data, uri, **kwargs)


@op("delete")
def delete(*, uri: str, mediaType: str = None, **kwargs):
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_deleter = zvm.state.deleters[parsed_uri.scheme][mediaType]
    uri_media_deleter(uri, **kwargs)

# misc


@op("fstring")
def format_string(*, fmt: str, **kwargs):
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
    args = pop_from_current(n=format_nargs)
    return fmt.format(*args, **kwargs)


@op("assert")
def assert_(x, /, *, error: str = '', negate: bool = False):
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
def delete_generic_file(uri: str, missing_ok: bool = False):
    path = urllib.parse.urlparse(uri).path
    pathlib.Path(path).unlink()


@loader(schemes='locals', media_type=None)
def load_local_variable(key):
    return zvm.state.local_vars[key]


@storer(schemes='locals', media_type=None)
def store_local_variable(data, key):
    zvm.state.local_vars[key] = data


@deleter(schemes='locals')
def delete_local_variable(key):
    del zvm.state.local_vars[key]


@loader(schemes='globals', media_type=None)
def load_global_variable(key):
    return zvm.state.global_vars[key]


@storer(schemes='globals', media_type=None)
def store_global_variable(data, key):
    zvm.state.global_vars[key] = data


@deleter(schemes='globals')
def delete_global_variable(key):
    del zvm.state.global_vars[key]
