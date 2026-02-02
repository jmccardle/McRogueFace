import mcrfpy

class PlaygroundScene(mcrfpy.Scene):
    """Scene with reset capability for playground idempotency"""
    def __init__(self, name="playground"):
        super().__init__(name)

    def reset(self):
        """Clear scene state for fresh execution"""
        # Stop all timers
        for t in mcrfpy.timers:
            t.stop()
        for a in mcrfpy.animations:
            a.stop()
        for s in mcrfpy.scenes:
            s.unregister()
        while self.children:
            self.children.pop()
        self.activate()

scene = PlaygroundScene()
scene.activate()

# REPL calls this each "run" before executing the code in the web form.
_reset = scene.reset
