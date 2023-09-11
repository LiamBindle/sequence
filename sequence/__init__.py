# from .utils import op, getter, putter, deleter
# from .vm import run, run_test

from sequence.utils import method, getter, putter, deleter, copier
from sequence.visitors.load import load
from sequence.visitors.base import Sequence
from sequence.visitors.state import State
import sequence.standard

from . import _version
__version__ = _version.get_versions()['version']
