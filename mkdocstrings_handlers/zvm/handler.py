from typing import Any, Mapping, MutableMapping, Optional, List
from mkdocstrings.handlers.base import BaseCollector, BaseHandler, BaseRenderer, CollectorItem

import inspect

import urllib.parse
import importlib
import zvm.zvm
import re

class ZVMHandler(BaseHandler):
    def __init__(self, *args: str | BaseCollector | BaseRenderer, **kwargs: str | BaseCollector | BaseRenderer) -> None:
        super().__init__(*args, **kwargs)

    @staticmethod
    def _docstring_description_regex(headers: list):
        return rf"\A(?P<base>[\s\S]+?)(?:\n\n|\Z)(?:{'|'.join(headers)})"

    @staticmethod
    def _docstring_section_regex(header: str, name: str):
        return rf"(?:^{header}[ \t]*\n-{{{len(header)}}}[ \t]*\n(?P<{name}>[\s\S]*?)(?:\n\n|\Z))"

    # @staticmethod
    # def _docstring_parameter_regex():
    #     return r"(?P<name>^\S[^:\n]*)(?P<type>:[^\(\n]*)?(?P<default>\(default:[ \t]*[^\)]*\))?(?P<description>(?:\n[  \t]+[\S \t]+)+)?"

    @staticmethod
    def _docstrings_parse_args(text: str, optional_key: str):
        pattern = r"(?P<name>^\S[^:\n]*)(?P<type>:[^\(\n]*)?(?P<default>\(default:[ \t]*[^\)]*\))?[ \t]*(?P<description>(?:\n[  \t]+[\S \t]+)+)?"
        hints = []
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
            hints.append(arg)
        return hints

    @staticmethod
    def _docstring_reference():
        return r"^\d+\.[ \t]*((?:(?:\n[ \t]+)?[^\n\(]+)+)(\([^\)]+\))?(?!\d)"

    def collect(self, identifier: str, config: MutableMapping[str, Any]) -> CollectorItem:
        imports: list[str] = config.get('imports', [])
        includes: dict[str, str] = config.get('includes', [])

        for module in imports:
            importlib.import_module(module)
        vm = zvm.zvm.ZVM()
        for routine, url in includes.items():
            vm._include(routine, url)

        re_filters = config.get('filter', ['.*'])
        if isinstance(re_filters, str):
            re_filters = [re_filters]
        ops = set()
        for re_filter in re_filters:
            re_filter = re.compile(re_filter)
            ops.update(filter(re_filter.match, zvm.zvm._static_ops.keys()))
        ops = sorted(ops)

        docs: dict = {}
        for op_name in ops:
            op = zvm.zvm._static_ops[op_name]
            if callable(op):
                docstring = inspect.getdoc(op)
                hints = {}

                SECTIONS = ['Inputs', 'Parameters', 'Outputs', 'References']
                if matches := re.match(self._docstring_description_regex(SECTIONS), docstring):
                    hints['description'] = matches.group(1)

                if matches := re.search(self._docstring_section_regex('Inputs', 'inputs'), docstring, re.MULTILINE):
                    text = matches.group('inputs')
                    hints['inputs'] = self._docstrings_parse_args(text, 'conditional')

                if matches := re.search(self._docstring_section_regex('Parameters', 'params'), docstring, re.MULTILINE):
                    text = matches.group('params')
                    params = self._docstrings_parse_args(text, 'optional')
                    params_dict = {}
                    for param in params:
                        params_dict[param.pop("name")] = param
                    hints['parameters'] = params_dict

                if matches := re.search(self._docstring_section_regex('Outputs', 'outputs'), docstring, re.MULTILINE):
                    text = matches.group('outputs')
                    hints['outputs'] = self._docstrings_parse_args(text, 'conditional')

                if matches := re.search(self._docstring_section_regex('References', 'references'), docstring, re.MULTILINE):
                    text = matches.group('references')
                    references = re.findall(self._docstring_reference(), text, re.MULTILINE)
                    refs = []
                    for ref in references:
                        ref = {
                            'text': ref[0].strip(),
                            'url': ref[1].strip(" \t()")
                        }
                        ref = {k: v for k, v in ref.items() if v != ''}
                        refs.append(ref)
                    if len(refs):
                        hints['references'] = refs
            else:
                hints: dict = op.get('hints', {})

            if 'description' in hints and 'references' in hints:
                for i, ref in enumerate(hints['references']):
                    if 'url' not in ref:
                        continue
                    hints['description'] = hints['description'].replace(f"[{i+1}]", f'<a href="{ref["url"]}" target="_blank">[{i+1}]</a>')

            docs[op_name] = hints
        return docs

    def render(self, data: CollectorItem, config: Mapping[str, Any]) -> str:
        template = self.env.get_template("ops.html")
        return template.render(ops=data)


# https://mkdocstrings.github.io/usage/handlers/#custom-handlers


def get_handler(
    **kwargs,
):
    return ZVMHandler(
        handler="zvm",
        **kwargs
    )
