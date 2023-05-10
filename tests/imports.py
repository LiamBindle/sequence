import zvm
import zvm.state


@zvm.op("discard_if_neq")
def discard_if_neq(a, /, *, value):
    if a == value:
        return value


@zvm.op("is_increasing")
def is_increasing(*args):
    if len(args) == 0:
        return False
    c = args[0]
    gt = []
    for v in args[1:]:
        gt.append(v > c)
        c = v
    return all(gt)


@zvm.op("pass_through")
def pass_through(*args):
    return list(args)


@zvm.op("check_local")
def check_local(*, key, value):
    if zvm.state.local[key] == value:
        return 1
    else:
        return 0
