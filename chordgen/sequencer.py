"""Step sequencer with 16 steps and pattern management."""

import logging
from typing import List, Optional, Dict
from dataclasses import dataclass, field
import random
import copy

logger = logging.getLogger(__name__)


@dataclass
class Step:
    """Single sequencer step."""
    note: Optional[int] = None  # MIDI note number
    velocity: int = 100          # 0-127
    length: float = 1.0          # 0.0-2.0 (1.0 = full step)
    probability: float = 1.0     # 0.0-1.0 (chance of playing)
    active: bool = True          # Step on/off

    def should_play(self) -> bool:
        """Determine if step should play based on probability."""
        return self.active and self.note is not None and random.random() < self.probability


@dataclass
class SequencerPattern:
    """Sequencer pattern with 16 steps."""
    name: str = "Pattern A"
    steps: List[Step] = field(default_factory=lambda: [Step() for _ in range(16)])
    length: int = 16  # Pattern length (1-16)
    scale: Optional[str] = None  # Scale for quantization

    def copy(self) -> "SequencerPattern":
        """Create deep copy of pattern."""
        return copy.deepcopy(self)


class Sequencer:
    """
    16-step sequencer with multiple patterns.
    """

    def __init__(self, num_patterns: int = 4):
        """
        Initialize sequencer.

        Args:
            num_patterns: Number of patterns (A, B, C, D)
        """
        self.patterns = {}
        pattern_names = ["A", "B", "C", "D"][:num_patterns]
        for name in pattern_names:
            self.patterns[name] = SequencerPattern(name=f"Pattern {name}")

        self.current_pattern_name = "A"
        self._step_index = 0
        self._clipboard = None

    @property
    def current_pattern(self) -> SequencerPattern:
        """Get current pattern."""
        return self.patterns[self.current_pattern_name]

    def step(self) -> Optional[Step]:
        """
        Advance sequencer and return current step.

        Returns:
            Current Step or None
        """
        pattern = self.current_pattern

        if self._step_index >= pattern.length:
            self._step_index = 0  # Loop

        step = pattern.steps[self._step_index]
        self._step_index += 1

        return step if step.should_play() else None

    def get_current_step_index(self) -> int:
        """Get current step index (0-based)."""
        return self._step_index - 1 if self._step_index > 0 else pattern.length - 1

    def set_step(
        self,
        step_num: int,
        note: Optional[int] = None,
        velocity: int = 100,
        length: float = 1.0,
        probability: float = 1.0,
        active: bool = True
    ):
        """
        Set step parameters.

        Args:
            step_num: Step number (0-15)
            note: MIDI note number
            velocity: Note velocity
            length: Note length multiplier
            probability: Play probability
            active: Step active state
        """
        if 0 <= step_num < 16:
            step = self.current_pattern.steps[step_num]
            if note is not None:
                step.note = note
            step.velocity = velocity
            step.length = length
            step.probability = probability
            step.active = active
            logger.debug(f"Set step {step_num}: note={note}, vel={velocity}")

    def clear_step(self, step_num: int):
        """Clear a step."""
        if 0 <= step_num < 16:
            self.current_pattern.steps[step_num] = Step()
            logger.debug(f"Cleared step {step_num}")

    def clear_pattern(self):
        """Clear current pattern."""
        self.current_pattern.steps = [Step() for _ in range(16)]
        logger.info(f"Cleared {self.current_pattern.name}")

    def randomize(
        self,
        density: float = 0.5,
        note_range: tuple = (60, 72),
        vel_range: tuple = (80, 120)
    ):
        """
        Randomize current pattern.

        Args:
            density: Probability of each step being active (0.0-1.0)
            note_range: (min_note, max_note)
            vel_range: (min_velocity, max_velocity)
        """
        pattern = self.current_pattern

        for step in pattern.steps:
            if random.random() < density:
                step.active = True
                step.note = random.randint(*note_range)
                step.velocity = random.randint(*vel_range)
                step.length = random.choice([0.5, 0.75, 1.0, 1.25])
                step.probability = random.choice([1.0, 1.0, 0.75, 0.5])
            else:
                step.active = False
                step.note = None

        logger.info(f"Randomized {pattern.name} with {density*100}% density")

    def copy_pattern(self):
        """Copy current pattern to clipboard."""
        self._clipboard = self.current_pattern.copy()
        logger.info(f"Copied {self.current_pattern.name}")

    def paste_pattern(self):
        """Paste pattern from clipboard."""
        if self._clipboard:
            self.current_pattern.steps = self._clipboard.copy().steps
            logger.info(f"Pasted to {self.current_pattern.name}")

    def switch_pattern(self, pattern_name: str):
        """Switch to different pattern."""
        if pattern_name in self.patterns:
            self.current_pattern_name = pattern_name
            self._step_index = 0
            logger.info(f"Switched to {pattern_name}")

    def set_pattern_length(self, length: int):
        """Set pattern length (1-16)."""
        self.current_pattern.length = max(1, min(16, length))
        logger.info(f"Pattern length set to {length}")

    def reset(self):
        """Reset sequencer to step 0."""
        self._step_index = 0

    def quantize_to_scale(self, scale_notes: List[int]):
        """
        Quantize all notes to scale.

        Args:
            scale_notes: List of MIDI note numbers in scale
        """
        pattern = self.current_pattern

        for step in pattern.steps:
            if step.note is not None:
                # Find closest note in scale
                closest = min(scale_notes, key=lambda x: abs(x - step.note))
                step.note = closest

        logger.info(f"Quantized {pattern.name} to scale")

    def shift_notes(self, semitones: int):
        """Transpose all notes by semitones."""
        pattern = self.current_pattern

        for step in pattern.steps:
            if step.note is not None:
                step.note = max(0, min(127, step.note + semitones))

        logger.info(f"Shifted notes by {semitones} semitones")

    def reverse_pattern(self):
        """Reverse pattern order."""
        self.current_pattern.steps = list(reversed(self.current_pattern.steps))
        logger.info(f"Reversed {self.current_pattern.name}")

    def get_pattern_summary(self) -> Dict:
        """Get summary of current pattern."""
        pattern = self.current_pattern
        active_steps = sum(1 for s in pattern.steps if s.active and s.note is not None)

        return {
            "name": pattern.name,
            "length": pattern.length,
            "active_steps": active_steps,
            "density": active_steps / pattern.length,
            "notes": [s.note for s in pattern.steps if s.note is not None]
        }
