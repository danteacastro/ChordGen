"""MIDI Clock Sync - Listen to external MIDI clock from Ableton/DAW."""

import logging
import mido
import time
from typing import Optional, Callable
from dataclasses import dataclass
from threading import Thread, Lock

logger = logging.getLogger(__name__)


@dataclass
class MIDIClockState:
    """State of external MIDI clock."""
    tempo: float = 120.0  # Calculated BPM
    running: bool = False
    last_clock_time: float = 0.0
    clock_count: int = 0  # Count of 0xF8 messages

    # MIDI clock sends 24 pulses per quarter note
    PPQN = 24


class MIDIClockSync:
    """
    Synchronizes to external MIDI clock from Ableton or other DAW.

    MIDI Clock Messages:
    - 0xF8: Clock (24 per quarter note)
    - 0xFA: Start
    - 0xFB: Continue
    - 0xFC: Stop
    - 0xFE: Active Sensing
    """

    def __init__(self, port_name: Optional[str] = None):
        """
        Initialize MIDI clock sync.

        Args:
            port_name: MIDI input port name (auto-detect if None)
        """
        self.port_name = port_name
        self.port = None
        self.state = MIDIClockState()
        self._lock = Lock()

        # Callbacks
        self._tempo_change_callbacks = []
        self._start_callbacks = []
        self._stop_callbacks = []

        # Listening thread
        self._listening = False
        self._listen_thread = None

        # Tempo calculation
        self._clock_times = []  # Last few clock message timestamps
        self._tempo_window = 24  # Calculate over 1 beat (24 clocks)

    def list_input_ports(self) -> list:
        """List available MIDI input ports."""
        return mido.get_input_names()

    def connect(self, port_name: Optional[str] = None) -> bool:
        """
        Connect to MIDI input port.

        Args:
            port_name: Port name (uses stored or auto-detects if None)

        Returns:
            True if connected successfully
        """
        if port_name:
            self.port_name = port_name

        # Auto-detect if not specified
        if not self.port_name:
            ports = self.list_input_ports()
            if ports:
                self.port_name = ports[0]
                logger.info(f"Auto-selected MIDI input: {self.port_name}")
            else:
                logger.error("No MIDI input ports found")
                return False

        try:
            self.port = mido.open_input(self.port_name)
            logger.info(f"Connected to MIDI input: {self.port_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to open MIDI input: {e}")
            return False

    def start_listening(self):
        """Start listening to MIDI clock messages."""
        if not self.port:
            logger.error("No MIDI port connected")
            return

        if self._listening:
            logger.warning("Already listening")
            return

        self._listening = True
        self._listen_thread = Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        logger.info("Started listening to MIDI clock")

    def stop_listening(self):
        """Stop listening to MIDI clock."""
        self._listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=1.0)
        logger.info("Stopped listening to MIDI clock")

    def _listen_loop(self):
        """Main listening loop for MIDI messages."""
        while self._listening and self.port:
            try:
                for msg in self.port.iter_pending():
                    self._process_message(msg)
                time.sleep(0.001)  # Small sleep to avoid CPU spinning
            except Exception as e:
                logger.error(f"Error in MIDI listen loop: {e}")

    def _process_message(self, msg):
        """Process incoming MIDI message."""
        # MIDI Clock messages are system real-time (no .type attribute)
        if isinstance(msg, mido.Message):
            msg_type = msg.type

            if msg_type == 'clock':  # 0xF8
                self._handle_clock()
            elif msg_type == 'start':  # 0xFA
                self._handle_start()
            elif msg_type == 'continue':  # 0xFB
                self._handle_continue()
            elif msg_type == 'stop':  # 0xFC
                self._handle_stop()

    def _handle_clock(self):
        """Handle MIDI clock message (0xF8)."""
        current_time = time.time()

        with self._lock:
            # Record clock time
            self._clock_times.append(current_time)

            # Keep only recent clocks for tempo calculation
            if len(self._clock_times) > self._tempo_window:
                self._clock_times.pop(0)

            # Calculate tempo from clock intervals
            if len(self._clock_times) >= 2:
                # Get time span
                time_span = self._clock_times[-1] - self._clock_times[0]
                num_clocks = len(self._clock_times) - 1

                if time_span > 0 and num_clocks > 0:
                    # Average interval between clocks
                    avg_interval = time_span / num_clocks

                    # 24 clocks per quarter note
                    # tempo (BPM) = 60 / (quarter_note_duration)
                    quarter_note_duration = avg_interval * 24
                    tempo = 60.0 / quarter_note_duration

                    # Update tempo (smooth it a bit)
                    old_tempo = self.state.tempo
                    self.state.tempo = tempo * 0.3 + old_tempo * 0.7

                    # Trigger callbacks if tempo changed significantly
                    if abs(self.state.tempo - old_tempo) > 0.5:
                        self._trigger_tempo_callbacks(self.state.tempo)

            self.state.clock_count += 1
            self.state.last_clock_time = current_time

    def _handle_start(self):
        """Handle MIDI start message (0xFA)."""
        with self._lock:
            self.state.running = True
            self.state.clock_count = 0
            self._clock_times.clear()

        logger.info("MIDI Clock: START")
        self._trigger_start_callbacks()

    def _handle_continue(self):
        """Handle MIDI continue message (0xFB)."""
        with self._lock:
            self.state.running = True

        logger.info("MIDI Clock: CONTINUE")
        self._trigger_start_callbacks()

    def _handle_stop(self):
        """Handle MIDI stop message (0xFC)."""
        with self._lock:
            self.state.running = False
            self._clock_times.clear()

        logger.info("MIDI Clock: STOP")
        self._trigger_stop_callbacks()

    def get_tempo(self) -> float:
        """Get current synchronized tempo."""
        with self._lock:
            return self.state.tempo

    def is_running(self) -> bool:
        """Check if external clock is running."""
        with self._lock:
            return self.state.running

    def on_tempo_change(self, callback: Callable[[float], None]):
        """Register callback for tempo changes."""
        self._tempo_change_callbacks.append(callback)

    def on_start(self, callback: Callable[[], None]):
        """Register callback for transport start."""
        self._start_callbacks.append(callback)

    def on_stop(self, callback: Callable[[], None]):
        """Register callback for transport stop."""
        self._stop_callbacks.append(callback)

    def _trigger_tempo_callbacks(self, tempo: float):
        """Trigger tempo change callbacks."""
        for callback in self._tempo_change_callbacks:
            try:
                callback(tempo)
            except Exception as e:
                logger.error(f"Tempo callback error: {e}")

    def _trigger_start_callbacks(self):
        """Trigger start callbacks."""
        for callback in self._start_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Start callback error: {e}")

    def _trigger_stop_callbacks(self):
        """Trigger stop callbacks."""
        for callback in self._stop_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Stop callback error: {e}")

    def close(self):
        """Close MIDI connection."""
        self.stop_listening()
        if self.port:
            self.port.close()
            logger.info("Closed MIDI input port")

    def __del__(self):
        """Cleanup on destruction."""
        self.close()
