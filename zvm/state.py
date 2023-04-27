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
