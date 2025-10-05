"""Arpeggiator engine with multiple patterns and tempo sync."""

import logging
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
import random
from .chords import Chord
from .utils import chord_to_midi_notes

logger = logging.getLogger(__name__)


class ArpPattern(Enum):
    """Arpeggiator patterns."""
    UP = "up"
    DOWN = "down"
    UP_DOWN = "updown"
    DOWN_UP = "downup"
    RANDOM = "random"
    AS_PLAYED = "as_played"
    CHORD = "chord"  # Play whole chord


class ArpRate(Enum):
    """Arpeggiator note rates (in beats)."""
    WHOLE = 4.0
    HALF = 2.0
    QUARTER = 1.0
    EIGHTH = 0.5
    SIXTEENTH = 0.25
    THIRTY_SECOND = 0.125


@dataclass
class ArpNote:
    """Arpeggiated note with timing."""
    note: int
    velocity: int
    start_time: float  # in beats
    duration: float    # in beats
    octave_offset: int = 0


class Arpeggiator:
    """
    Arpeggiator engine.
    Converts chords into arpeggiated note sequences.
    """

    def __init__(
        self,
        pattern: ArpPattern = ArpPattern.UP,
        rate: ArpRate = ArpRate.EIGHTH,
        octaves: int = 1,
        gate: float = 0.75,
        swing: float = 0.0
    ):
        """
        Initialize arpeggiator.

        Args:
            pattern: Arp pattern
            rate: Note rate
            octaves: Octave range (1-4)
            gate: Gate length (0.1-2.0, where 1.0 = full note)
            swing: Swing amount (0.0-0.75)
        """
        self.pattern = pattern
        self.rate = rate
        self.octaves = max(1, min(4, octaves))
        self.gate = max(0.1, min(2.0, gate))
        self.swing = max(0.0, min(0.75, swing))

        self.latch = False
        self.current_chord = None
        self.current_notes = []
        self._pattern_index = 0
        self._direction = 1  # 1 for up, -1 for down

    def arpeggiate(
        self,
        chord: Chord,
        duration_beats: float,
        start_beat: float = 0.0,
        velocity: int = 100
    ) -> List[ArpNote]:
        """
        Generate arpeggio sequence from chord.

        Args:
            chord: Chord to arpeggiate
            duration_beats: Total duration in beats
            start_beat: Start time in beats
            velocity: Note velocity (0-127)

        Returns:
            List of ArpNote objects
        """
        # Get MIDI notes for chord
        base_notes = chord_to_midi_notes(chord.root, chord.quality, octave=4)

        # Expand to multiple octaves
        notes = []
        for octave_offset in range(self.octaves):
            for note in base_notes:
                notes.append(note + (octave_offset * 12))

        # Apply pattern
        sequence = self._apply_pattern(notes)

        # Generate timed notes
        arp_notes = []
        note_duration = self.rate.value
        current_time = start_beat
        note_index = 0

        while current_time < start_beat + duration_beats:
            if note_index >= len(sequence):
                note_index = 0  # Loop the pattern

            note = sequence[note_index]

            # Apply swing (only on even notes)
            if self.swing > 0 and note_index % 2 == 1:
                swing_offset = note_duration * self.swing
                current_time += swing_offset

            # Calculate actual note duration with gate
            actual_duration = note_duration * self.gate

            arp_note = ArpNote(
                note=note,
                velocity=velocity,
                start_time=current_time,
                duration=actual_duration,
                octave_offset=(note - base_notes[0]) // 12
            )
            arp_notes.append(arp_note)

            current_time += note_duration
            note_index += 1

        logger.debug(f"Generated {len(arp_notes)} arp notes for {chord}")
        return arp_notes

    def _apply_pattern(self, notes: List[int]) -> List[int]:
        """
        Apply arpeggiator pattern to note list.

        Args:
            notes: List of MIDI note numbers

        Returns:
            Reordered note list
        """
        if self.pattern == ArpPattern.UP:
            return sorted(notes)

        elif self.pattern == ArpPattern.DOWN:
            return sorted(notes, reverse=True)

        elif self.pattern == ArpPattern.UP_DOWN:
            up = sorted(notes)
            down = sorted(notes, reverse=True)[1:-1]  # Exclude duplicates
            return up + down

        elif self.pattern == ArpPattern.DOWN_UP:
            down = sorted(notes, reverse=True)
            up = sorted(notes)[1:-1]  # Exclude duplicates
            return down + up

        elif self.pattern == ArpPattern.RANDOM:
            shuffled = notes.copy()
            random.shuffle(shuffled)
            return shuffled

        elif self.pattern == ArpPattern.AS_PLAYED:
            return notes  # Keep original order

        elif self.pattern == ArpPattern.CHORD:
            return notes[:1]  # Just return first note (whole chord played separately)

        return notes

    def get_next_note(
        self,
        chord: Optional[Chord] = None,
        velocity: int = 100
    ) -> Optional[ArpNote]:
        """
        Get next note in arpeggio sequence (for real-time use).

        Args:
            chord: New chord (updates current chord)
            velocity: Note velocity

        Returns:
            Next ArpNote or None
        """
        # Update chord if provided
        if chord is not None:
            self.current_chord = chord
            base_notes = chord_to_midi_notes(chord.root, chord.quality, octave=4)

            # Expand to octaves
            self.current_notes = []
            for octave_offset in range(self.octaves):
                for note in base_notes:
                    self.current_notes.append(note + (octave_offset * 12))

            # Apply pattern
            self.current_notes = self._apply_pattern(self.current_notes)
            self._pattern_index = 0

        # Check if we have notes
        if not self.current_notes:
            return None

        # Get current note
        note = self.current_notes[self._pattern_index]

        # Create ArpNote
        arp_note = ArpNote(
            note=note,
            velocity=velocity,
            start_time=0.0,  # Real-time, not pre-calculated
            duration=self.rate.value * self.gate,
            octave_offset=(note - self.current_notes[0]) // 12
        )

        # Advance index
        self._pattern_index = (self._pattern_index + 1) % len(self.current_notes)

        return arp_note

    def reset(self):
        """Reset arpeggiator state."""
        self._pattern_index = 0
        self._direction = 1

    def set_pattern(self, pattern: ArpPattern):
        """Set arp pattern."""
        self.pattern = pattern
        self.reset()
        logger.info(f"Arp pattern set to {pattern.value}")

    def set_rate(self, rate: ArpRate):
        """Set arp rate."""
        self.rate = rate
        logger.info(f"Arp rate set to {rate.value} beats")

    def set_octaves(self, octaves: int):
        """Set octave range."""
        self.octaves = max(1, min(4, octaves))
        logger.info(f"Arp octaves set to {self.octaves}")

    def set_gate(self, gate: float):
        """Set gate length."""
        self.gate = max(0.1, min(2.0, gate))
        logger.info(f"Arp gate set to {self.gate * 100}%")

    def set_swing(self, swing: float):
        """Set swing amount."""
        self.swing = max(0.0, min(0.75, swing))
        logger.info(f"Arp swing set to {self.swing * 100}%")
