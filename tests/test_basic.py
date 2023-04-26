from zvm.vm import run


def test_trivial_routine():
    routine = {
        "code": {
            "imports": {},
            "defs": {
                '+': {'fname': "op_add", "fexec": "def op_add(a, b): return a + b", "n": 2},
                '*': {'feval': "lambda a, b: [a*b]", "n": 2},
                'int': {'fname': 'make_int', 'fexec': "def make_int(*, value): return int(value)", "n": 0},
                'add2': {'f': lambda x: x+2, "n": 1},
                'comment': {},
            },
        },
        "exe": [
            [
                [[1, 2, {"op": "+"}]],
                {"op": "int", "value": 2},
                {"op": "*"}
            ],
            3,
            {"op": "+"},
            {"op": "comment", "message": "This is a test"},
            {"op": "add2"},
            1,
            {"op": "if", "true": [1], "false": [0]},
            {"op": "eval", "exe": [1, 2]}
        ]
    }

    result = run(routine)
    assert result == [11, 1, 1, 2]
