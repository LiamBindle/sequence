from .base import Visitor, Sequence
from .load import SequenceLoader
from .run import SequenceFrame


class SequenceTester(Visitor):
    def __init__(self, parameters: dict = {}) -> None:
        self.parameters = parameters

    def visit(self, seq: Sequence):
        tests_passed = 0
        for test in seq.tests:
            test_name = test.get("name", "unnamed-test")

            loader = SequenceLoader(recurse=True)
            loader.visit(seq)

            frame = SequenceFrame(parameters=self.parameters)
            frame.stack = test.get("init", [])
            frame.visit(seq)

            if "answer" in test:
                assert frame.stack == test["answer"], f"Test failed: {test_name}. Answer: {test['answer']}. Result: {frame.stack}."
            else:
                assert len(seq.run) > 0, f"Test failed: {test_name}. Nothing was run."
            tests_passed += 1
        assert tests_passed > 0, "No tests were run"
