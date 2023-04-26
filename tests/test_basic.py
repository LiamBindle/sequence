from zvm.vm import run


def test_trivial_routine():
    routine = {
        "code": {
            "imports": [],
            "defs": {  # place to define new routines
                '+': {'name': "op_add", "exec": "def op_add(a, b): return a + b", "n": 2},
                '*': {'eval': "lambda a, b: [a*b]", "n": 2},  # routine defined by eval
                'int': {'name': 'make_int', 'exec': "def make_int(*, value): return int(value)", "n": 0},  # routine defined by exec
                'add2': {'eval': 'lambda x: x+2', "n": 1},  # routine defined by callable
                'add3': {'instr': [3, {"op": "+"}], "n": 1},  # stack routine with 1 argument
                'comment': {},
            },
            # define-types,
        },
        "instr": [
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
            {"op": "run", "instr": [1, 2]},  # anonymous routine
            {"op": "add3"},
            {"op": "assert", "size": 4, "eq": [5, 1, 1, 11]},
            {"op": "assert", "end": 2, "size": 2, "eq": [5, 1]},
        ]
    }

    result = run(routine)
    assert result == [11, 1, 1, 5]
