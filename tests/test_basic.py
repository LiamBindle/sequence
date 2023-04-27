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


def test_trivial_include():
    routine = {
        "includes": [
            "file:./tests/data/include-1.json"
        ],
        "instr": [
            1,
            {"op": "plus5"},
            {"op": "assert", "eq": [6]},
        ]
    }

    assert run(routine)

    # {
    #     "include": [
    #         # must be uri, but uri scheme is extensible
    #         {"$ref": "#/other-code/code-1.json"}  # .inst, .code, and .conf are initialized by includes, overriden by .
    #     ],
    #     "conf": {  # todo: a routine can modify the config
    #         "debug": True,
    #         "progress": False,
    #         "run.until": "next|next-in|next-out|checkpoint|eof"
    #     },
    #     "tests": [  # todo: a routine can have tests
    #         {
    #             "name": "simple",
    #             "fixture": {"op": "run"},  # result is passed to test
    #             "instr": [],  # the test
    #         }
    #     ]
    # }

    # recursive functions via "op": "."; need zvm.call(op, **kwargs) -- take current logic in run

# def test_dereference():
#     d = {
#         "a": {"value": 1},
#         "b": {"$ref": "#/a"},
#         "c": [{"$ref": "#/a"}],
#         "d": [[{"a": [{"$ref": "#/c"}]}]]
#     }
#     answer = {
#         "a": {"value": 1},
#         "b": {"value": 1},
#         "c": [{"value": 1}],
#         "d": [[{"a": [{"value": 1}]}]]
#     }
#     import jsonref
#     json = """{
#     "include": [
#         {"$ref": "/home/liam/zvm/test.json"}
#     ]
#     }
#     """
    
#     x = jsonref.loads(json)
#     print(x)
