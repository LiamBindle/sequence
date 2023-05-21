import zvm
import zvm.state


@zvm.op("discard_if_neq")
def discard_if_neq(a, /, *, value):
    if a == value:
        return value


@zvm.op("is_decreasing")
def is_decreasing(*args):
    if len(args) == 0:
        return False
    c = args[0]
    lt = []
    for v in args[1:]:
        lt.append(v < c)
        c = v
    return all(lt)


@zvm.op("pass_through")
def pass_through(*args):
    return list(args)


@zvm.op("check_local")
def check_local(*, key, value):
    if zvm.state.local_vars[key] == value:
        return 1
    else:
        return 0
