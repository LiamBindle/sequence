import pytest
import sequence
import json

from sequence.visitors.tester import SequenceTester

TEST_FILES = [
    "./tests/json/test-import.json",
    "./tests/json/test-include.json",
    "./tests/json/test-variables.json",
    "./tests/json/test-std-if.json",
    "./tests/json/test-recurse.json",
    "./tests/json/test-std-begin.json",
    "./tests/json/test-std-while.json",
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
