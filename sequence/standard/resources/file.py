import urllib.parse
import urllib.request
import pathlib
import sequence.vm as svm


@svm.deleter(schemes=['file'])
def delete_generic_file(state: svm.State, uri: str, *, missing_ok: bool = False):
    """
    Deletes a local file.
    """
    path = urllib.parse.urlparse(uri).path
    path = urllib.parse.unquote(path)
    pathlib.Path(path).unlink(missing_ok)
