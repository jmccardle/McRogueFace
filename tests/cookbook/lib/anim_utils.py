# McRogueFace Cookbook - Animation Utilities
"""
Utilities for complex animation orchestration.

Example:
    from lib.anim_utils import AnimationChain, AnimationGroup, delay

    # Sequential animations
    chain = AnimationChain(
        (frame, "x", 200, 0.5),
        delay(0.2),
        (frame, "y", 300, 0.5),
        callback=on_complete
    )
    chain.start()

    # Parallel animations
    group = AnimationGroup(
        (frame, "x", 200, 0.5),
        (frame, "opacity", 0.5, 0.5),
        callback=on_complete
    )
    group.start()
"""
import mcrfpy


class AnimationStep:
    """Base class for animation steps."""

    def start(self, callback):
        """Start the step, call callback when done."""
        raise NotImplementedError


class PropertyAnimation(AnimationStep):
    """Single property animation step.

    Args:
        target: The UI element to animate
        property: Property name (e.g., "x", "y", "opacity")
        value: Target value
        duration: Duration in seconds
        easing: Easing function (default: EASE_OUT)
    """

    def __init__(self, target, property_name, value, duration, easing=None):
        self.target = target
        self.property_name = property_name
        self.value = value
        self.duration = duration
        self.easing = easing or mcrfpy.Easing.EASE_OUT
        self._timer_name = None

    def start(self, callback=None):
        """Start the animation."""
        # Start the animation on the target
        self.target.animate(self.property_name, self.value, self.duration, self.easing)

        # Schedule callback after duration
        if callback:
            self._timer_name = f"anim_step_{id(self)}"
            mcrfpy.Timer(self._timer_name, lambda rt: callback(), int(self.duration * 1000))


class DelayStep(AnimationStep):
    """Delay step - just waits for a duration."""

    def __init__(self, duration):
        self.duration = duration
        self._timer_name = None

    def start(self, callback=None):
        """Wait for duration then call callback."""
        if callback:
            self._timer_name = f"delay_step_{id(self)}"
            mcrfpy.Timer(self._timer_name, lambda rt: callback(), int(self.duration * 1000))
        # If no callback, this is a no-op (shouldn't happen in a chain)


class CallbackStep(AnimationStep):
    """Step that calls a function."""

    def __init__(self, func):
        self.func = func

    def start(self, callback=None):
        """Call the function immediately, then callback."""
        self.func()
        if callback:
            callback()


def delay(duration):
    """Create a delay step.

    Args:
        duration: Delay in seconds

    Returns:
        DelayStep object
    """
    return DelayStep(duration)


def callback(func):
    """Create a callback step.

    Args:
        func: Function to call (no arguments)

    Returns:
        CallbackStep object
    """
    return CallbackStep(func)


def _parse_animation_spec(spec):
    """Parse an animation specification.

    Args:
        spec: Either an AnimationStep, or a tuple of (target, property, value, duration[, easing])

    Returns:
        AnimationStep object
    """
    if isinstance(spec, AnimationStep):
        return spec

    if isinstance(spec, tuple):
        if len(spec) == 4:
            target, prop, value, duration = spec
            return PropertyAnimation(target, prop, value, duration)
        elif len(spec) == 5:
            target, prop, value, duration, easing = spec
            return PropertyAnimation(target, prop, value, duration, easing)

    raise ValueError(f"Invalid animation spec: {spec}")


class AnimationChain:
    """Sequential animation execution.

    Runs animations one after another. Each step must complete before
    the next one starts.

    Args:
        *steps: Animation steps - either AnimationStep objects or tuples of
                (target, property, value, duration[, easing])
        callback: Optional function to call when chain completes
        loop: If True, restart chain when it completes

    Example:
        chain = AnimationChain(
            (frame, "x", 200, 0.5),
            delay(0.2),
            (frame, "y", 300, 0.5),
            callback=lambda: print("Done!")
        )
        chain.start()
    """

    def __init__(self, *steps, callback=None, loop=False):
        self.steps = [_parse_animation_spec(s) for s in steps]
        self.callback = callback
        self.loop = loop
        self._current_index = 0
        self._running = False

    def start(self):
        """Start the animation chain."""
        self._current_index = 0
        self._running = True
        self._run_next()

    def stop(self):
        """Stop the animation chain."""
        self._running = False

    def _run_next(self):
        """Run the next step in the chain."""
        if not self._running:
            return

        if self._current_index >= len(self.steps):
            # Chain complete
            if self.callback:
                self.callback()
            if self.loop:
                self._current_index = 0
                self._run_next()
            else:
                self._running = False
            return

        # Run current step
        step = self.steps[self._current_index]
        self._current_index += 1
        step.start(callback=self._run_next)


