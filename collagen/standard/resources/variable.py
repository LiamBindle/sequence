from typing import Any
import urllib.parse
import urllib.request
import collagen.vm as cvm


@cvm.getter(schemes='locals', media_type=None)
def load_local_variable(state: cvm.State, key, *, default: Any = None):
    """
    Loads a local variable and places the result at the top of the stack.

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
    return state._op_frame._set.get(path, default)


@cvm.putter(schemes='locals', media_type=None)
def store_local_variable(state: cvm.State, data, key):
    """
    Saves a local variable (procedure-scope).
    """
    path = urllib.parse.urlparse(key).path
    state._op_frame._set[path] = data


@cvm.deleter(schemes='locals')
def delete_local_variable(state: cvm.State, key):
    """
    Deletes a local variable.
    """
    path = urllib.parse.urlparse(key).path
    del state._op_frame._set[path]


@cvm.getter(schemes='globals', media_type=None)
def load_global_variable(state: cvm.State, key, *, default: Any = None):
    """
    Loads a global variable and places the result at the top of the stack.

    Parameters
    ----------
    [default]: Any (default: None)
        The default value if the variable doesn't exist.

    Outputs
    -------
    data: Any
        The global variable.
    """
    path = urllib.parse.urlparse(key).path
    return state._vm._globals.get(path, default)


@cvm.putter(schemes='globals', media_type=None)
def store_global_variable(state: cvm.State, data, key):
    """
    Saves a global variable.
    """
    path = urllib.parse.urlparse(key).path
    state._vm._globals[path] = data


@cvm.deleter(schemes='globals')
def delete_global_variable(state: cvm.State, key):
    """
    Deletes a global variable.
    """
    path = urllib.parse.urlparse(key).path
    del state._vm._globals[path]
