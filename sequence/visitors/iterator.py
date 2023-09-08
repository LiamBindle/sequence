from .base import Visitor, Sequence
import sequence.static
from enum import IntFlag, auto


class IteratorMode(IntFlag):
    Sequence = auto()
    Method = auto()
    Data = auto()


class SequenceIterator(Visitor):
    def __init__(self, depth_first: bool = True, mode: IteratorMode = IteratorMode.Sequence):
        self.depth_first = depth_first
        self.mode = mode

    def visit(self, seq: Sequence):
        subs: list[Sequence] = []
        for ex in seq.run:
            if isinstance(ex, dict) and ("op" in ex):
                op = sequence.static.ops.get(ex["op"])
                if isinstance(op, Sequence):
                    subs.append(op)
                    if self.mode & IteratorMode.Sequence:
                        yield op
                    if self.depth_first:
                        yield from self.visit(op)
                elif callable(op) and (self.mode & IteratorMode.Method):
                    yield op
            elif self.mode & IteratorMode.Data:
                yield ex

        if not self.depth_first:
            for sub in subs:
                yield from self.visit(sub)


class MethodIterator(Visitor):
    def __init__(self, depth_first: bool = False):
        self.depth_first = depth_first

    def visit(self, seq: Sequence):
        subs: list[Sequence] = []
        for ex in seq.run:
            if isinstance(ex, dict) and ("op" in ex) and callable(sequence.static.ops.get(ex["op"])):
                sub: Sequence = sequence.static.ops[ex["op"]]
                subs.append(sub)
                yield sub
                if self.depth_first:
                    yield from self.visit(sub)
        if not self.depth_first:
            for sub in subs:
                yield from self.visit(sub)
