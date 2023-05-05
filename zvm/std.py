import requests
import urllib.parse
import json
import zvm.state
from zvm.utils import op, uri_scheme

# @uri_scheme -- function is passed urlparse objected and expected to return dict resulting from loading json object


# format string
# looping (see forth)
# conditionals
# reodering (see stack machine)
# asserts
# get expression from uri (content type: application/zvm-expression)
# save/load/delete from memory (use uri with scheme=zvm)
# logging
# recurse
# pop from stack (so anonymous routines can have arguments)


@op("assert")
def assert_(*, start: int = None, end: int = None, step: int = 1, size: int = None, eq: list = None, neq: list = None):
    if start is None:
        start = -1
    else:
        start = -start - 1
    if end is not None:
        end = -end - 1

    values = zvm.state.stack[start:end:-step]
    if size is not None:
        assert len(values) == size
    if eq is not None:
        assert values == eq
    if neq is not None:
        assert values != neq


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


@uri_scheme(schemes=['http', 'https'], content_type='application/json')
def fetch_json_http(url: str):
    response = requests.get(url=url)
    return response.json()


@uri_scheme(schemes=['file'], content_type='application/json')
def fetch_json_file(url: str):
    path = urllib.parse.urlparse(url).path
    with open(path, 'r') as f:
        data = json.load(f)
    return data
