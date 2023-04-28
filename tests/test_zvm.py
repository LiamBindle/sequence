import pytest
import zvm.vm
import zvm.state
import json

TEST_FILES = [
    "./tests/json/test-import.json",
    "./tests/json/test-include.json",
    "./tests/json/test-argument-order.json",
    "./tests/json/test-routine-definition.json",
]


@pytest.mark.parametrize("path", TEST_FILES)
def test_all(path):
    with open(path, 'r') as f:
        test: dict = json.load(f)
    zvm.vm.run_test(test)
    assert zvm.state.finished, "Nothing ran"


def test_bench_routine():
    path = "./tests/json/test-argument-order.json"
    name = "op.argorder - 3"
    with open(path, 'r') as f:
        test: dict = json.load(f)
    zvm.vm.run_test(test, name)
    assert zvm.state.finished, "Nothing ran"
