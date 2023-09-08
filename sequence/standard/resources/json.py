import json
import urllib.parse
import urllib.request
import sequence


@sequence.getter(schemes=['http', 'https'], media_type='application/json', extensions=['.json'])
def fetch_json_http(state: sequence.State, url: str):
    """
    Loads a JSON file from a remote HTTP/HTTPS source.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    response = urllib.request.urlopen(url)
    if response.code != 200:
        raise RuntimeError(f"Error reading {url}")
    return json.loads(response.read())


@sequence.getter(schemes=['file'], media_type='application/json', extensions=['.json'])
def fetch_json_file(state: sequence.State, url: str):
    """
    Loads a JSON file from a local file.

    Outputs
    -------
    json_data: key-value array
        The json data as a key-value array.
    """
    path = urllib.parse.urlparse(url).path
    path = urllib.parse.unquote(path)
    with open(path, 'r') as f:
        data = json.load(f)
    return data


@sequence.putter(schemes=['file'], media_type='application/json')
def store_json_file(state: sequence.State, data, uri: str):
    """
    Loads a JSON file from a local file.

    Inputs
    ------
    data: key-value array
        The key-value array to be saved.
    """
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    with open(path, 'w') as f:
        json.dump(data, f)
