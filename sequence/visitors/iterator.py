from .base import Visitor, Sequence
import sequence.static
from enum import IntFlag, auto


class IteratorMode(IntFlag):
    Sequence = auto()
    Method = auto()
    Data = auto()


class SequenceIterator(Visitor):
    def __init__(self, depth_first: bool = True, mode: IteratorMode = IteratorMode.Sequence, visit_root: bool = True):
        self.depth_first = depth_first
        self.mode = mode
        self.visit_root = visit_root

    def visit(self, seq: Sequence, depth: int = 0):
        subs: list[Sequence] = []
        if self.visit_root and depth == 0 and self.mode & IteratorMode.Sequence:
            yield seq

        for ex in seq.run:
            if isinstance(ex, dict) and ("op" in ex):
                op = sequence.static.ops.get(ex["op"])
                if isinstance(op, Sequence):
                    subs.append(op)
                    if self.mode & IteratorMode.Sequence:
                        yield op
                    if self.depth_first:
                        yield from self.visit(op, depth=depth+1)
                elif callable(op) and (self.mode & IteratorMode.Method):
                    yield op
            elif self.mode & IteratorMode.Data:
                yield ex

        if not self.depth_first:
            for sub in subs:
                yield from self.visit(sub, depth=depth+1)
