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
