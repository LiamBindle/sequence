import urllib.parse
import urllib.request
import collagen.vm as cvm


try:
    import hjson
    ENABLE_HJSON = True
except ImportError:
    ENABLE_HJSON = False


@cvm.getter(schemes=['http', 'https'], media_type='application/hjson')
def fetch_hjson_http(state: cvm.State, url: str):
    """
    Loads a HJSON file from a remote HTTP/HTTPS source.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    if not ENABLE_HJSON:
        raise RuntimeError("hjson support not enabled")
    response = urllib.request.urlopen(url)
    if response.code != 200:
        raise RuntimeError(f"Error reading {url}")
    return hjson.loads(response.read())


@cvm.getter(schemes=['file'], media_type='application/hjson')
def fetch_hjson_file(state: cvm.State, url: str):
    """
    Loads a HJSON file from a local file.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    if not ENABLE_HJSON:
        raise RuntimeError("hjson support not enabled")
    path = urllib.parse.urlparse(url).path
    path = urllib.parse.unquote(path)
    with open(path, 'r') as f:
        data = hjson.load(f)
    return data


@cvm.putter(schemes=['file'], media_type='application/hjson')
def store_hjson_file(state: cvm.State, data, uri: str):
    """
    Loads a HJSON file from a local file.

    Inputs
    ------
    data: key-value array
        The key-value array to be saved.
    """
    if not ENABLE_HJSON:
        raise RuntimeError("hjson support not enabled")
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    with open(path, 'w') as f:
        hjson.dump(data, f)
