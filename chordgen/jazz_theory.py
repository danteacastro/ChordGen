"""Jazz theory - scales, voicings, and chord structures."""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class JazzScale(Enum):
    """Jazz scales with intervals."""
    MAJOR = [0, 2, 4, 5, 7, 9, 11]  # Ionian
    DORIAN = [0, 2, 3, 5, 7, 9, 10]
    PHRYGIAN = [0, 1, 3, 5, 7, 8, 10]
    LYDIAN = [0, 2, 4, 6, 7, 9, 11]
    MIXOLYDIAN = [0, 2, 4, 5, 7, 9, 10]
    AEOLIAN = [0, 2, 3, 5, 7, 8, 10]  # Natural minor
    LOCRIAN = [0, 1, 3, 5, 6, 8, 10]

    # Melodic minor modes
    MELODIC_MINOR = [0, 2, 3, 5, 7, 9, 11]
    DORIAN_b2 = [0, 1, 3, 5, 7, 9, 10]  # Phrygian #6
    LYDIAN_AUGMENTED = [0, 2, 4, 6, 8, 9, 11]
    LYDIAN_DOMINANT = [0, 2, 4, 6, 7, 9, 10]  # Acoustic scale
    MIXOLYDIAN_b6 = [0, 2, 4, 5, 7, 8, 10]
    LOCRIAN_SHARP2 = [0, 2, 3, 5, 6, 8, 10]  # Half-diminished scale
    ALTERED = [0, 1, 3, 4, 6, 8, 10]  # Super Locrian

    # Other jazz scales
    HARMONIC_MINOR = [0, 2, 3, 5, 7, 8, 11]
    WHOLE_TONE = [0, 2, 4, 6, 8, 10]
    DIMINISHED = [0, 2, 3, 5, 6, 8, 9, 11]  # Half-whole
    WHOLE_HALF_DIM = [0, 1, 3, 4, 6, 7, 9, 10]  # Whole-half
    BLUES = [0, 3, 5, 6, 7, 10]
    BEBOP_MAJOR = [0, 2, 4, 5, 7, 8, 9, 11]
    BEBOP_DOMINANT = [0, 2, 4, 5, 7, 9, 10, 11]


class ChordVoicing(Enum):
    """Jazz chord voicing types."""
    ROOT_POSITION = "root"  # 1-3-5-7
    FIRST_INVERSION = "1st"  # 3-5-7-1
    SECOND_INVERSION = "2nd"  # 5-7-1-3
    THIRD_INVERSION = "3rd"  # 7-1-3-5

    # Jazz voicings
    DROP_2 = "drop2"  # Drop 2nd voice by octave: 1-5-7-3
    DROP_3 = "drop3"  # Drop 3rd voice by octave: 1-7-3-5
    DROP_2_4 = "drop24"  # Drop 2nd and 4th: 1-5-3-7 (one octave lower)

    # Rootless voicings (for left hand piano comping)
    ROOTLESS_A = "rootless_a"  # 3-5-7-9
    ROOTLESS_B = "rootless_b"  # 7-9-3-5

    # Shell voicings (essential tones only)
    SHELL = "shell"  # 1-3-7 or 1-7-3

    # Upper structures
    UPPER_STRUCTURE = "upper"  # Shell + tensions


@dataclass
class ChordStructure:
    """Detailed chord structure with jazz theory."""
    root: str
    quality: str
    intervals: List[int]  # Intervals from root
    scale_degrees: List[str]  # e.g., ['1', 'b3', '5', 'b7']
    notes: List[str]  # Note names
    midi_notes: List[int]  # MIDI note numbers
    recommended_scale: JazzScale
    tensions: List[str]  # Available tensions (9, 11, 13)
    avoid_notes: List[str]  # Notes to avoid


