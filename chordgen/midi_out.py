"""MIDI output: live to virtual ports and file export."""

import logging
from pathlib import Path
from typing import List, Optional
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
import time
from .chords import Chord
from .utils import chord_to_midi_notes, timing_decorator
from .config import settings

logger = logging.getLogger(__name__)


def list_ports() -> List[str]:
    """
    List available MIDI output ports.

    Returns:
        List of port names
    """
    try:
        ports = mido.get_output_names()
        logger.info(f"Found {len(ports)} MIDI ports: {ports}")
        return ports
    except Exception as e:
        logger.error(f"Failed to list MIDI ports: {e}")
        return []


class MIDISender:
    """Send MIDI messages to a virtual port in real-time."""

    def __init__(self, port_name: Optional[str] = None):
        """
        Initialize MIDI sender.

        Args:
            port_name: Name of MIDI port (None for first available)
        """
        self.port = None
        self.port_name = port_name

        if port_name:
            self._open_port(port_name)

    def _open_port(self, port_name: str):
        """Open MIDI port."""
        try:
            self.port = mido.open_output(port_name)
            self.port_name = port_name
            logger.info(f"Opened MIDI port: {port_name}")
        except Exception as e:
            logger.error(f"Failed to open MIDI port '{port_name}': {e}")
            raise

    def close(self):
        """Close MIDI port."""
        if self.port:
            self.port.close()
            logger.info(f"Closed MIDI port: {self.port_name}")

    def send_chord(
        self,
        chord: Chord,
        velocity: int = None,
        channel: int = None,
        octave: int = 4
    ):
        """
        Send a single chord as MIDI notes.

        Args:
            chord: Chord object
            velocity: Note velocity (0-127)
            channel: MIDI channel (0-15)
            octave: Base octave for chord
        """
        if not self.port:
            logger.warning("No MIDI port open")
            return

        if velocity is None:
            velocity = settings.midi.default_velocity
        if channel is None:
            channel = settings.midi.channel

        # Get MIDI notes for chord
        notes = chord_to_midi_notes(chord.root, chord.quality, octave)

        # Send note-on messages
        for note in notes:
            msg = Message('note_on', note=note, velocity=velocity, channel=channel)
            self.port.send(msg)

        logger.debug(f"Sent chord {chord}: notes {notes}")

    def stop_all_notes(self, channel: int = None):
        """
        Send note-off for all notes.

        Args:
            channel: MIDI channel
        """
        if not self.port:
            return

        if channel is None:
            channel = settings.midi.channel

        # Send note-off for all possible notes
        for note in range(128):
            msg = Message('note_off', note=note, velocity=0, channel=channel)
            self.port.send(msg)

    @timing_decorator
    def send_progression(
        self,
        progression: List[Chord],
        tempo: float = None,
        loop: bool = False,
        stop_callback = None
    ):
        """
        Send chord progression in real-time.

        Args:
            progression: List of chords
            tempo: Tempo in BPM
            loop: Loop the progression
            stop_callback: Function that returns True to stop playback
        """
        if not self.port:
            raise RuntimeError("No MIDI port open")

        if tempo is None:
            tempo = settings.midi.default_tempo

        # Calculate timing
        beat_duration = 60.0 / tempo  # seconds per beat

        logger.info(f"Playing progression at {tempo} BPM")

        try:
            while True:
                for chord in progression:
                    # Check stop callback
                    if stop_callback and stop_callback():
                        break

                    # Send chord
                    self.send_chord(chord)

                    # Wait for chord duration
                    time.sleep(chord.duration_beats * beat_duration)

                    # Stop notes
                    self.stop_all_notes()

                if not loop or (stop_callback and stop_callback()):
                    break

        except KeyboardInterrupt:
            logger.info("Playback interrupted")
        finally:
            self.stop_all_notes()


