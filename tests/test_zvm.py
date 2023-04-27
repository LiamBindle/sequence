import pytest
import zvm.vm
import zvm.state
import json

TEST_FILES = [
    "./tests/json/include-2.json"
]


@pytest.mark.parametrize("path", TEST_FILES)
def test_all(path):
    with open(path, 'r') as f:
        test: dict = json.load(f)
    zvm.vm.run_test(test)
    assert zvm.state.finished, "Nothing ran"


def test_bench_routine():
    path = "./tests/json/include-2.json"
    name = "trivial"
    with open(path, 'r') as f:
        test: dict = json.load(f)
    zvm.vm.run_test(test, name)
    assert zvm.state.finished, "Nothing ran"
