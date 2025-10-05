"""MIDI clock, transport controls, and timing system."""

import logging
import time
from typing import Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class TransportState(Enum):
    """Transport states."""
    STOPPED = "stopped"
    PLAYING = "playing"
    RECORDING = "recording"
    PAUSED = "paused"


@dataclass
class TimePosition:
    """Musical time position."""
    bar: int = 1
    beat: int = 1
    tick: int = 0
    total_beats: float = 0.0

    def __str__(self):
        return f"{self.bar}:{self.beat}:{self.tick}"


class MIDIClock:
    """
    MIDI clock with transport controls.
    Handles timing, playback, and position tracking.
    """

    PPQN = 480  # Pulses Per Quarter Note (standard MIDI resolution)

    def __init__(self, tempo: float = 120.0, time_signature: Tuple[int, int] = (4, 4), external_sync: bool = False):
        """
        Initialize MIDI clock.

        Args:
            tempo: Tempo in BPM
            time_signature: (numerator, denominator) e.g., (4, 4)
            external_sync: If True, sync to external MIDI clock
        """
        self.tempo = tempo
        self.time_signature = time_signature
        self.state = TransportState.STOPPED
        self.external_sync = external_sync

        # Position tracking
        self.position = TimePosition()
        self._tick_count = 0
        self._last_tick_time = time.time()

        # Callbacks
        self._tick_callbacks = []
        self._beat_callbacks = []
        self._bar_callbacks = []

        # Threading
        self._clock_thread = None
        self._running = False
        self._lock = threading.Lock()

        # External sync
        self._midi_sync = None
        if external_sync:
            from .midi_sync import MIDIClockSync
            self._midi_sync = MIDIClockSync()
            self._setup_external_sync()

    @property
    def beats_per_bar(self) -> int:
        """Get beats per bar from time signature."""
        return self.time_signature[0]

    @property
    def ticks_per_beat(self) -> int:
        """Get ticks per beat."""
        return self.PPQN

    @property
    def ticks_per_bar(self) -> int:
        """Get ticks per bar."""
        return self.ticks_per_beat * self.beats_per_bar

    @property
    def beat_duration(self) -> float:
        """Get duration of one beat in seconds."""
        return 60.0 / self.tempo

    @property
    def tick_duration(self) -> float:
        """Get duration of one tick in seconds."""
        return self.beat_duration / self.ticks_per_beat

    def start(self):
        """Start playback."""
        with self._lock:
            if self.state == TransportState.STOPPED or self.state == TransportState.PAUSED:
                self.state = TransportState.PLAYING
                self._last_tick_time = time.time()
                self._start_clock_thread()
                logger.info(f"Started playback at {self.tempo} BPM")

    def stop(self):
        """Stop playback."""
        with self._lock:
            if self.state != TransportState.STOPPED:
                self.state = TransportState.STOPPED
                self._stop_clock_thread()
                logger.info("Stopped playback")

    def pause(self):
        """Pause playback."""
        with self._lock:
            if self.state == TransportState.PLAYING:
                self.state = TransportState.PAUSED
                self._stop_clock_thread()
                logger.info("Paused playback")

    def record(self):
        """Start recording."""
        with self._lock:
            self.state = TransportState.RECORDING
            self._last_tick_time = time.time()
            self._start_clock_thread()
            logger.info("Started recording")

    def reset(self):
        """Reset position to start."""
        with self._lock:
            self.position = TimePosition()
            self._tick_count = 0
            logger.info("Reset to beginning")

    def set_tempo(self, tempo: float):
        """Set tempo in BPM."""
        with self._lock:
            self.tempo = max(20.0, min(300.0, tempo))  # Clamp 20-300 BPM
            logger.info(f"Tempo set to {self.tempo} BPM")

    def set_position(self, bar: int = 1, beat: int = 1, tick: int = 0):
        """Set playback position."""
        with self._lock:
            self.position.bar = bar
            self.position.beat = beat
            self.position.tick = tick
            self._update_tick_count()
            logger.info(f"Position set to {self.position}")

    def _update_tick_count(self):
        """Update internal tick count from position."""
        self._tick_count = (
            (self.position.bar - 1) * self.ticks_per_bar +
            (self.position.beat - 1) * self.ticks_per_beat +
            self.position.tick
        )

    def _update_position_from_ticks(self):
        """Update position from tick count."""
        total_ticks = self._tick_count

        # Calculate bar
        self.position.bar = (total_ticks // self.ticks_per_bar) + 1
        remaining = total_ticks % self.ticks_per_bar

        # Calculate beat
        self.position.beat = (remaining // self.ticks_per_beat) + 1
        self.position.tick = remaining % self.ticks_per_beat

        # Calculate total beats for easy reference
        self.position.total_beats = self._tick_count / self.ticks_per_beat

    def tick(self):
        """Advance clock by one tick."""
        with self._lock:
            if self.state == TransportState.STOPPED:
                return

            old_beat = self.position.beat
            old_bar = self.position.bar

            # Advance tick count
            self._tick_count += 1
            self._update_position_from_ticks()

            # Trigger callbacks
            self._trigger_tick_callbacks()

            if self.position.beat != old_beat:
                self._trigger_beat_callbacks()

            if self.position.bar != old_bar:
                self._trigger_bar_callbacks()

    def _start_clock_thread(self):
        """Start clock thread for automatic ticking."""
        if self._clock_thread is None or not self._clock_thread.is_alive():
            self._running = True
            self._clock_thread = threading.Thread(target=self._clock_loop, daemon=True)
            self._clock_thread.start()

    def _stop_clock_thread(self):
        """Stop clock thread."""
        self._running = False
        if self._clock_thread:
            self._clock_thread.join(timeout=1.0)

    def _clock_loop(self):
        """Main clock loop running in thread."""
        while self._running:
            current_time = time.time()
            elapsed = current_time - self._last_tick_time

            if elapsed >= self.tick_duration:
                self.tick()
                self._last_tick_time = current_time

            # Sleep for a fraction of tick duration
            time.sleep(self.tick_duration / 10)

    def on_tick(self, callback: Callable):
        """Register tick callback."""
        self._tick_callbacks.append(callback)

    def on_beat(self, callback: Callable):
        """Register beat callback."""
        self._beat_callbacks.append(callback)

    def on_bar(self, callback: Callable):
        """Register bar callback."""
        self._bar_callbacks.append(callback)

    def _trigger_tick_callbacks(self):
        """Trigger all tick callbacks."""
        for callback in self._tick_callbacks:
            try:
                callback(self.position)
            except Exception as e:
                logger.error(f"Tick callback error: {e}")

    def _trigger_beat_callbacks(self):
        """Trigger all beat callbacks."""
        for callback in self._beat_callbacks:
            try:
                callback(self.position)
            except Exception as e:
                logger.error(f"Beat callback error: {e}")

    def _trigger_bar_callbacks(self):
        """Trigger all bar callbacks."""
        for callback in self._bar_callbacks:
            try:
                callback(self.position)
            except Exception as e:
                logger.error(f"Bar callback error: {e}")

    def get_position(self) -> TimePosition:
        """Get current position."""
        with self._lock:
            return TimePosition(
                bar=self.position.bar,
                beat=self.position.beat,
                tick=self.position.tick,
                total_beats=self.position.total_beats
            )

    def is_playing(self) -> bool:
        """Check if clock is playing."""
        return self.state in [TransportState.PLAYING, TransportState.RECORDING]

    def get_beat_fraction(self) -> float:
        """
        Get current position within beat as fraction (0.0-1.0).
        Useful for swing and groove calculations.
        """
        return self.position.tick / self.ticks_per_beat

    def quantize_to_beat(self):
        """Snap position to nearest beat."""
        with self._lock:
            self.position.tick = 0
            self._update_tick_count()

    def quantize_to_bar(self):
        """Snap position to nearest bar."""
        with self._lock:
            self.position.beat = 1
            self.position.tick = 0
            self._update_tick_count()

    def _setup_external_sync(self):
        """Setup callbacks for external MIDI sync."""
        if not self._midi_sync:
            return

        # Sync tempo changes
        self._midi_sync.on_tempo_change(self._on_external_tempo_change)

        # Sync transport
        self._midi_sync.on_start(self._on_external_start)
        self._midi_sync.on_stop(self._on_external_stop)

        logger.info("External MIDI sync configured")

    def _on_external_tempo_change(self, tempo: float):
        """Handle tempo change from external clock."""
        with self._lock:
            self.tempo = tempo
            logger.info(f"Tempo synced from external clock: {tempo:.1f} BPM")

    def _on_external_start(self):
        """Handle start from external clock."""
        self.start()
        logger.info("Started from external MIDI clock")

    def _on_external_stop(self):
        """Handle stop from external clock."""
        self.stop()
        logger.info("Stopped from external MIDI clock")

    def enable_external_sync(self, port_name: Optional[str] = None) -> bool:
        """
        Enable external MIDI clock sync.

        Args:
            port_name: MIDI input port name (auto-detect if None)

        Returns:
            True if connected successfully
        """
        if not self._midi_sync:
            from .midi_sync import MIDIClockSync
            self._midi_sync = MIDIClockSync()
            self._setup_external_sync()

        if self._midi_sync.connect(port_name):
            self._midi_sync.start_listening()
            self.external_sync = True
            logger.info("External MIDI sync enabled")
            return True

        return False

    def disable_external_sync(self):
        """Disable external MIDI clock sync."""
        if self._midi_sync:
            self._midi_sync.close()
        self.external_sync = False
        logger.info("External MIDI sync disabled")

    def get_external_tempo(self) -> Optional[float]:
        """Get tempo from external MIDI clock."""
        if self._midi_sync:
            return self._midi_sync.get_tempo()
        return None

    def is_externally_synced(self) -> bool:
        """Check if synced to external clock."""
        return self.external_sync and self._midi_sync is not None
