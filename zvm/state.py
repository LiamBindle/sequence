from typing import Any

# state variables
_routine_ops = [{}]
_routine_stacks = []
_routine_instructions = []
_routine_pc = []
_routine_begin_stacks = []
_routine_locals = [{}]
_routine_imports = [set()]

# current routine pointers
ops: dict[str, dict] = _routine_ops[-1]
stack: list = None
instr: list[str] = None
local_vars: dict[str, Any] = _routine_locals[-1]
global_vars: dict[str, Any] = {}

# global variables
loaders: dict[str, dict[str, callable]] = {}
storers: dict[str, dict[str, callable]] = {}
deleters: dict[str, dict[str, callable]] = {}
finished: bool = False


def restart():
    global _routine_ops
    global _routine_stacks
    global _routine_instructions
    global _routine_begin_stacks
    global _routine_pc
    global _routine_locals
    global _routine_imports
    global ops
    global stack
    global instr
    global local_vars
    global global_vars
    global loaders
    global storers
    global deleters
    global finished

    _routine_ops = [{}]
    _routine_stacks = []
    _routine_instructions = []
    _routine_begin_stacks = []
    _routine_pc = []
    _routine_locals = [{}]
    ops = _routine_ops[-1]
    stack = None
    instr = None
    local_vars = _routine_locals[-1]
    global_vars = {}
    loaders = {}
    storers = {}
    deleters = {}
    finished = False
    _routine_imports = [set()]
