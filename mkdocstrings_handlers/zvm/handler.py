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
    def _docstring_section_regex(header: str, name: str):
        return rf"(?:^{header}\n-{{{len(header)}}}\n(?P<{name}>[\s\S]*?)(?:\n\n|\Z))"

    @staticmethod
    def _docstring_parameter_regex():
        return r"(?P<name>^\S[\S\h]*?)(?P<type>:[\S\h]*)?(?P<default>\(default:\h*[\S\h]*\))?(?P<description>(?:\n\h+[\S\h]+)+)"

    @staticmethod
    def _docstring_reference():
        return r"^(?P<number>[[:digit:]]+)\.\h*(?P<reference>(?:(?:\n\h+)?[\S\h]+)+)"

    def collect(self, identifier: str, config: MutableMapping[str, Any]) -> CollectorItem:
        # if it's a module, import it, get all docstrings per function name
        # match functions to callables in zvm ops
        #
        # import zvm.zvm
        # zvm.zvm._static_ops['+'].__doc__
        #
        # import inspect
        # inspect.getdoc(zvm.zvm._static_ops['+'])
        # TODO: add kwarg for name

        imports: list[str] = config.get('imports', [])
        includes: dict[str, str] = config.get('includes', [])

        for module in imports:
            importlib.import_module(module)
        vm = zvm.zvm.ZVM()
        for routine, url in includes.items():
            vm._include(routine, url)

        re_filter = re.compile(config.get('filter', '.*'))
        ops = sorted(filter(re_filter.match, zvm.zvm._static_ops.keys()))

        docs: dict = {}
        for op_name in ops:
            op = zvm.zvm._static_ops[op_name]
            if callable(op):
                docstring = inspect.getdoc(op)
                sep_regex = r"(?:^|\n\n)"
                summary_regex = r"(?P<base>[\s\S]+?)"
                inputs_regex = rf"(?:{sep_regex}Inputs\n-{{6}}\n(?P<inputs>[\s\S]*?))"
                parameters_regex = rf"(?:{sep_regex}Parameters\n-{{10}}\n(?P<parameters>[\s\S]*?))"
                outputs_regex = rf"(?:{sep_regex}Outputs\n-{{7}}\n(?P<outputs>[\s\S]*?))"
                references_regex = rf"(?:{sep_regex}References\n-{{10}}\n(?P<references>[\s\S]*))"
                combined_regex = rf"^{summary_regex}??{inputs_regex}?{parameters_regex}?{outputs_regex}?{references_regex}?$"
                match = re.search(combined_regex, docstring)  # text being your example text
                matches = match.groupdict()
                # TODO: continue parsing to build hints
                docs[op_name]: dict = {}
            else:
                docs[op_name]: dict = op.get('hints', {})
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
