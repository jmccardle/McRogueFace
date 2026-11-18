"""Reusable harness for check-then-convert bugs (#558, same family as #543).

A binding function that validates against the object's CURRENT state (a size, a "has a grid"
flag, a node pointer) and THEN converts an argument runs user code in between: __index__,
__float__, a property read by getattr, __bool__, __len__ / __getitem__. That code can resize or
re-initialise the object, detach it, clear its container. The validation is then stale.

`Hostile` is a number (and a few other things) whose every conversion hook first runs a supplied
`action`, then answers a fixed value:

    layer = mcrfpy.ColorLayer("c", -1, (50, 50))
    evil = Hostile(lambda: layer.__init__("c", -1, (1, 1)), 3)
    layer.set((49, 49), (evil, 2, 3))          # must not write out of bounds

The hooks are class-level so Python's special-method lookup finds them:
    __index__   -> value (an int)             __float__ -> float(value)
    __int__     -> int(value)                 __bool__  -> bool(value)
    __len__     -> 2                          __getitem__ -> value (so a Hostile is also a "pair")
    .value      -> value   (a property; how a DiscreteMap reads an IntEnum-like)
    .x / .y     -> value   (properties; how Vector-likes are read)
`calls` counts how often the action ran (it runs ONCE per Hostile, on the first hook; later hooks
only answer) so a test can assert the hostile code really did execute.

`attempt(label, fn)` runs fn, accepting any ORDINARY exception (TypeError, ValueError, IndexError,
OverflowError, RuntimeError: a stale validation may legitimately turn into an error) and recording
a failure for SystemError (an exception left pending), BaseException subclasses that are not
ordinary, or a result the caller's own check rejects. A crash is the failure ASan reports.
"""
import sys

ORDINARY = (TypeError, ValueError, IndexError, OverflowError, RuntimeError, KeyError, AttributeError)


class Hostile:
    def __init__(self, action, value=1):
        self._action = action
        self._value = value
        self.calls = 0

    def _run(self):
        if self.calls == 0:
            self.calls = 1
            self._action()
        return self._value

    # numeric conversions
    def __index__(self): return int(self._run())
    def __int__(self): return int(self._run())
    def __float__(self): return float(self._run())
    def __bool__(self): return bool(self._run())

    # "a pair" hooks: a Hostile is a 2-sequence whose items are its value
    def __len__(self):
        self._run()
        return 2

    def __getitem__(self, i):
        self._run()
        return self._value

    # attribute hooks
    @property
    def value(self): return self._run()
    @property
    def x(self): return self._run()
    @property
    def y(self): return self._run()


class Failures:
    def __init__(self):
        self.items = []

    def add(self, msg):
        self.items.append(msg)

    def attempt(self, label, fn, hostile=None):
        """Run fn(); any ordinary exception is acceptable, SystemError and other oddities are not.
        If `hostile` is given, also require that its action actually ran."""
        try:
            fn()
        except SystemError as e:
            self.add(f"{label}: SystemError (an exception was left pending): {e}")
        except ORDINARY:
            pass
        except BaseException as e:
            self.add(f"{label}: raised {type(e).__name__}: {e}")
        if hostile is not None and hostile.calls == 0:
            self.add(f"{label}: the hostile action never ran (the test proves nothing)")

    def finish(self):
        for f in self.items:
            print("FAIL:", f)
        print("FAIL" if self.items else "PASS")
        sys.exit(1 if self.items else 0)
