# from .utils import op, getter, putter, deleter
# from .vm import run, run_test
from .zvm import op, getter, putter, deleter, ZVM, State, test, copier

from . import _version
__version__ = _version.get_versions()['version']
