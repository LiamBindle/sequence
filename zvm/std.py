import inspect
import requests
import urllib.parse
import json
import zvm.state


def op(name):
    def inner(func: callable):
        signature = inspect.signature(func)
        # validate expression
        n = 0
        for param_name, param_value in signature.parameters.items():
            if param_value.kind == inspect.Parameter.POSITIONAL_ONLY:
                n += 1
                assert param_value.default == inspect.Parameter.empty, f"definition of '{func.__name__}' sets a default value for the positional argument '{param_name}' (not allowed)"
            else:
                break
        zvm.state.ops[name] = {'f': func, "n": n}
        return func
    return inner


def uri_scheme(*, schemes: str | list[str], content_type: str):
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: callable):
        for scheme in schemes:
            if scheme not in zvm.state.fetchers:
                zvm.state.fetchers[scheme] = {}
            zvm.state.fetchers[scheme][content_type] = func
        return func
    return inner

# @uri_scheme -- function is passed urlparse objected and expected to return dict resulting from loading json object


@op("if")
def if_(cond, /, *, true, false):
    return true if cond else false


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
