import collagen.vm as cvm


@cvm.op("discard_if_neq")
def discard_if_neq(state: cvm.State, *, value):
    a = state.pop()
    if a == value:
        return value


@cvm.op("is_decreasing")
def is_decreasing(state: cvm.State, *, argc: int):
    args = state.popn(argc)
    if len(args) == 0:
        return False
    c = args[0]
    lt = []
    for v in args[1:]:
        lt.append(v < c)
        c = v
    return all(lt)


@cvm.op("pass_through")
def pass_through(state: cvm.State, *, argc: int):
    args = state.popn(argc)
    return list(args)


@cvm.op("check_local")
def check_local(state: cvm.State, *, key, value):
    if state.has(key) and state.get(key) == value:
        return 1
    else:
        return 0


@cvm.op("equals")
def equals_(state: cvm.State):
    x, y = state.popn(2)
    return [x, x == y]


@cvm.op("append_value_to_key")
def append_value_to_key(state: cvm.State, *, key, value: int):
    d = state.pop()
    d[key].append(value)
    return d


@cvm.op("change_key_value")
def change_key_value(state: cvm.State, *, key, value):
    d = state.pop()
    d[key] = value
    return d


@cvm.op("check_file_exists")
def check_file_exists(state: cvm.State, *, path):
    import os.path
    return os.path.exists(path)
