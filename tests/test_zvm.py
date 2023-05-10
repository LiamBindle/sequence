import pytest
import zvm.vm
import zvm.state
import json

TEST_FILES = [
    "./tests/json/test-import.json",
    "./tests/json/test-import-repeated.json",
    "./tests/json/test-include.json",
    "./tests/json/test-argument-order.json",
    "./tests/json/test-local.json",
    "./tests/json/test-routine-definition.json",
    "./tests/json/test-std-if.json",
    "./tests/json/test-recurse.json",
    "./tests/json/test-std-begin.json",
    "./tests/json/test-std-algebra.json",
    "./tests/json/test-std-bool.json",
    "./tests/json/test-std-compare.json",
    "./tests/json/test-std-stack.json",
    "./tests/json/test-std-fstring.json",
    "./tests/json/test-std-load-store-delete.json",
]


@pytest.mark.parametrize("path", TEST_FILES)
def test_all(path):
    with open(path, 'r') as f:
        test: dict = json.load(f)
    zvm.vm.run_test(test)
    assert zvm.state.finished, "Nothing ran"


def test_bench_routine():
    path = "./tests/json/test-std-begin.json"
    name = "std.begin - 11..44"
    with open(path, 'r') as f:
        test: dict = json.load(f)
    zvm.vm.run_test(test, name)
    assert zvm.state.finished, "Nothing ran"
