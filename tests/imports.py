import zvm


@zvm.op("discard_if_neq")
def discard_if_neq(state: zvm.State, *, value):
    a = state.pop()
    if a == value:
        return value


@zvm.op("is_decreasing")
def is_decreasing(state: zvm.State, *, argc: int):
    args = state.popn(argc)
    if len(args) == 0:
        return False
    c = args[0]
    lt = []
    for v in args[1:]:
        lt.append(v < c)
        c = v
    return all(lt)


@zvm.op("pass_through")
def pass_through(state: zvm.State, *, argc: int):
    args = state.popn(argc)
    return list(args)


@zvm.op("check_local")
def check_local(state: zvm.State, *, key, value):
    if state.has(key) and state.get(key) == value:
        return 1
    else:
        return 0
