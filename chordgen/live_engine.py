"""Live performance engine - coordinates all modules in real-time."""

import logging
import threading
import time
from typing import Optional, List
from dataclasses import dataclass
from .midi_clock import MIDIClock, TimePosition
from .arpeggiator import Arpeggiator, ArpNote
from .sequencer import Sequencer
from .chords import Chord
from .midi_out import MIDISender

logger = logging.getLogger(__name__)


@dataclass
class LiveConfig:
    """Live performance configuration."""
    chord_enabled: bool = True
    arp_enabled: bool = False
    seq_enabled: bool = False
    midi_port: Optional[str] = None
    midi_channel: int = 1


class LiveEngine:
    """
    Coordinates chord generator, arpeggiator, and sequencer in real-time.
    """

    def __init__(
        self,
        clock: MIDIClock,
        config: LiveConfig,
        progression: Optional[List[Chord]] = None,
        arpeggiator: Optional[Arpeggiator] = None,
        sequencer: Optional[Sequencer] = None
    ):
        """
        Initialize live engine.

        Args:
            clock: MIDI clock instance
            config: Live configuration
            progression: Chord progression
            arpeggiator: Arpeggiator instance
            sequencer: Sequencer instance
        """
        self.clock = clock
        self.config = config
        self.progression = progression or []
        self.arpeggiator = arpeggiator
        self.sequencer = sequencer

        # MIDI output
        self.midi_sender = None
        self._running = False
        self._performance_thread = None

        # State
        self._current_chord_index = 0
        self._last_beat = -1

        # Register clock callbacks
        self.clock.on_beat(self._on_beat)
        self.clock.on_bar(self._on_bar)

    def start(self):
        """Start live performance."""
        if self._running:
            logger.warning("Live engine already running")
            return

        # Initialize MIDI sender
        if self.config.midi_port:
            try:
                self.midi_sender = MIDISender(self.config.midi_port)
                logger.info(f"MIDI sender initialized: {self.config.midi_port}")
            except Exception as e:
                logger.error(f"Failed to initialize MIDI: {e}")
                return

        self._running = True
        self.clock.start()

        logger.info("Live engine started")

    def stop(self):
        """Stop live performance."""
        if not self._running:
            return

        self._running = False
        self.clock.stop()

        # Close MIDI
        if self.midi_sender:
            self.midi_sender.close()
            self.midi_sender = None

        logger.info("Live engine stopped")

    def _on_beat(self, position: TimePosition):
        """Called on every beat."""
        if not self._running or not self.midi_sender:
            return

        # Arpeggiator mode
        if self.config.arp_enabled and self.arpeggiator and self.progression:
            self._handle_arpeggiator(position)

        # Sequencer mode
        elif self.config.seq_enabled and self.sequencer:
            self._handle_sequencer(position)

        # Chord mode (just play the chord)
        elif self.config.chord_enabled and self.progression:
            self._handle_chord(position)

    def _on_bar(self, position: TimePosition):
        """Called on every bar."""
        if not self._running:
            return

        # Update chord on bar change
        if self.progression:
            self._current_chord_index = (position.bar - 1) % len(self.progression)
            logger.debug(f"Bar {position.bar}: Chord index {self._current_chord_index}")

    def _handle_chord(self, position: TimePosition):
        """Handle chord playback."""
        if not self.progression or not self.midi_sender:
            return

        # Play chord on beat 1
        if position.beat == 1:
            chord = self.progression[self._current_chord_index]
            from .utils import chord_to_midi_notes

            notes = chord_to_midi_notes(chord.root, chord.quality, octave=4)

            # Send chord
            for note in notes:
                self.midi_sender.send_chord(chord)

            logger.debug(f"Played chord: {chord}")

    def _handle_arpeggiator(self, position: TimePosition):
        """Handle arpeggiator playback."""
        if not self.progression or not self.arpeggiator or not self.midi_sender:
            return

        # Get current chord
        chord = self.progression[self._current_chord_index]

        # Calculate if we should play an arp note on this beat
        arp_rate = self.arpeggiator.rate.value  # in beats

        # Check if this beat aligns with arp rate
        beat_in_bar = position.beat - 1  # 0-indexed
        total_beat = (position.bar - 1) * self.clock.beats_per_bar + beat_in_bar

        # Play arp note
        if total_beat % arp_rate == 0:
            arp_note = self.arpeggiator.get_next_note(chord)
            if arp_note:
                self.midi_sender.send_note(arp_note.note, arp_note.velocity)
                logger.debug(f"Arp note: {arp_note.note}")

    def _handle_sequencer(self, position: TimePosition):
        """Handle sequencer playback."""
        if not self.sequencer or not self.midi_sender:
            return

        # Sequencer steps on 16th notes
        # We need to trigger on sub-beat divisions
        # For now, trigger on each beat (simplified)
        step = self.sequencer.step()

        if step and step.should_play():
            self.midi_sender.send_note(step.note, step.velocity)
            logger.debug(f"Seq note: {step.note}")

    def update_progression(self, progression: List[Chord]):
        """Update chord progression."""
        self.progression = progression
        self._current_chord_index = 0
        logger.info(f"Updated progression: {len(progression)} chords")

    def update_config(self, config: LiveConfig):
        """Update live configuration."""
        self.config = config
        logger.info("Updated live config")

    def is_running(self) -> bool:
        """Check if engine is running."""
        return self._running

    def get_current_chord(self) -> Optional[Chord]:
        """Get current chord."""
        if self.progression and 0 <= self._current_chord_index < len(self.progression):
            return self.progression[self._current_chord_index]
        return None
