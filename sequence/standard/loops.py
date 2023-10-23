import sequence


# looping
@sequence.method("begin")
def begin_(state: sequence.State):
    """
    Marks the beginning of a loop.
    """
    state._frame.begins.append(state._frame.pc)


@sequence.method("repeat")
def repeat_(state: sequence.State):
    """
    Marks the end of a loop.
    """
    state._frame.pc = state._frame.begins[-1]


@sequence.method("continue")
def continue_(state: sequence.State):
    """
    Skips to the next loop iteration.
    """
    state._frame.pc = state._frame.begins[-1]


@sequence.method("break")
def break_(state: sequence.State):
    """
    Breaks out of a loop (terminates the loop).
    """
    nested_loops = 0
    pc = state._frame.pc
    while pc < len(state._frame.run):
        pc += 1
        ex = state._frame.run[pc]
        if not isinstance(ex, dict):
            continue
        if 'op' not in ex:
            continue
        op = ex["op"]
        if op == 'begin':  # or any loop-start
            nested_loops += 1
        elif op == 'repeat':  # or any loop-end
            if nested_loops == 0:
                state._frame.pc = pc
                state._frame.begins.pop()
                return
            else:
                nested_loops -= 1

    # continue until repeat
    raise RuntimeError("Unterminated begin statement")


@sequence.method("recurse")
def recurse(state: sequence.State):
    """
    Restarts the current sequence.
    """
    state._frame.pc = -1


@sequence.method("while")
def while_(state: sequence.State):
    """
    Continues the loop if the item at the top of the stack is true. If the
    item at the top of the stack is not true, it terminates the loop.

    This method is useful for constructing traditional while-loops in a
    sequence.

    This method MUST be placed between `{"op": "begin"}` and `{"op": "repeat"}`.

    Inputs
    ------
    cond: bool, Any
        If true, the loop continues. If false, the loop terminates.
    """
    cond = state.pop()
    if not cond:
        break_(state)


@sequence.method("foreach")
def foreach_(state: sequence.State):
    """
    Loops through each element of an iterable. The next element is placed at the
    TOS at the start of each loop.

    This method MUST be placed between `{"op": "begin"}` and `{"op": "repeat"}`.
    Usually, this method comes immediately after `{"op": "begin"}`.

    Inputs
    ------
    [iterable]: list, iterable
        The thing that is iterated through. This input only applies to initializing
        the loop.

    Outputs
    -------
    element: Any
        The next element.
    """
    key = f'/_foreach/{state._frame._breadcrumb}'
    keep_alive_key = f'{key}/keep-alive'
    if state.has(key):
        # continue loop
        it = state.get(key)
        try:
            return next(it)
        except StopIteration:
            state.delete(key)
            state.delete(keep_alive_key)
            break_(state)
    else:
        # start loop
        iterable = state.pop()
        it = iter(iterable)
        state.set(key, it)
        state.set(keep_alive_key, iterable)  # avoids destructor call
        try:
            return next(it)
        except StopIteration:
            state.delete(key)
            break_(state)