class AnimationGroup:
    """Parallel animation execution.

    Runs all animations simultaneously. The group completes when
    all animations have finished.

    Args:
        *steps: Animation steps - either AnimationStep objects or tuples of
                (target, property, value, duration[, easing])
        callback: Optional function to call when all animations complete

    Example:
        group = AnimationGroup(
            (frame, "x", 200, 0.5),
            (frame, "opacity", 0.5, 0.3),
            callback=lambda: print("All done!")
        )
        group.start()
    """

    def __init__(self, *steps, callback=None):
        self.steps = [_parse_animation_spec(s) for s in steps]
        self.callback = callback
        self._pending = 0
        self._running = False

    def start(self):
        """Start all animations in parallel."""
        if not self.steps:
            if self.callback:
                self.callback()
            return

        self._running = True
        self._pending = len(self.steps)

        for step in self.steps:
            step.start(callback=self._on_step_complete)

    def stop(self):
        """Stop tracking the group (note: individual animations continue)."""
        self._running = False

    def _on_step_complete(self):
        """Called when each step completes."""
        if not self._running:
            return

        self._pending -= 1
        if self._pending <= 0:
            self._running = False
            if self.callback:
                self.callback()


class AnimationSequence:
    """More complex animation sequencing with named steps and branching.

    Args:
        steps: Dict mapping step names to animation specs or step lists
        start_step: Name of the first step to run
        callback: Optional function to call when sequence ends
    """

    def __init__(self, steps=None, start_step="start", callback=None):
        self.steps = steps or {}
        self.start_step = start_step
        self.callback = callback
        self._current_step = None
        self._running = False

    def add_step(self, name, *animations, next_step=None):
        """Add a named step.

        Args:
            name: Step name
            *animations: Animation specs for this step
            next_step: Name of next step (or None to end)
        """
        self.steps[name] = {
            "animations": [_parse_animation_spec(a) for a in animations],
            "next": next_step
        }

    def start(self, step_name=None):
        """Start the sequence from a given step."""
        self._running = True
        self._run_step(step_name or self.start_step)

    def stop(self):
        """Stop the sequence."""
        self._running = False

    def _run_step(self, name):
        """Run a named step."""
        if not self._running or name not in self.steps:
            if name is None and self.callback:
                self.callback()
            return

        self._current_step = name
        step_data = self.steps[name]
        animations = step_data.get("animations", [])
        next_step = step_data.get("next")

        if not animations:
            # No animations, go directly to next
            self._run_step(next_step)
            return

        # Run animations in parallel, then proceed to next step
        group = AnimationGroup(
            *animations,
            callback=lambda: self._run_step(next_step)
        )
        group.start()


# Convenience functions for common patterns

def fade_in(target, duration=0.3, easing=None):
    """Create a fade-in animation (opacity 0 to 1)."""
    target.opacity = 0
    return PropertyAnimation(target, "opacity", 1.0, duration, easing)


def fade_out(target, duration=0.3, easing=None):
    """Create a fade-out animation (current opacity to 0)."""
    return PropertyAnimation(target, "opacity", 0.0, duration, easing)


def slide_in_from_left(target, distance=100, duration=0.3, easing=None):
    """Create a slide-in from left animation."""
    original_x = target.x
    target.x = original_x - distance
    return PropertyAnimation(target, "x", original_x, duration, easing or mcrfpy.Easing.EASE_OUT)


def slide_in_from_right(target, distance=100, duration=0.3, easing=None):
    """Create a slide-in from right animation."""
    original_x = target.x
    target.x = original_x + distance
    return PropertyAnimation(target, "x", original_x, duration, easing or mcrfpy.Easing.EASE_OUT)


def slide_in_from_top(target, distance=100, duration=0.3, easing=None):
    """Create a slide-in from top animation."""
    original_y = target.y
    target.y = original_y - distance
    return PropertyAnimation(target, "y", original_y, duration, easing or mcrfpy.Easing.EASE_OUT)


def slide_in_from_bottom(target, distance=100, duration=0.3, easing=None):
    """Create a slide-in from bottom animation."""
    original_y = target.y
    target.y = original_y + distance
    return PropertyAnimation(target, "y", original_y, duration, easing or mcrfpy.Easing.EASE_OUT)


def pulse(target, scale_factor=1.1, duration=0.2):
    """Create a pulse animation (scale up then back)."""
    # Note: This requires scale animation support
    # If not available, we approximate with position
    original_x = target.x
    original_y = target.y
    offset = (scale_factor - 1) * 10  # Approximate offset

    return AnimationChain(
        (target, "x", original_x - offset, duration / 2),
        (target, "x", original_x, duration / 2),
    )


def shake(target, intensity=5, duration=0.3):
    """Create a shake animation."""
    original_x = target.x
    step_duration = duration / 6

    return AnimationChain(
        (target, "x", original_x - intensity, step_duration),
        (target, "x", original_x + intensity, step_duration),
        (target, "x", original_x - intensity * 0.5, step_duration),
        (target, "x", original_x + intensity * 0.5, step_duration),
        (target, "x", original_x - intensity * 0.25, step_duration),
        (target, "x", original_x, step_duration),
    )
