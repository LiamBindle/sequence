import pytest
import sequence.vm as svm
import json

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
    with open(path, 'r') as f:
        test: dict = json.load(f)
    checks_passed = svm.test(test)
    assert checks_passed > 0, "Nothing checked"


def test_bench_routine():
    path = "./tests/json/test-std-if.json"
    name = "std.if - iE-Ie-Ie"
    with open(path, 'r') as f:
        test: dict = json.load(f)
    checks_passed = svm.test(test, name)
    assert checks_passed > 0, "Nothing checked"
