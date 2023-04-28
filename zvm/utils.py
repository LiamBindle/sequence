import inspect
import zvm.state


def op(name):
    def inner(func: callable):
        signature = inspect.signature(func)
        # validate expression
        n = 0
        for param_name, param_value in signature.parameters.items():
            if param_value.kind == inspect.Parameter.POSITIONAL_ONLY:
                n += 1
                assert param_value.default == inspect.Parameter.empty, f"definition of '{func.__name__}' sets a default value for the positional argument '{param_name}' (not allowed)"
            else:
                break
        zvm.state.ops[name] = {'f': func, "n": n}
        return func
    return inner


def uri_scheme(*, schemes: str | list[str], content_type: str):
    if isinstance(schemes, str):
        schemes = [schemes]

    def inner(func: callable):
        for scheme in schemes:
            if scheme not in zvm.state.fetchers:
                zvm.state.fetchers[scheme] = {}
            zvm.state.fetchers[scheme][content_type] = func
        return func
    return inner
