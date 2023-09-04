import urllib.parse
import urllib.request
import sequence.vm as svm


try:
    import json5
    ENABLE_JSON5 = True
except ImportError:
    ENABLE_JSON5 = False


@svm.getter(schemes=['http', 'https'], media_type='application/json5')
def fetch_json5_http(state: svm.State, url: str):
    """
    Loads a JSON5 file from a remote HTTP/HTTPS source.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    if not ENABLE_JSON5:
        raise RuntimeError("json5 support not enabled")
    response = urllib.request.urlopen(url)
    if response.code != 200:
        raise RuntimeError(f"Error reading {url}")
    return json5.loads(response.read())


@svm.getter(schemes=['file'], media_type='application/json5')
def fetch_json5_file(state: svm.State, url: str):
    """
    Loads a JSON5 file from a local file.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    if not ENABLE_JSON5:
        raise RuntimeError("json5 support not enabled")
    path = urllib.parse.urlparse(url).path
    path = urllib.parse.unquote(path)
    with open(path, 'r') as f:
        data = json5.load(f)
    return data


@svm.putter(schemes=['file'], media_type='application/json5')
def store_json5_file(state: svm.State, data, uri: str):
    """
    Loads a JSON5 file from a local file.

    Inputs
    ------
    data: key-value array
        The key-value array to be saved.
    """
    if not ENABLE_JSON5:
        raise RuntimeError("json5 support not enabled")
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    with open(path, 'w') as f:
        json5.dump(data, f)
