"""UNWRITTEN - modal input dispatch. Owner: Agent A.

One InputStack per scene owns scene.on_key and dispatches to a stack of
handlers, top-most first. A handler is fn(key, state) -> bool; returning True
consumes the event (lower handlers do not see it). Overworld pushes its
movement handler; a DialogueBox / menu pushes itself while open and pops on
close, freezing everything beneath it.
"""


class InputStack:
    def __init__(self, scene):
        self.scene = scene
        self.stack = []          # list of (name, handler)
        scene.on_key = self._dispatch

    def push(self, handler, name=""):
        self.stack.append((name, handler))

    def pop(self, name=""):
        """Pop the top handler, or the top-most handler matching name."""
        if name:
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == name:
                    return self.stack.pop(i)
            return None
        if self.stack:
            return self.stack.pop()
        return None

    def replace(self, handler, name=""):
        """Replace the top handler with a new one."""
        self.pop()
        self.push(handler, name)

    def clear(self):
        self.stack = []

    def has(self, name):
        return any(n == name for n, _ in self.stack)

    def _dispatch(self, key, state):
        for i in range(len(self.stack) - 1, -1, -1):
            handler = self.stack[i][1]
            if handler(key, state):
                return
