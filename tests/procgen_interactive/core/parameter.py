"""Parameter definitions and validation for procedural generation demos.

Parameters define configurable values that affect generation steps.
When a parameter changes, the framework re-runs from the affected step.
"""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional, List, Callable


@dataclass
class Parameter:
    """Definition for a configurable generation parameter.

    Attributes:
        name: Internal identifier used in code
        display: Human-readable label for UI
        type: Parameter type - 'int', 'float', or 'choice'
        default: Default value
        min_val: Minimum value (for numeric types)
        max_val: Maximum value (for numeric types)
        step: Increment for +/- buttons (for numeric types)
        choices: List of valid values (for choice type)
        affects_step: Which step index to re-run when this parameter changes
        description: Optional tooltip/help text
    """
    name: str
    display: str
    type: Literal['int', 'float', 'choice']
    default: Any
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    step: float = 1
    choices: Optional[List[Any]] = None
    affects_step: int = 0
    description: str = ""

    # Runtime state
    _value: Any = field(default=None, repr=False)
    _on_change: Optional[Callable] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize runtime value to default."""
        if self._value is None:
            self._value = self.default

    @property
    def value(self) -> Any:
        """Get current parameter value."""
        return self._value

    @value.setter
    def value(self, new_value: Any):
        """Set parameter value with validation and change notification."""
        validated = self._validate(new_value)
        if validated != self._value:
            self._value = validated
            if self._on_change:
                self._on_change(self)

    def _validate(self, value: Any) -> Any:
        """Validate and coerce value to correct type/range."""
        if self.type == 'int':
            value = int(value)
            if self.min_val is not None:
                value = max(int(self.min_val), value)
            if self.max_val is not None:
                value = min(int(self.max_val), value)
        elif self.type == 'float':
            value = float(value)
            if self.min_val is not None:
                value = max(self.min_val, value)
            if self.max_val is not None:
                value = min(self.max_val, value)
        elif self.type == 'choice':
            if self.choices and value not in self.choices:
                value = self.choices[0] if self.choices else self.default
        return value

    def increment(self):
        """Increase value by step amount."""
        if self.type in ('int', 'float'):
            self.value = self._value + self.step
        elif self.type == 'choice' and self.choices:
            idx = self.choices.index(self._value)
            if idx < len(self.choices) - 1:
                self.value = self.choices[idx + 1]

    def decrement(self):
        """Decrease value by step amount."""
        if self.type in ('int', 'float'):
            self.value = self._value - self.step
        elif self.type == 'choice' and self.choices:
            idx = self.choices.index(self._value)
            if idx > 0:
                self.value = self.choices[idx - 1]

    def reset(self):
        """Reset to default value."""
        self.value = self.default

    def format_value(self) -> str:
        """Format value for display."""
        if self.type == 'int':
            return str(int(self._value))
        elif self.type == 'float':
            # Show 2 decimal places for floats
            return f"{self._value:.2f}"
        else:
            return str(self._value)

    def get_normalized(self) -> float:
        """Get value as 0-1 normalized float (for sliders)."""
        if self.type in ('int', 'float') and self.min_val is not None and self.max_val is not None:
            if self.max_val == self.min_val:
                return 0.5
            return (self._value - self.min_val) / (self.max_val - self.min_val)
        return 0.5

    def set_from_normalized(self, normalized: float):
        """Set value from 0-1 normalized float (from sliders)."""
        if self.type in ('int', 'float') and self.min_val is not None and self.max_val is not None:
            normalized = max(0.0, min(1.0, normalized))
            raw_value = self.min_val + normalized * (self.max_val - self.min_val)
            self.value = raw_value
