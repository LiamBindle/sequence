from typing import List, Any, Union, Callable, Generator
from dataclasses import dataclass, field
import copy
import importlib
import urllib.parse
import re
import datetime
import ast
import sys
import urllib.request
import urllib.parse
import pathlib
import logging


_static_ops: dict[str, Union[dict, Callable]] = {}
_static_getters: dict[str, dict[str, Callable]] = {}
_static_ext_getter: dict[str, dict[str, Callable]] = {}
_static_putters: dict[str, dict[str, Callable]] = {}
_static_deleters: dict[str, dict[str, Callable]] = {}
_static_copiers = {}

_logger = logging.getLogger('sequence')


class Visitor:
    def _dereference(self, data: Union[str, list, dict]):
        if isinstance(data, str):
            if ref := re.match(r"^\$\{([a-zA-Z0-9\+\-\.]+):([^}]+)\}$", data):
                scheme = ref.group(1)
                uri = f'{scheme}:{ref.group(2)}'
                state = State(self)
                return _static_getters[scheme][None](state, uri)
            else:
                return data
        elif isinstance(data, list):
            for i, v in enumerate(data):
                data[i] = self._dereference(v)
            return data
        elif isinstance(data, dict):
            for k, v in data.items():
                data[k] = self._dereference(v)
            return data
        else:
            return data

    def visit(self, sequence: 'Sequence'):
        pass


@dataclass(frozen=True)
class Sequence:
    toolkits: list[str] = field(default_factory=list)
    include: dict[str, Union[str, dict]] = field(default_factory=dict)
    run: list[Any] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    tests: list[dict] = field(default_factory=list)


class SequenceLoader(Visitor):
    def __init__(self, parameters: dict = None, recurse: bool = False):
        self.parameters = parameters or {}
        self.recurse = recurse

    def visit(self, sequence: Sequence):
        global _static_ops
        for toolkit in sequence.toolkits:
            importlib.import_module(toolkit)
        for name, url_or_seq in sequence.include.items():
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
            _static_ops[name] = seq

    @staticmethod
    def load(url: str) -> Sequence:
        importlib.import_module("sequence.standard")
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme == '' and pathlib.Path(url).exists():
            path = url
            return SequenceLoader.load(f'file:{path}')
        extension = pathlib.Path(parsed_url.path).suffix
        _logger.debug(f'GET {url}  (scheme: {parsed_url.scheme}, ext: {extension})')
        data = _static_ext_getter[parsed_url.scheme][extension](None, url)
        return Sequence(**data)


