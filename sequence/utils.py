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
