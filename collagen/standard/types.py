import collagen.vm as cvm


@cvm.method("asbool")
def asbool_(state: cvm.State):
    """
    Coerces the item at the top of the stack to a boolean value.

    Inputs
    ------
    x: Any
        The item to be converted to a boolean value.

    Outputs
    -------
    x_bool: bool
        x as a boolean value.
    """
    x = state.pop()
    return bool(x)


@cvm.method("asint")
def asint_(state: cvm.State):
    """
    Coerces the item at the top of the stack to an integer.

    Inputs
    ------
    x: Any
        The item to be converted to an integer.

    Outputs
    -------
    x_int: int
        x as an integer.
    """
    x = state.pop()
    return int(x)


@cvm.method("asfloat")
def asfloat_(state: cvm.State):
    """
    Coerces the item at the top of the stack to a float.

    Inputs
    ------
    x: Any
        The item to be converted to a float.

    Outputs
    -------
    x_float: float
        x as an float.
    """
    x = state.pop()
    return float(x)
