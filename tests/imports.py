import sequence.vm as svm


@svm.method("discard_if_neq")
def discard_if_neq(state: svm.State, *, value):
    a = state.pop()
    if a == value:
        return value


@svm.method("is_decreasing")
def is_decreasing(state: svm.State, *, argc: int):
    args = state.popn(argc)
    if len(args) == 0:
        return False
    c = args[0]
    lt = []
    for v in args[1:]:
        lt.append(v < c)
        c = v
    return all(lt)


@svm.method("pass_through")
def pass_through(state: svm.State, *, argc: int):
    args = state.popn(argc)
    return list(args)


@svm.method("check_local")
def check_local(state: svm.State, *, key, value):
    if state.has(key) and state.get(key) == value:
        return 1
    else:
        return 0


@svm.method("equals")
def equals_(state: svm.State):
    x, y = state.popn(2)
    return [x, x == y]


@svm.method("append_value_to_key")
def append_value_to_key(state: svm.State, *, key, value: int):
    d = state.pop()
    d[key].append(value)
    return d


@svm.method("change_key_value")
def change_key_value(state: svm.State, *, key, value):
    d = state.pop()
    d[key] = value
    return d


@svm.method("check_file_exists")
def check_file_exists(state: svm.State, *, path):
    import os.path
    return os.path.exists(path)
