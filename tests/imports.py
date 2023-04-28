import zvm


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
