from typing import Any

# state variables
_routine_ops = [{}]
_routine_stacks = []
_routine_instructions = []
_routine_confs = [{}]

# current routine pointers
ops: dict[str, dict] = _routine_ops[-1]
stack: list = None
instr: list[str] = None
conf: dict[str, Any] = _routine_confs[-1]

# global variables
fetchers: dict[str, dict[str, callable]] = {}
finished: bool = False


def restart():
    global _routine_ops
    global _routine_stacks
    global _routine_instructions
    global _routine_confs
    global ops
    global stack
    global instr
    global conf
    global fetchers
    global finished

    _routine_ops = [{}]
    _routine_stacks = []
    _routine_instructions = []
    _routine_confs = [{}]
    ops = _routine_ops[-1]
    stack = None
    instr = None
    conf = _routine_confs[-1]
    fetchers = {}
    finished = False