class SequenceFrame(Visitor):
    def __init__(self, name: str = 'root', parent: 'SequenceFrame' = None, parameters: dict = None):
        self.name = name
        self.parent = parent
        if parent is None:
            self.variables = {}
            self.stack = []
            self.started_at = datetime.datetime.utcnow()
        else:
            self.variables = copy.copy(parent.variables)
            self.stack = parent.stack
            self.started_at = parent.started_at
        self.pc: int = 0
        self.begins: List[int] = []
        self.parameters: dict = parameters or {}
        self.run: list = []

    @property
    def _breadcrumb(self) -> str:
        runner = self
        runners = []
        while runner is not None:
            runners.append(f'{runner.name}.{runner.pc}')
            runner = runner.parent
        return ':'.join(reversed(runners))

    def _elapsed_time(self, since: datetime.datetime = None) -> str:
        elapsed = datetime.datetime.utcnow() - (since or self.started_at)
        t = elapsed.total_seconds()
        seconds = t % 60
        minutes = int(t//60) % 60
        hours = int(t//3600)
        elapsed = ""
        if hours:
            elapsed += f"{hours:d}h"
        if minutes:
            elapsed += f"{minutes: 2d}m"
        elapsed += f"{seconds: 6.3f}"[:6] + "s"
        return elapsed

    def visit(self, sequence: Sequence):
        self.variables.update(sequence.defaults)
        self.run = sequence.run

        while self.pc < len(sequence.run):
            ex = sequence.run[self.pc]

            if isinstance(ex, dict) and "op" in ex:
                # ex in an op
                name = ex['op']
                op = _static_ops[name]

                size_before = len(self.stack)
                _logger.debug(f'Starting [{self._breadcrumb}] total elapsed: {self._elapsed_time()}, stack size: {size_before}')
                time_before = datetime.datetime.utcnow()

                if isinstance(op, Sequence):
                    parameters = {}
                    missing_parameters = []
                    for param_name, param_def in op.metadata.get("parameters", {}).items():
                        is_required = (not param_def.get("optional", False)) and ("default" not in param_def)
                        if is_required and param_name not in ex and param_name not in parameters:
                            missing_parameters.append(param_name)
                        if param_name in ex:
                            parameters[param_name] = ex[param_name]
                        elif "default" in param_def:
                            parameters[param_name] = param_def["default"]
                    if missing_parameters:
                        raise TypeError(f'procedure "{name}" missing {len(missing_parameters)} parameter(s): {", ".join([f"{p}" for p in missing_parameters])}')
                    parameters = self._dereference(parameters)

                    child = SequenceFrame(name=name, parent=self, parameters=parameters)
                    child.visit(op)
                    result = None  # child.run will have updated the stack
                else:
                    assert callable(op), "internal error"
                    parameters = {k: v for k, v in ex.items() if k != "op"}
                    parameters = self._dereference(parameters)
                    state = State(self)
                    result = op(state, **parameters)  # methods run within current frame

                size_delta = len(self.stack) - size_before
                stack_delta = '0' if size_delta == 0 else (f'+{size_delta}' if size_delta > 0 else f'{size_delta}')
                _logger.debug(f'Finished [{self._breadcrumb}] incl. elapsed: {self._elapsed_time(since=time_before)}, stack delta: +{stack_delta}')
            else:
                # is a literal
                result = ex
                name = None

            if isinstance(result, list):
                self.stack.extend(result)
            elif result is not None:
                self.stack.append(result)
            self.pc += 1


class State:
    def __init__(self, frame: SequenceFrame) -> None:
        self._frame = frame
        self._started_at = datetime.datetime.utcnow()

    def push(self, value: Any):
        self._frame.stack.append(value)

    def pop(self) -> Any:
        if len(self._frame.stack) == 0:
            raise RuntimeError("Cannot pop from empty stack")
        return self._frame.stack.pop()

    def popn(self, n: int) -> List[Any]:
        if n > len(self._frame.stack):
            raise RuntimeError("Cannot pop from empty stack")
        return [self._frame.stack.pop() for _ in range(n)][::-1]

    def set(self, key: str, value: Any):
        self._frame.variables[key] = value

    def has(self, key) -> bool:
        return key in self._frame.variables

    def get(self, key: str) -> Any:
        if key not in self._frame.variables:
            raise RuntimeError(f"Variable has not been set: {key}")
        return self._frame.variables[key]

    def delete(self, key):
        del self._frame.variables[key]


def test(sequence: Sequence):
    tests_passed = 0
    for test in sequence.tests:
        test_name = test.get("name", "unnamed-test")

        loader = SequenceLoader(recurse=True)
        loader.visit(sequence)

        frame = SequenceFrame()
        frame.stack = test.get("init", [])
        frame.visit(sequence)

        if "answer" in test:
            assert frame.stack == test["answer"], f"Test failed: {test_name}. Answer: {test['answer']}. Result: {frame.stack}."
        else:
            assert len(sequence.run) > 0, f"Test failed: {test_name}. Nothing was run."
        tests_passed += 1
    return tests_passed


def method(name):
    global _static_ops
    def inner(func: Callable):
        global _static_ops
        if func.__code__.co_argcount != 1:
            raise RuntimeError("function must take exactly one position argument (state: svm.State)")
        _static_ops[name] = func
        return func
    return inner


def getter(*, schemes: Union[str, list[str]], media_type: str, extensions: Union[str, list[str]] = []):
    global _static_getters, _static_ext_getter
    if isinstance(schemes, str):
        schemes = [schemes]
    if isinstance(extensions, str):
        extensions = [extensions]

    def inner(func: Callable):
        global _static_getters, _static_ext_getter
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position arguments (state: svm.State, url: str)")
        for scheme in schemes:
            if scheme not in _static_getters:
                _static_getters[scheme] = {}
            _static_getters[scheme][media_type] = func

            if scheme not in _static_ext_getter:
                _static_ext_getter[scheme] = {}
            for ext in extensions:
                _static_ext_getter[scheme][ext] = func

        return func
    return inner


def putter(*, schemes: Union[str, list[str]], media_type: str):
    global _static_putters
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: Callable):
        global _static_putters
        if func.__code__.co_argcount != 3:
            raise RuntimeError("function must take exactly three position argument (state: svm.State, data: Any, url: str)")
        for scheme in schemes:
            if scheme not in _static_putters:
                _static_putters[scheme] = {}
            _static_putters[scheme][media_type] = func
        return func
    return inner


def deleter(*, schemes: Union[str, list[str]], media_type: str = None):
    global _static_deleters
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: Callable):
        global _static_deleters
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position argument (state: svm.State, url: str)")
        for scheme in schemes:
            if scheme not in _static_deleters:
                _static_deleters[scheme] = {}
            _static_deleters[scheme][media_type] = func
        return func
    return inner


def copier(*, types: Union[type, List[type]]):
    global _static_copiers
    if isinstance(types, type):
        types = [types]

    def inner(func: Callable):
        global _static_copiers
        if func.__code__.co_argcount != 2:
            raise RuntimeError("function must take exactly two position argument (data: object, deep: bool)")
        for t in types:
            _static_copiers[t] = func
        return func
    return inner
