import datetime
import copy

from .base import Visitor, Sequence
import sequence.static

from .state import State


class SequenceFrame(Visitor):
    def __init__(self, name: str = 'root', parent: 'SequenceFrame' = None, parameters: dict = None):
        self.name = name
        self.parent = parent
        if parent is None:
            self.variables = {}
            self.stack = []
            self.started_at = datetime.datetime.utcnow()
        else:
            self.variables = copy.copy(parent.variables)
            self.stack = parent.stack
            self.started_at = parent.started_at
        self.pc: int = 0
        self.begins: list[int] = []
        self.parameters: dict = parameters or {}
        self.run: list = []

    @property
    def _breadcrumb(self) -> str:
        runner = self
        runners = []
        while runner is not None:
            runners.append(f'{runner.name}.{runner.pc}')
            runner = runner.parent
        return ':'.join(reversed(runners))

    def _elapsed_time(self, since: datetime.datetime = None) -> str:
        elapsed = datetime.datetime.utcnow() - (since or self.started_at)
        t = elapsed.total_seconds()
        seconds = t % 60
        minutes = int(t//60) % 60
        hours = int(t//3600)
        elapsed = ""
        if hours:
            elapsed += f"{hours:d}h"
        if minutes:
            elapsed += f"{minutes: 2d}m"
        elapsed += f"{seconds: 6.3f}"[:6] + "s"
        return elapsed

    def visit(self, seq: Sequence):
        for var_name, var_default in self._dereference(seq.variables).items():
            self.variables.setdefault(var_name, var_default)
        self.run = seq.run

        while self.pc < len(seq.run):
            ex = seq.run[self.pc]

            if isinstance(ex, dict) and "op" in ex:
                # ex in an op
                name = ex['op']
                op = sequence.static.ops[name]

                sequence.static.logger.info(f'Starting [{self._breadcrumb}] total elapsed: {self._elapsed_time()}, stack size: {len(self.stack)}, op: {name}')
                time_before = datetime.datetime.utcnow()

                if isinstance(op, Sequence):
                    parameters = {}
                    missing_parameters = []
                    for param_name, param_def in op.metadata.get("parameters", {}).items():
                        is_required = (not param_def.get("optional", False)) and ("default" not in param_def)
                        if is_required and param_name not in ex and param_name not in parameters:
                            missing_parameters.append(param_name)
                        if param_name in ex:
                            parameters[param_name] = ex[param_name]
                        elif "default" in param_def:
                            parameters[param_name] = param_def["default"]
                    if missing_parameters:
                        raise TypeError(f'sequence "{name}" missing {len(missing_parameters)} parameter(s): {", ".join([f"{p}" for p in missing_parameters])}')
                    parameters = self._dereference(copy.deepcopy(parameters))

                    child = SequenceFrame(name=name, parent=self, parameters=parameters)
                    child.visit(op)
                    result = None  # child.run will have updated the stack
                else:
                    assert callable(op), "internal error"
                    parameters = {k: v for k, v in ex.items() if k != "op"}
                    parameters = self._dereference(copy.deepcopy(parameters))
                    state = State(self)
                    result = op(state, **parameters)  # methods run within current frame

                sequence.static.logger.debug(f'Finished [{self._breadcrumb}] incl. elapsed: {self._elapsed_time(since=time_before)}, op: {name}')
            else:
                # is a literal
                result = ex
                name = None

            if isinstance(result, tuple):
                self.stack.extend(result)
            elif result is not None:
                self.stack.append(result)
            self.pc += 1
