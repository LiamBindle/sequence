import string
import sequence


# misc
@sequence.method("fstring")
def format_string(state: sequence.State, *, fmt: str, **params):
    """
    Formats a string.

    Parameters
    ----------
    fmt: str
        The format string (a python f-string). See the Python documentation of
        f-strings details.
    [**params]:
        Named arguments for the f-string.

    Inputs
    ------
    ...: Any
        The top N items are poped from the stack where N is the number of
        positional arguments in the f-string.

    Outputs
    -------
    result: str
        The formatted string.
    """
    formatter = string.Formatter()
    parsed_fmt = formatter.parse(fmt)
    format_nargs = 0
    format_params = set()
    for (_, field_name, _, _) in parsed_fmt:
        if field_name is None:
            # no replacement field
            continue
        if field_name == '' or field_name.isnumeric():
            format_nargs += 1
        else:
            format_params.add(field_name)
    args = state.popn(format_nargs)
    return fmt.format(*args, **params)


@sequence.method("assert")
def assert_(state: sequence.State, *, error: str = '', negate: bool = False):
    """
    Asserts that the item at the top of the stack is true. Terminates
    execution if false.

    Parameters
    ----------
    [error]: str
        The error message to print if the assertion fails.
    [negate]: bool (default: false)
        Assert that the item at the top of the stack if false (rather than
        true).

    Inputs
    ------
    cond: bool
        The boolean value to check.
    """
    x = state.pop()
    if negate:
        assert not x, error
    else:
        assert x, error
