import urllib.parse
import urllib.request
import pathlib
import sequence


@sequence.deleter(schemes=['file'])
def delete_generic_file(state: sequence.State, uri: str, *, missing_ok: bool = False):
    """
    Deletes a local file.
    """
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    pathlib.Path(path).unlink(missing_ok)
