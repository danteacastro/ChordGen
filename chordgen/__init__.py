"""
ChordGen - AI-Powered Chord Progression Generator

Analyze music, detect chords, generate progressions, output MIDI with effects suggestions.
"""

__version__ = "0.1.0"

from . import audio_io
from . import analysis
from . import chords
from . import generate
from . import midi_out
from . import effects
from . import config
from . import utils

__all__ = [
    "audio_io",
    "analysis",
    "chords",
    "generate",
    "midi_out",
    "effects",
    "config",
    "utils",
]