@timing_decorator
def export_midi(
    progression: List[Chord],
    output_path: Path,
    tempo: float = None,
    include_bass: bool = True,
    include_pad: bool = False
) -> Path:
    """
    Export chord progression to MIDI file.

    Args:
        progression: List of chords
        output_path: Output file path
        tempo: Tempo in BPM
        include_bass: Include bass track (root notes)
        include_pad: Include pad/arp track

    Returns:
        Path to created MIDI file
    """
    if tempo is None:
        tempo = settings.midi.default_tempo

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create MIDI file
    mid = MidiFile(type=1)  # Type 1: multiple tracks

    # Calculate ticks per beat (standard: 480)
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    # Track 1: Chords
    chords_track = MidiTrack()
    mid.tracks.append(chords_track)

    chords_track.append(MetaMessage('track_name', name='Chords', time=0))
    chords_track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo), time=0))

    _add_chord_track(chords_track, progression, ticks_per_beat)

    # Track 2: Bass (optional)
    if include_bass:
        bass_track = MidiTrack()
        mid.tracks.append(bass_track)
        bass_track.append(MetaMessage('track_name', name='Bass', time=0))
        _add_bass_track(bass_track, progression, ticks_per_beat)

    # Track 3: Pad/Arp (optional)
    if include_pad:
        pad_track = MidiTrack()
        mid.tracks.append(pad_track)
        pad_track.append(MetaMessage('track_name', name='Pad', time=0))
        _add_pad_track(pad_track, progression, ticks_per_beat)

    # Save file
    mid.save(output_path)
    logger.info(f"Exported MIDI to: {output_path}")

    return output_path


def _add_chord_track(track: MidiTrack, progression: List[Chord], ticks_per_beat: int):
    """Add chord voicings to track."""
    velocity = settings.midi.default_velocity
    current_time = 0

    for chord in progression:
        # Get notes for chord (middle register)
        notes = chord_to_midi_notes(chord.root, chord.quality, octave=4)

        # Note on at start
        for i, note in enumerate(notes):
            time_delta = 0 if i > 0 else int(current_time)
            track.append(Message('note_on', note=note, velocity=velocity, time=time_delta))
            current_time = 0  # Only first note gets the time delta

        # Calculate duration in ticks
        duration_ticks = int(chord.duration_beats * ticks_per_beat)

        # Note off at end
        for i, note in enumerate(notes):
            time_delta = duration_ticks if i == 0 else 0
            track.append(Message('note_off', note=note, velocity=0, time=time_delta))

        current_time = 0  # Reset for next chord


def _add_bass_track(track: MidiTrack, progression: List[Chord], ticks_per_beat: int):
    """Add bass line (root notes) to track."""
    velocity = settings.midi.default_velocity
    current_time = 0

    for chord in progression:
        # Get root note in bass register
        notes = chord_to_midi_notes(chord.root, "maj", octave=2)
        root = notes[0]  # Just the root

        # Note on
        track.append(Message('note_on', note=root, velocity=velocity, time=int(current_time)))

        # Calculate duration (sustain for full chord duration)
        duration_ticks = int(chord.duration_beats * ticks_per_beat)

        # Note off
        track.append(Message('note_off', note=root, velocity=0, time=duration_ticks))

        current_time = 0


def _add_pad_track(track: MidiTrack, progression: List[Chord], ticks_per_beat: int):
    """Add pad/sustained upper voices to track."""
    velocity = int(settings.midi.default_velocity * 0.7)  # Softer
    current_time = 0

    for chord in progression:
        # Get notes for chord (higher register)
        notes = chord_to_midi_notes(chord.root, chord.quality, octave=5)

        # Use only upper two notes for pad texture
        pad_notes = notes[-2:] if len(notes) >= 2 else notes

        # Note on
        for i, note in enumerate(pad_notes):
            time_delta = 0 if i > 0 else int(current_time)
            track.append(Message('note_on', note=note, velocity=velocity, time=time_delta))

        # Calculate duration
        duration_ticks = int(chord.duration_beats * ticks_per_beat)

        # Note off
        for i, note in enumerate(pad_notes):
            time_delta = duration_ticks if i == 0 else 0
            track.append(Message('note_off', note=note, velocity=0, time=time_delta))

        current_time = 0
