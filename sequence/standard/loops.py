import sequence.vm as svm


# looping
@svm.method("begin")
def begin_(state: svm.State):
    """
    Marks the beginning of a loop.
    """
    state._op_frame._begins.append(state._op_frame._pc)


@svm.method("repeat")
def repeat_(state: svm.State):
    """
    Marks the end of a loop.
    """
    state._op_frame._pc = state._op_frame._begins[-1]


@svm.method("break")
def break_(state: svm.State):
    """
    Breaks out of a loop (terminates the loop).
    """
    nested_loops = 0
    pc = state._op_frame._pc
    while pc < len(state._op_frame._run):
        pc += 1
        ex = state._op_frame._run[pc]
        if not isinstance(ex, dict):
            continue
        if 'op' not in ex:
            continue
        op = ex["op"]
        if op == 'begin':  # or any loop-start
            nested_loops += 1
        elif op == 'repeat':  # or any loop-end
            if nested_loops == 0:
                state._op_frame._pc = pc
                state._op_frame._begins.pop()
                return
            else:
                nested_loops -= 1

    # continue until repeat
    raise RuntimeError("Unterminated begin statement")


@svm.method("recurse")
def recurse(state: svm.State):
    """
    Restarts the current procedure.
    """
    state._op_frame._pc = -1


@svm.method("while")
def while_(state: svm.State):
    """
    Continues the loop if the item at the top of the stack is true. If the
    item at the top of the stack is not true, it terminates the loop.

    This method is useful for constructing traditional while-loops in a
    procedure.

    This method MUST be placed between `{"op": "begin"}` and `{"op": "repeat"}`.

    Inputs
    ------
    cond: bool, Any
        If true, the loop continues. If false, the loop terminates.
    """
    cond = state.pop()
    if not cond:
        break_(state)
