# from .utils import op, getter, putter, deleter
# from .vm import run, run_test
from .vm import method, State

from . import _version
__version__ = _version.get_versions()['version']
