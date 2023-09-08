import importlib
import urllib.parse
import pathlib
from .base import Visitor, Sequence
import sequence.static


class SequenceLoader(Visitor):
    def __init__(self, parameters: dict = None, recurse: bool = False):
        self.parameters = parameters or {}
        self.recurse = recurse

    def visit(self, seq: Sequence):
        # global _static_ops
        for toolkit in seq.toolkits:
            importlib.import_module(toolkit)
        for name, url_or_seq in seq.include.items():
            if isinstance(url_or_seq, str):
                url_or_seq = self._dereference(url_or_seq)
            if isinstance(url_or_seq, str):
                seq = self.load(url_or_seq)
            elif isinstance(url_or_seq, dict):
                seq = Sequence(**url_or_seq)
            else:
                raise RuntimeError("include is not a url (str) or an op (dict)")
            if self.recurse:
                self.visit(seq)
            sequence.static.ops[name] = seq

    @staticmethod
    def load(url: str) -> Sequence:
        importlib.import_module("sequence.standard")
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme == '' and pathlib.Path(url).exists():
            path = url
            return SequenceLoader.load(f'file:{path}')
        extension = pathlib.Path(parsed_url.path).suffix
        sequence.static.logger.debug(f'GET {url}  (scheme: {parsed_url.scheme}, ext: {extension})')
        data = sequence.static.ext_getter[parsed_url.scheme][extension](None, url)
        return Sequence(**data)


def load(url: str) -> Sequence:
    return SequenceLoader.load(url)
