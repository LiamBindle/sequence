import pytest
import sequence
import json


from sequence.visitors.tester import SequenceTester
from sequence.visitors.load import SequenceLoader
from sequence.visitors.iterator import SequenceIterator, IteratorMode
import sequence.standard.operators

TEST_FILES = [
    "./tests/json/test-import.json",
    "./tests/json/test-include.json",
    "./tests/json/test-variables.json",
    "./tests/json/test-std-if.json",
    "./tests/json/test-recurse.json",
    "./tests/json/test-std-begin.json",
    "./tests/json/test-std-while.json",
    "./tests/json/test-std-foreach.json",
    "./tests/json/test-std-algebra.json",
    "./tests/json/test-std-bool.json",
    "./tests/json/test-std-compare.json",
    "./tests/json/test-std-stack.json",
    "./tests/json/test-std-fstring.json",
    "./tests/json/test-std-pack-kwargs.json",
    "./tests/json/test-std-load-store-delete.json",
    "./tests/json/test-parameters.json",
    "./tests/json/test-dereference.json",
]


@pytest.mark.parametrize("path", TEST_FILES)
def test_all(path):
    seq = sequence.load(path)
    tester = SequenceTester()
    tester.visit(seq)


def test_iter():
    root = sequence.load("tests/json/test-iter.json")

    loader = SequenceLoader(recurse=True)
    loader.visit(root)

    seq: sequence.Sequence

    # test sequences
    answer = [
        "nest1",
        "nest2",
        "nest1.1",
        "nest1.2",
        "nest2.1",
        "nest2.2",
        "nest2.1.1",
    ]
    it = SequenceIterator(depth_first=False, visit_root=False)
    for i, seq in enumerate(it.visit(root)):
        assert seq.metadata.get("name") == answer[i]

    answer = [
        "nest1",
        "nest1.1",
        "nest1.2",
        "nest2",
        "nest2.1",
        "nest2.1.1",
        "nest2.2",
    ]
    it = SequenceIterator(depth_first=True, visit_root=False)
    for i, seq in enumerate(it.visit(root)):
        assert seq.metadata.get("name") == answer[i]

    # test methods
    answer = [
        sequence.standard.operators.plus,
        sequence.standard.operators.not_equal,
    ]
    it = SequenceIterator(depth_first=True, mode=IteratorMode.Method, visit_root=False)
    for i, meth in enumerate(it.visit(root)):
        assert meth is answer[i]

    answer = [
        sequence.standard.operators.not_equal,
        sequence.standard.operators.plus,
    ]
    it = SequenceIterator(depth_first=False, mode=IteratorMode.Method, visit_root=False)
    for i, meth in enumerate(it.visit(root)):
        assert meth is answer[i]

    # test data
    answer = [1, 2, 3]
    it = SequenceIterator(depth_first=True, mode=IteratorMode.Data, visit_root=False)
    for i, meth in enumerate(it.visit(root)):
        assert meth is answer[i]

    answer = [1, 3, 2]
    it = SequenceIterator(depth_first=False, mode=IteratorMode.Data, visit_root=False)
    for i, meth in enumerate(it.visit(root)):
        assert meth is answer[i]
