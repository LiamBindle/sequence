from typing import Any, Union
import logging


ops: dict[str, Union[dict, Any]] = {}
getters: dict[str, dict[str, Any]] = {}
ext_getter: dict[str, dict[str, Any]] = {}
putters: dict[str, dict[str, Any]] = {}
deleters: dict[str, dict[str, Any]] = {}
copiers = {}

logger = logging.getLogger('sequence')
