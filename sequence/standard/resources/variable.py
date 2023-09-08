from typing import Any
import urllib.parse
import urllib.request
import sequence.vm as svm


@svm.getter(schemes='variables', media_type=None)
def get_variable(state: svm.State, key, *, default: Any = None):
    """
    Loads a variable and places it at the top of stack.

    Parameters
    ----------
    [default]: Any (default: None)
        The default value if the variable doesn't exist.

    Outputs
    -------
    data: Any
        The local variable.
    """
    path = urllib.parse.urlparse(key).path
    return state._frame.variables.get(path, default)


@svm.putter(schemes='variables', media_type=None)
def put_variable(state: svm.State, data, key):
    """
    Saves a local variable (procedure-scope).
    """
    path = urllib.parse.urlparse(key).path
    state._frame.variables[path] = data


@svm.deleter(schemes='variables')
def delete_variable(state: svm.State, key):
    """
    Deletes a local variable.
    """
    path = urllib.parse.urlparse(key).path
    del state._frame.variables[path]


@svm.getter(schemes='parameters', media_type=None)
def get_parameter(state: svm.State, key, *, default: Any = None):
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
