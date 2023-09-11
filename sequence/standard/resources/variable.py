from typing import Any
import urllib.parse
import urllib.request
import sequence


@sequence.getter(schemes='variables', media_type=None)
def get_variable(state: sequence.State, key, *, default: Any = None):
    """
    Loads a variable and places it at the top of stack.

    Parameters
    ----------
    [default]: Any (default: None)
        The default value if the variable doesn't exist.

    Outputs
    -------
    data: Any
        The variable.
    """
    path = urllib.parse.urlparse(key).path
    return state._frame.variables.get(path, default)


@sequence.putter(schemes='variables', media_type=None)
def put_variable(state: sequence.State, data, key):
    """
    Saves a variable (sequence-scope).
    """
    path = urllib.parse.urlparse(key).path
    state._frame.variables[path] = data


@sequence.deleter(schemes='variables')
def delete_variable(state: sequence.State, key):
    """
    Deletes a variable.
    """
    path = urllib.parse.urlparse(key).path
    del state._frame.variables[path]


@sequence.getter(schemes='parameters', media_type=None)
def get_parameter(state: sequence.State, key, *, default: Any = None):
    """
    Loads a parameter and places it at the top of stack.

    Parameters
    ----------
    [default]: Any (default: None)
        The default value if the parameter doesn't exist.

    Outputs
    -------
    data: Any
        The parameter.
    """
    path = urllib.parse.urlparse(key).path
    return state._frame.parameters.get(path, default)
