# dont need modes because operations can be raster/pixel independently
# question: how to track multiple things
# question: how to represent diagnostics (debugging)
import zvm.std
import zvm.state


def run(routine: dict):
    return zvm.state.ops['eval']['f'](exe=routine.pop("exe", []), code=routine.pop("code", None))
