import importlib
import urllib.parse
import pathlib
from .base import Visitor, Sequence
import sequence.static

# TODO: add warning for redefeinition


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
                url_or_seq = url_or_seq  #self._dereference(url_or_seq)  # TODO: remove because include should not be dereferenceable (can also move dereference to SequenceFrame)
            if isinstance(url_or_seq, str):
                seq = self.load(url_or_seq)
                seq.metadata['origin'] = url_or_seq
            elif isinstance(url_or_seq, dict):
                seq = Sequence(**url_or_seq)
            else:
                raise RuntimeError("include is not a url (str) or an op (dict)")
            if self.recurse:
                self.visit(seq)
            seq.metadata['name'] = name
            sequence.static.ops[name] = seq

    @staticmethod
    def load(url: str, name: str = None) -> Sequence:
        importlib.import_module("sequence.standard")
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme == '' and pathlib.Path(url).exists():
            path = url
            return SequenceLoader.load(f'file:{path}')
        extension = pathlib.Path(parsed_url.path).suffix
        sequence.static.logger.debug(f'GET {url}  (scheme: {parsed_url.scheme}, ext: {extension})')
        data = sequence.static.ext_getter[parsed_url.scheme][extension](None, url)
        seq = Sequence(**data)
        seq.metadata['origin'] = url
        if name is not None:
            seq.metadata['name'] = name
            sequence.static.ops[name] = seq
        return seq

    @staticmethod
    def load_toolkit(toolkit: str):
        importlib.import_module(toolkit)


def load(url: str, parameters: dict = {}) -> Sequence:
    seq = SequenceLoader.load(url)
    loader = SequenceLoader(parameters, recurse=True)
    loader.visit(seq)
    return seq
