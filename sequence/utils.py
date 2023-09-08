import re
from typing import List, Callable, Union
import inspect
import sequence.static
from enum import Enum


def method(name):
    def inner(func: Callable):
        if func.__code__.co_argcount != 1:
            raise RuntimeError("function must take exactly one position argument (state: sequence.State)")
        sequence.static.ops[name] = func
        return func
    return inner


def getter(*, schemes: Union[str, list[str]], media_type: str, extensions: Union[str, list[str]] = []):
    if isinstance(schemes, str):
        schemes = [schemes]
    if isinstance(extensions, str):
        extensions = [extensions]

    def inner(func: Callable):
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position arguments (state: sequence.State, url: str)")
        for scheme in schemes:
            if scheme not in sequence.static.getters:
                sequence.static.getters[scheme] = {}
            sequence.static.getters[scheme][media_type] = func

            if scheme not in sequence.static.ext_getter:
                sequence.static.ext_getter[scheme] = {}
            for ext in extensions:
                sequence.static.ext_getter[scheme][ext] = func

        return func
    return inner


def putter(*, schemes: Union[str, list[str]], media_type: str):
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: Callable):
        if func.__code__.co_argcount != 3:
            raise RuntimeError("function must take exactly three position argument (state: sequence.State, data: Any, url: str)")
        for scheme in schemes:
            if scheme not in sequence.static.putters:
                sequence.static.putters[scheme] = {}
            sequence.static.putters[scheme][media_type] = func
        return func
    return inner


def deleter(*, schemes: Union[str, list[str]], media_type: str = None):
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: Callable):
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position argument (state: sequence.State, url: str)")
        for scheme in schemes:
            if scheme not in sequence.static.deleters:
                sequence.static.deleters[scheme] = {}
            sequence.static.deleters[scheme][media_type] = func
        return func
    return inner


def copier(*, types: Union[type, List[type]]):
    if isinstance(types, type):
        types = [types]

    def inner(func: Callable):
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position argument (data: object, deep: bool)")
        for t in types:
            sequence.static.copiers[t] = func
        return func
    return inner



def parse_docstring(docstring: str, metadata: dict = None) -> dict:
    if metadata is None:
        metadata = {}

    def _docstring_description_regex(headers: list):
        return rf"\A(?P<base>[\s\S]+?)(?:\n\n|\Z)(?:{'|'.join(headers)})?"

    def _docstring_section_regex(header: str, name: str):
        return rf"(?:^{header}[ \t]*\n-{{{len(header)}}}[ \t]*\n(?P<{name}>[\s\S]*?)(?:\n\n|\Z))"

    def _docstrings_parse_args(text: str, optional_key: str):
        pattern = r"(?P<name>^\S[^:\n]*)(?P<type>:[^\(\n]*)?(?P<default>\(default:[ \t]*[^\)]*\))?[ \t]*(?P<description>(?:\n[  \t]+[\S \t]+)+)?"
        metadata = []
        for match in re.findall(pattern, text, re.MULTILINE):
            arg = {}
            name = match[0]
            optional = bool(re.match(r"^\[\S+\]", name))
            arg['name'] = name.strip(" []")
            arg['type'] = match[1].strip(" :")
            arg['default'] = match[2].removeprefix("(default:").removesuffix(")").strip()
            arg['description'] = match[3].strip()
            arg[optional_key] = optional or arg['default'] != ''
            arg = {k: v for k, v in arg.items() if v != ''}
            metadata.append(arg)
        return metadata

    def _docstring_reference():
        return r"^\d+\.[ \t]*((?:(?:\n[ \t]+)?[^\n\[]+)+)(\[[^\]]+\])?(?!\d)"

    SECTIONS = ['Inputs', 'Parameters', 'Outputs', 'References']
    if matches := re.match(_docstring_description_regex(SECTIONS), docstring):
        metadata['description'] = matches.group(1)

    if matches := re.search(_docstring_section_regex('Inputs', 'inputs'), docstring, re.MULTILINE):
        text = matches.group('inputs')
        inputs = _docstrings_parse_args(text, 'conditional')
        if inputs:
            metadata['inputs'] = inputs

    if matches := re.search(_docstring_section_regex('Parameters', 'params'), docstring, re.MULTILINE):
        text = matches.group('params')
        params = _docstrings_parse_args(text, 'optional')
        params_dict = {}
        for param in params:
            params_dict[param.pop("name")] = param
        if 'parameters' not in metadata:
            metadata['parameters'] = {}
        metadata['parameters'].update(params_dict)

    if matches := re.search(_docstring_section_regex('Outputs', 'outputs'), docstring, re.MULTILINE):
        text = matches.group('outputs')
        outputs = _docstrings_parse_args(text, 'conditional')
        if outputs:
            metadata['outputs'] = outputs

    if matches := re.search(_docstring_section_regex('References', 'references'), docstring, re.MULTILINE):
        text = matches.group('references')
        references = re.findall(_docstring_reference(), text, re.MULTILINE)
        refs = []
        for ref in references:
            ref = {
                'text': ref[0].strip(),
                'url': ref[1].strip(" \t[]")
            }
            ref = {k: v for k, v in ref.items() if v != ''}
            refs.append(ref)
        if len(refs):
            metadata['references'] = refs
    return metadata


def get_metadata():
    ops_metadata = {}
    for op_name in sequence.static.ops.keys():
        op = sequence.static.ops[op_name]
        if callable(op):
            docstring = inspect.getdoc(op)
            metadata = parse_docstring(docstring)
        else:
            metadata: dict = op.get('metadata', {})
        ops_metadata[op_name] = metadata

    resource_metadata = {}

    def add_resource_metadata(scheme: str, media_type: str, op_type: str, metadata: dict):
        if scheme is None:
            scheme = '*'
        if scheme not in resource_metadata:
            resource_metadata[scheme] = {}
        if media_type not in resource_metadata[scheme]:
            resource_metadata[scheme][media_type] = {}
        resource_metadata[scheme][media_type][op_type] = metadata

    for scheme in sequence.static.getters.keys():
        for media_type, func in sequence.static.getters[scheme].items():
            metadata = {
                'outputs': [
                    {'name': 'data', 'description': 'The loaded resource', 'conditional': False}
                ],
                'parameters': {
                    'uri': {
                        'type': 'str',
                        'description': 'The URI of the resource to load',
                        'optional': False,
                    }
                }
            }
            metadata = parse_docstring(inspect.getdoc(func), metadata)
            add_resource_metadata(scheme, media_type, 'get', metadata)
        for media_type, func in sequence.static.putters[scheme].items():
            metadata = {
                'inputs': [
                    {'name': 'data', 'description': 'The resource to save', 'conditional': False}
                ],
                'parameters': {
                    'uri': {
                        'type': 'str',
                        'description': 'The URI of where the resource should be saved',
                        'optional': False,
                    }
                }
            }
            metadata = parse_docstring(inspect.getdoc(func), metadata)
            add_resource_metadata(scheme, media_type, 'put', metadata)
        for media_type, func in sequence.static.deleters[scheme].items():
            metadata = {
                'parameters': {
                    'uri': {
                        'type': 'str',
                        'description': 'The URI of the resource to delete',
                        'optional': False,
                    }
                }
            }
            metadata = parse_docstring(inspect.getdoc(func), metadata)
            add_resource_metadata(scheme, media_type, 'del', metadata)

    return ops_metadata, resource_metadata
