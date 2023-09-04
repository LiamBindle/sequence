from typing import Any, Callable
import urllib.parse
import sequence.vm as svm
from ...vm import _static_getters, _static_deleters, _static_putters


# state
@svm.method("get")
def load(state: svm.State, *, uri: str, mediaType: str = None, **params):
    """
    Loads an resource from a URI and places it as the top of the stack.

    Parameters
    ----------
    uri: str
        The URI of the resource you want to load.
    [mediaType]: str
        The media type of the resource you want to load.
    [**params]:
        Additional parameters are passed to the getter.

    Outputs
    -------
    item: Any
        The loaded resource.
    """
    global _static_getters
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_getter = _static_getters[parsed_uri.scheme][mediaType]
    return uri_media_getter(state, uri, **params)


@svm.method("put")
def store(state: svm.State, *, uri: str, mediaType: str = None, **params):
    """
    Stores the item at the top of the stack.

    Parameters
    ----------
    uri: str
        The desination where you want to store the item.
    [mediaType]: str
        The media type of the resource you want to store.
    [**params]:
        Additional parameters are passed to the putter.

    Inputs
    -------
    item: Any
        The item to be stored.
    """
    global _static_putters
    data = state.pop()
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_putter = _static_putters[parsed_uri.scheme][mediaType]
    uri_media_putter(state, data, uri, **params)


@svm.method("del")
def delete(state: svm.State, *, uri: str, mediaType: str = None, **params):
    """
    Deletes a resource.

    Parameters
    ----------
    uri: str
        The URI of the resource to be deleted.
    [mediaType]: str
        The media type of the resource you want to delete.
    [**params]:
        Additional parameters are passed to the deleter.
    """
    global _static_deleters
    parsed_uri = urllib.parse.urlparse(uri)
    uri_media_deleter = _static_deleters[parsed_uri.scheme][mediaType]
    uri_media_deleter(state, uri, **params)
