from typing import Any, Mapping, MutableMapping, Optional, List
from mkdocstrings.handlers.base import BaseHandler, CollectorItem
import fnmatch
import inspect

import urllib.parse
import importlib
import re

from sequence.visitors.load import SequenceLoader
from sequence.docs import getter_doc, putter_doc, deleter_doc, op_doc


def add_hyperlinks_to_descriptions(metadata):
    if 'description' in metadata and 'references' in metadata:
        for i, ref in enumerate(metadata['references']):
            if 'url' not in ref:
                continue
            metadata['description'] = metadata['description'].replace(f"[{i+1}]", f'<a href="{ref["url"]}" target="_blank">[{i+1}]</a>')
    return metadata


class SequenceHandler(BaseHandler):
    def __init__(self, handler, theme, custom_templates) -> None:
        self.fallback_theme = 'terminal'
        super().__init__(handler, theme, custom_templates)

    def collect(self, identifier: str, config: MutableMapping[str, Any]) -> CollectorItem:
        for name, path in config.get('includes', {}).items():
            SequenceLoader.load(path, name)

        for toolkit in config.get('toolkits', []):
            SequenceLoader.load_toolkit(toolkit)

        # load

        docs: dict = {
            'op_names': [],
            'op_metadata': [],
            'data_op': [],
            'data_op_metadata': [],
            'data_op_scheme': [],
            'data_op_media_type': [],
        }
        for op in config.get('ops', []):
            docs['op_names'].append(op)
            docs['op_metadata'].append(op_doc(op))

        for data_spec in config.get("data", []):
            if ":" in data_spec:
                scheme, media_type = data_spec.split(":")
            else:
                scheme = data_spec
                media_type = None

            for op, func in zip(['get', 'put', 'del'], [getter_doc, putter_doc, deleter_doc]):
                doc = func(scheme, media_type)
                if doc is not None:
                    docs['data_op'].append(op)
                    docs['data_op_metadata'].append(doc)
                    docs['data_op_scheme'].append(scheme)
                    docs['data_op_media_type'].append(media_type)
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
        theme=kwargs.get('theme'),
        custom_templates=kwargs.get('custom_templates')
    )
