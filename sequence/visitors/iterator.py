from .base import Visitor, Sequence
import sequence.static


class SequenceIterator(Visitor):
    def __init__(self, depth_first: bool = False):
        self.depth_first = depth_first

    def visit(self, seq: Sequence):
        subs: list[Sequence] = []
        for ex in seq.run:
            if isinstance(ex, dict) and ("op" in ex) and isinstance(sequence.static.ops.get(ex["op"]), Sequence):
                sub: Sequence = sequence.static.ops[ex["op"]]
                subs.append(sub)
                yield sub
                if self.depth_first:
                    yield from self.visit(sub)
        if not self.depth_first:
            for sub in subs:
                yield from self.visit(sub)
