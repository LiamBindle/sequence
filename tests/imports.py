import sequence


@sequence.method("discard_if_neq")
def discard_if_neq(state: sequence.State, *, value):
    a = state.pop()
    if a == value:
        return value


@sequence.method("is_decreasing")
def is_decreasing(state: sequence.State, *, argc: int):
    args = state.popn(argc)
    if len(args) == 0:
        return False
    c = args[0]
    lt = []
    for v in args[1:]:
        lt.append(v < c)
        c = v
    return all(lt)


@sequence.method("pass_through")
def pass_through(state: sequence.State, *, argc: int):
    args = state.popn(argc)
    return list(args)


@sequence.method("check_local")
def check_local(state: sequence.State, *, key, value):
    if state.has(key) and state.get(key) == value:
        return 1
    else:
        return 0


@sequence.method("equals")
def equals_(state: sequence.State):
    x, y = state.popn(2)
    return (x, x == y)


@sequence.method("append_value_to_key")
def append_value_to_key(state: sequence.State, *, key, value: int):
    d = state.pop()
    d[key].append(value)
    return d


@sequence.method("change_key_value")
def change_key_value(state: sequence.State, *, key, value):
    d = state.pop()
    d[key] = value
    return d


@sequence.method("check_file_exists")
def check_file_exists(state: sequence.State, *, path):
    import os.path
    return os.path.exists(path)
