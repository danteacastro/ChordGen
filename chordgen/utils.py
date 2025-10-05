"""Utility functions for logging, caching, and helpers."""

import logging
import time
from pathlib import Path
from functools import wraps
from typing import Callable, Any
import hashlib
import pickle


def setup_logging(log_file: str = "logs/app.log", level: str = "INFO"):
    """Setup logging to console and file."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )


def timing_decorator(func: Callable) -> Callable:
    """Decorator to time function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        logger = logging.getLogger(func.__module__)
        start = time.time()
        logger.info(f"Starting {func.__name__}")
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"Completed {func.__name__} in {elapsed:.2f}s")
        return result
    return wrapper


class SimpleCache:
    """Simple file-based cache for expensive operations."""

    def __init__(self, cache_dir: Path = Path(".cache")):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_str = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Any:
        """Get cached value."""
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None

    def set(self, key: str, value: Any):
        """Set cached value."""
        cache_file = self.cache_dir / f"{key}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(value, f)

    def cached(self, func: Callable) -> Callable:
        """Decorator to cache function results."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = self._get_cache_key(*args, **kwargs)
            result = self.get(cache_key)
            if result is not None:
                logging.getLogger(func.__module__).debug(f"Cache hit for {func.__name__}")
                return result

            result = func(*args, **kwargs)
            self.set(cache_key, result)
            return result
        return wrapper


# Global cache instance
cache = SimpleCache()


def note_name_to_number(note_name: str) -> int:
    """
    Convert note name to MIDI note number.

    Args:
        note_name: Note name like "C4", "F#3", "Bb5"

    Returns:
        MIDI note number (0-127)

    Examples:
        >>> note_name_to_number("C4")
        60
        >>> note_name_to_number("A4")
        69
    """
    note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

    # Parse note name
    note = note_name[0].upper()
    accidental = ""
    octave_str = ""

    for char in note_name[1:]:
        if char in "#b":
            accidental += char
        else:
            octave_str += char

    octave = int(octave_str)

    # Calculate MIDI number
    midi_num = note_map[note] + (octave + 1) * 12

    # Apply accidentals
    if '#' in accidental:
        midi_num += accidental.count('#')
    if 'b' in accidental:
        midi_num -= accidental.count('b')

    return midi_num


def note_number_to_name(note_num: int) -> str:
    """
    Convert MIDI note number to note name.

    Args:
        note_num: MIDI note number (0-127)

    Returns:
        Note name like "C4"

    Examples:
        >>> note_number_to_name(60)
        'C4'
        >>> note_number_to_name(69)
        'A4'
    """
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (note_num // 12) - 1
    note = note_names[note_num % 12]
    return f"{note}{octave}"


def chord_to_midi_notes(root: str, quality: str, octave: int = 4) -> list[int]:
    """
    Convert chord name to MIDI note numbers.

    Args:
        root: Root note (C, D, E, F, G, A, B)
        quality: Chord quality (maj, min, maj7, min7, dom7, dim, aug)
        octave: Base octave for root note

    Returns:
        List of MIDI note numbers

    Examples:
        >>> chord_to_midi_notes("C", "maj", 4)
        [60, 64, 67]  # C-E-G
        >>> chord_to_midi_notes("C", "min7", 4)
        [60, 63, 67, 70]  # C-Eb-G-Bb
    """
    root_note = note_name_to_number(f"{root}{octave}")

    intervals = {
        "maj": [0, 4, 7],
        "min": [0, 3, 7],
        "dim": [0, 3, 6],
        "aug": [0, 4, 8],
        "maj7": [0, 4, 7, 11],
        "min7": [0, 3, 7, 10],
        "dom7": [0, 4, 7, 10],
        "dim7": [0, 3, 6, 9],
        "hdim7": [0, 3, 6, 10],  # half-diminished
        "maj9": [0, 4, 7, 11, 14],
        "min9": [0, 3, 7, 10, 14],
    }

    if quality not in intervals:
        quality = "maj"  # Default to major

    return [root_note + interval for interval in intervals[quality]]
