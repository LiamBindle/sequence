import sequence


@sequence.method("if")
def if_(state: sequence.State):
    """
    Marks the beginning of an if-block. An if statment MUST be terminated by `{"op": "endif"}`.

    Inputs
    ------
    cond: bool, Any
        If true, the if-block is evaluated. If false, the else-block is
        evaluated if it exists.
    """
    cond = state.pop()
    if cond:
        return
    # set PC to address to else/endif
    nested_branches = 0
    pc = state._frame.pc
    while pc < len(state._frame.run):
        pc += 1
        ex = state._frame.run[pc]
        if not isinstance(ex, dict):
            continue
        if 'op' not in ex:
            continue
        op = ex["op"]
        if op == 'if':
            nested_branches += 1
        elif nested_branches == 0 and (op == 'else' or op == 'endif'):
            state._frame.pc = pc
            return
        elif op == 'endif':
            nested_branches -= 1

    raise RuntimeError("Unterminated if statement")


@sequence.method("else")
def else_(state: sequence.State):
    """
    Marks the beginning of an else-block. This method MUST be placed between
    `{"op": "if"}` and `{"op": "endif"}`.
    """
    # set PC to address to else/endif
    nested_branches = 0
    pc = state._frame.pc
    while pc < len(state._frame.run):
        pc += 1
        ex = state._frame.run[pc]
        if not isinstance(ex, dict):
            continue
        if 'op' not in ex:
            continue
        op = ex["op"]
        if op == 'if':
            nested_branches += 1
        elif op == 'else':
            if nested_branches == 0:
                raise RuntimeError("Unbound else")
            else:
                nested_branches -= 1
        elif op == 'endif' and nested_branches == 0:
            state._frame.pc = pc
            return
    raise RuntimeError("Unterminated if statement")


@sequence.method("endif")
def endif_(state: sequence.State):
    """
    Marks the end of an if statement.
    """
    # noop
    pass
