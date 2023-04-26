

# state variables
_routine_ops = [{}]
_routine_stacks = []
_routine_exes = []

# current routine pointers
ops: dict[str, dict] = _routine_ops[-1]
stack: list = None
exe: list[str] = None
