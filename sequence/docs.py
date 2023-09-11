from typing import Optional, Any, Union
import re
import inspect
from dataclasses import dataclass, field
from sequence.visitors.base import Sequence
from sequence.visitors.load import SequenceLoader
import sequence.static


@dataclass
class Parameter:
    type: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    optional: bool = False


@dataclass
class Input:
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    conditional: bool = False


@dataclass
class Output:
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    conditional: bool = False


@dataclass
class Reference:
    text: Optional[str]
    url: Optional[str] = None

    @staticmethod
    def create(obj: Union[str, dict]):
        if isinstance(obj, str):
            return Reference(text=obj)
        else:
            return Reference(**obj)


@dataclass
class OpDoc:
    name: Optional[str]
    description: Optional[str]
    inputs: list[Input]
    parameters: dict[str, Parameter]
    outputs: list[Output]
    references: list[Reference]

    @staticmethod
    def from_dict(d: dict) -> 'OpDoc':
        return OpDoc(
            name=d.get('name'),
            description=d.get('description'),
            inputs=[Input(**i) for i in d.get('inputs', [])],
            parameters={n: Parameter(**p) for n, p in d.get('parameters', {}).items()},
            outputs=[Output(**o) for o in d.get('outputs', [])],
            references=[Reference.create(r) for r in d.get('references', [])]
        )


def parse_docstring(method, metadata: dict = None) -> dict:
    docstring = inspect.getdoc(method)

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


def op_doc(op: str) -> OpDoc:
    op = sequence.static.ops[op]
    if isinstance(op, Sequence):
        metadata = op.metadata
    else:
        assert callable(op), 'internal error'
        metadata = parse_docstring(op)
    return OpDoc.from_dict(metadata)


def getter_doc(scheme: str, media_type: str):
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
    if not (scheme in sequence.static.getters and media_type in sequence.static.getters[scheme]):
        return None
    metadata = parse_docstring(sequence.static.getters[scheme][media_type], metadata)
    return OpDoc.from_dict(metadata)


def putter_doc(scheme: str, media_type: str):
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
    if not (scheme in sequence.static.putters and media_type in sequence.static.putters[scheme]):
        return None
    metadata = parse_docstring(sequence.static.putters[scheme][media_type], metadata)
    return OpDoc.from_dict(metadata)


def deleter_doc(scheme: str, media_type: str):
    metadata = {
        'parameters': {
            'uri': {
                'type': 'str',
                'description': 'The URI of the resource to delete',
                'optional': False,
            }
        }
    }
    if not (scheme in sequence.static.deleters and media_type in sequence.static.deleters[scheme]):
        return None
    metadata = parse_docstring(sequence.static.deleters[scheme][media_type], metadata)
    return OpDoc.from_dict(metadata)


if __name__ == '__main__':
    import sequence.standard.stack_operations
    file = "tests/json/test-recurse.json"
    seq = SequenceLoader.load(file, 'test recurse')
    # doc = op_doc(seq)
    # doc = op_doc("pack")
    # doc = getter_doc("https", "application/json")
    doc = putter_doc("variables", None)
    # doc = deleter_doc("file", None)
    print(doc)