class JazzTheory:
    """Jazz theory helper for scales and chord structures."""

    # Note names
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Chord interval templates
    CHORD_INTERVALS = {
        'maj': [0, 4, 7],
        'min': [0, 3, 7],
        'dim': [0, 3, 6],
        'aug': [0, 4, 8],
        'maj7': [0, 4, 7, 11],
        'min7': [0, 3, 7, 10],
        'dom7': [0, 4, 7, 10],
        '7': [0, 4, 7, 10],  # Alias for dom7
        'min7b5': [0, 3, 6, 10],  # Half-diminished
        'dim7': [0, 3, 6, 9],
        'maj9': [0, 4, 7, 11, 14],
        'min9': [0, 3, 7, 10, 14],
        'dom9': [0, 4, 7, 10, 14],
        '9': [0, 4, 7, 10, 14],
        'maj11': [0, 4, 7, 11, 14, 17],
        'min11': [0, 3, 7, 10, 14, 17],
        'dom11': [0, 4, 7, 10, 14, 17],
        'maj13': [0, 4, 7, 11, 14, 21],
        '13': [0, 4, 7, 10, 14, 21],
        'sus2': [0, 2, 7],
        'sus4': [0, 5, 7],
        '7sus4': [0, 5, 7, 10],
        '6': [0, 4, 7, 9],
        'min6': [0, 3, 7, 9],
        'm7b5': [0, 3, 6, 10],  # Alias
        'ø7': [0, 3, 6, 10],  # Half-diminished symbol
    }

    # Scale recommendations for chord types
    CHORD_SCALE_MAP = {
        'maj7': JazzScale.MAJOR,
        'maj9': JazzScale.MAJOR,
        'maj13': JazzScale.LYDIAN,
        'dom7': JazzScale.MIXOLYDIAN,
        'dom9': JazzScale.MIXOLYDIAN,
        '7alt': JazzScale.ALTERED,
        '7#11': JazzScale.LYDIAN_DOMINANT,
        'min7': JazzScale.DORIAN,
        'min9': JazzScale.DORIAN,
        'min6': JazzScale.DORIAN,
        'min7b5': JazzScale.LOCRIAN_SHARP2,
        'ø7': JazzScale.LOCRIAN_SHARP2,
        'dim7': JazzScale.WHOLE_HALF_DIM,
    }

    @classmethod
    def get_scale_notes(cls, root: str, scale: JazzScale, octave: int = 4) -> List[int]:
        """
        Get MIDI notes for a scale.

        Args:
            root: Root note name
            scale: Jazz scale
            octave: Starting octave

        Returns:
            List of MIDI note numbers
        """
        root_num = cls.NOTE_NAMES.index(root)
        base_note = root_num + (octave * 12)

        notes = []
        for interval in scale.value:
            notes.append(base_note + interval)

        return notes

    @classmethod
    def get_scale_note_names(cls, root: str, scale: JazzScale) -> List[str]:
        """Get note names for a scale."""
        root_num = cls.NOTE_NAMES.index(root)

        note_names = []
        for interval in scale.value:
            note_idx = (root_num + interval) % 12
            note_names.append(cls.NOTE_NAMES[note_idx])

        return note_names

    @classmethod
    def analyze_chord(cls, root: str, quality: str, octave: int = 4) -> ChordStructure:
        """
        Analyze chord structure with jazz theory.

        Args:
            root: Root note
            quality: Chord quality
            octave: Octave for MIDI notes

        Returns:
            ChordStructure with full analysis
        """
        # Get intervals
        intervals = cls.CHORD_INTERVALS.get(quality, [0, 4, 7])

        # Calculate MIDI notes
        root_num = cls.NOTE_NAMES.index(root)
        base_note = root_num + (octave * 12)
        midi_notes = [base_note + interval for interval in intervals]

        # Get note names
        notes = []
        for interval in intervals:
            note_idx = (root_num + interval) % 12
            notes.append(cls.NOTE_NAMES[note_idx])

        # Get scale degrees
        scale_degrees = cls._get_scale_degrees(intervals)

        # Recommended scale
        recommended_scale = cls.CHORD_SCALE_MAP.get(quality, JazzScale.MAJOR)

        # Available tensions
        tensions = cls._get_available_tensions(quality)

        # Avoid notes
        avoid_notes = cls._get_avoid_notes(quality)

        return ChordStructure(
            root=root,
            quality=quality,
            intervals=intervals,
            scale_degrees=scale_degrees,
            notes=notes,
            midi_notes=midi_notes,
            recommended_scale=recommended_scale,
            tensions=tensions,
            avoid_notes=avoid_notes
        )

    @classmethod
    def _get_scale_degrees(cls, intervals: List[int]) -> List[str]:
        """Convert intervals to scale degree notation."""
        degree_map = {
            0: '1', 1: 'b9', 2: '9', 3: 'b3', 4: '3',
            5: '11', 6: '#11', 7: '5', 8: 'b13', 9: '13',
            10: 'b7', 11: '7', 12: '1', 14: '9'
        }

        return [degree_map.get(i, str(i)) for i in intervals]

    @classmethod
    def _get_available_tensions(cls, quality: str) -> List[str]:
        """Get available tensions for chord type."""
        tension_map = {
            'maj7': ['9', '13'],
            'maj9': ['13'],
            'dom7': ['9', 'b9', '#9', '#11', 'b13', '13'],
            'min7': ['9', '11'],
            'min7b5': ['b9', '11'],
        }
        return tension_map.get(quality, [])

    @classmethod
    def _get_avoid_notes(cls, quality: str) -> List[str]:
        """Get avoid notes for chord type."""
        avoid_map = {
            'maj7': ['11'],  # Avoid natural 11 on major chords
            'min7': ['b13'],  # Avoid b13 on minor
            'dom7': [],  # Dominant can handle most tensions
        }
        return avoid_map.get(quality, [])

    @classmethod
    def apply_voicing(
        cls,
        chord_notes: List[int],
        voicing: ChordVoicing,
        bass_note: Optional[int] = None
    ) -> List[int]:
        """
        Apply jazz voicing to chord notes.

        Args:
            chord_notes: List of MIDI note numbers
            voicing: Voicing type
            bass_note: Optional separate bass note

        Returns:
            Voiced chord notes
        """
        if len(chord_notes) < 3:
            return chord_notes

        root = chord_notes[0]

        if voicing == ChordVoicing.ROOT_POSITION:
            return chord_notes

        elif voicing == ChordVoicing.FIRST_INVERSION:
            return chord_notes[1:] + [chord_notes[0] + 12]

        elif voicing == ChordVoicing.SECOND_INVERSION:
            return chord_notes[2:] + [chord_notes[0] + 12, chord_notes[1] + 12]

        elif voicing == ChordVoicing.DROP_2:
            if len(chord_notes) >= 4:
                # 1-5-7-3 (drop 2nd highest by octave)
                return [
                    chord_notes[0],  # Root
                    chord_notes[2] - 12,  # 5th down octave
                    chord_notes[3],  # 7th
                    chord_notes[1]  # 3rd
                ]

        elif voicing == ChordVoicing.DROP_3:
            if len(chord_notes) >= 4:
                # 1-7-3-5
                return [
                    chord_notes[0],  # Root
                    chord_notes[3] - 12,  # 7th down octave
                    chord_notes[1],  # 3rd
                    chord_notes[2]  # 5th
                ]

        elif voicing == ChordVoicing.ROOTLESS_A:
            if len(chord_notes) >= 4:
                # 3-5-7-9 (no root)
                return chord_notes[1:4] + [chord_notes[0] + 14]  # Add 9

        elif voicing == ChordVoicing.ROOTLESS_B:
            if len(chord_notes) >= 4:
                # 7-9-3-5
                return [
                    chord_notes[3],  # 7th
                    chord_notes[0] + 14,  # 9
                    chord_notes[1] + 12,  # 3rd up
                    chord_notes[2] + 12  # 5th up
                ]

        elif voicing == ChordVoicing.SHELL:
            # 1-3-7 (essential tones)
            if len(chord_notes) >= 4:
                return [chord_notes[0], chord_notes[1], chord_notes[3]]

        return chord_notes

    @classmethod
    def get_chord_formula(cls, quality: str) -> str:
        """Get chord formula in scale degrees."""
        intervals = cls.CHORD_INTERVALS.get(quality, [0, 4, 7])
        degrees = cls._get_scale_degrees(intervals)
        return ' - '.join(degrees)
