from typing import Any, Mapping, MutableMapping, Optional, List
from mkdocstrings.handlers.base import BaseCollector, BaseHandler, BaseRenderer, CollectorItem
import fnmatch
import inspect

import urllib.parse
import importlib
import sequence.vm
import re


def add_hyperlinks_to_descriptions(metadata):
    if 'description' in metadata and 'references' in metadata:
        for i, ref in enumerate(metadata['references']):
            if 'url' not in ref:
                continue
            metadata['description'] = metadata['description'].replace(f"[{i+1}]", f'<a href="{ref["url"]}" target="_blank">[{i+1}]</a>')
    return metadata


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


class SequenceHandler(BaseHandler):
    def __init__(self, *args, **kwargs) -> None:
        self.fallback_theme = 'terminal'
        super().__init__(*args, **kwargs)

    def collect(self, identifier: str, config: MutableMapping[str, Any]) -> CollectorItem:
        includes: dict[str, str] = config.get('includes', {})
        imports: list[str] = config.get('imports', [])

        for module in imports:
            importlib.import_module(module)
        vm = sequence.vm.VirtualMachine()
        for routine, url in includes.items():
            vm._include(routine, url)

        docs: dict = {
            'op_names': [],
            'op_metadata': []
        }
        for op_name in config.get('ops', []):
            op = sequence.vm._static_ops[op_name]
            if callable(op):
                docstring = inspect.getdoc(op)
                metadata = parse_docstring(docstring)
            else:
                metadata: dict = op.get('metadata', {})
            metadata = add_hyperlinks_to_descriptions(metadata)
            docs['op_names'].append(op_name)
            docs['op_metadata'].append(metadata)

        docs['extdata_op'] = []
        docs['extdata_scheme'] = []
        docs['extdata_media_type'] = []
        docs['extdata_metadata'] = []
        for data_spec in config.get("data", []):
            if ":" in data_spec:
                scheme, media_type = data_spec.split(":")
            else:
                scheme = data_spec
                media_type = None

            getter = sequence.vm._static_getters.get(scheme, {}).get(media_type, None)
            putter = sequence.vm._static_putters.get(scheme, {}).get(media_type, None)
            deleter = sequence.vm._static_deleters.get(scheme, {}).get(media_type, None)

            if getter is not None:
                docs['extdata_op'].append("get")
                docs['extdata_scheme'].append(scheme)
                docs['extdata_media_type'].append(media_type)
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
                getter = inspect.getdoc(getter)
                metadata = parse_docstring(getter, metadata)
                docs['extdata_metadata'].append(metadata)
            if putter is not None:
                docs['extdata_op'].append("put")
                docs['extdata_scheme'].append(scheme)
                docs['extdata_media_type'].append(media_type)
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
                putter = inspect.getdoc(putter)
                metadata = parse_docstring(putter, metadata)
                docs['extdata_metadata'].append(metadata)
            if deleter is not None:
                docs['extdata_op'].append("del")
                docs['extdata_scheme'].append(scheme)
                docs['extdata_media_type'].append(media_type)
                metadata = {
                    'parameters': {
                        'uri': {
                            'type': 'str',
                            'description': 'The URI of the resource to delete',
                            'optional': False,
                        }
                    }
                }
                deleter = inspect.getdoc(deleter)
                metadata = parse_docstring(deleter, metadata)
                docs['extdata_metadata'].append(metadata)

        return docs

    def render(self, data: CollectorItem, config: Mapping[str, Any]) -> str:
        self.env.filters['zip'] = zip
        template = self.env.get_template("ops.html")
        return template.render(**data)


# https://mkdocstrings.github.io/usage/handlers/#custom-handlers


def get_handler(
    **kwargs,
):
    return SequenceHandler(
        handler="sequence",
        **kwargs
    )
