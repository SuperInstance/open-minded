from .core.core import Interpreter
import sys
import types

# This is done so when users `import interpreter`,
# they get an instance of interpreter — but we wrap the module so that
# submodule imports like `interpreter.induction` still work.

_module = sys.modules["interpreter"]
_module.Interpreter = Interpreter
_instance = Interpreter()


class _CallableModule(types.ModuleType):
    """Module proxy that delegates attribute access to an Interpreter instance
    while preserving real module behaviour (submodule imports, __path__, etc.)."""

    def __init__(self, mod, inst):
        super().__init__(mod.__name__)
        self.__dict__.update(mod.__dict__)
        self.__wrapped__ = mod
        self._inst = inst

    def __call__(self, *a, **kw):
        return self._inst(*a, **kw)

    def __getattr__(self, name):
        # Delegate unknown attributes to the Interpreter instance
        try:
            return getattr(self._inst, name)
        except AttributeError:
            raise AttributeError(f"module 'interpreter' has no attribute {name!r}")


sys.modules["interpreter"] = _CallableModule(_module, _instance)

# **This is a modified version of the original module-swap pattern.**
# The original replaced the entire module with an Interpreter() instance,
# which broke `from interpreter.induction import ...`.  This proxy preserves
# both behaviours: `import interpreter; interpreter.chat(...)` works AND
# `from interpreter.induction.synchronizer import TripartiteSynchronizer` works.

#     ____                      ____      __                            __
#    / __ \____  ___  ____     /  _/___  / /____  _________  ________  / /____  _____
#   / / / / __ \/ _ \/ __ \    / // __ \/ __/ _ \/ ___/ __ \/ ___/ _ \/ __/ _ \/ ___/
#  / /_/ / /_/ /  __/ / / /  _/ // / / / /_/  __/ /  / /_/ / /  /  __/ /_/  __/ /
#  \____/ .___/\___/_/ /_/  /___/_/ /_/\__/\___/_/  / .___/_/   \___/\__/\___/_/
#      /_/                                         /_/
