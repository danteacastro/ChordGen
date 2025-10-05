"""Chord progression generation using Markov models and music theory rules."""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np
from .chords import Chord, NOTE_NAMES
from .utils import timing_decorator
from .config import settings

logger = logging.getLogger(__name__)


# Common cadential patterns
MAJOR_CADENCES = [
    ["V", "I"],           # Authentic cadence
    ["IV", "I"],          # Plagal cadence
    ["ii", "V", "I"],     # ii-V-I
    ["vi", "IV", "I", "V"],  # Pop progression
    ["I", "V", "vi", "IV"],  # Axis progression
]

MINOR_CADENCES = [
    ["v", "i"],
    ["iv", "i"],
    ["ii°", "v", "i"],
    ["VI", "iv", "i", "v"],
    ["i", "v", "VI", "iv"],
]


@dataclass
class StyleProfile:
    """
    Musical style profile extracted from analysis.
    """
    key: str
    mode: str  # "major" or "minor"
    tempo: float
    harmonic_rhythm: float = 1.0  # Average beats per chord
    chord_functions: List[str] = None  # List of Roman numerals used
    secondary_dominant_rate: float = 0.0  # % of secondary dominants
    borrowed_chord_rate: float = 0.0  # % of borrowed chords

    def __post_init__(self):
        if self.chord_functions is None:
            # Default diatonic progressions
            if self.mode == "major":
                self.chord_functions = ["I", "ii", "iii", "IV", "V", "vi"]
            else:
                self.chord_functions = ["i", "ii°", "III", "iv", "v", "VI", "VII"]


class ProgressionGenerator:
    """
    Generate chord progressions based on style profile.
    Uses Markov chain with music theory constraints.
    """

    def __init__(self, style_profile: StyleProfile, seed: Optional[int] = None):
        """
        Initialize generator.

        Args:
            style_profile: Style profile from analysis
            seed: Random seed for reproducibility
        """
        self.profile = style_profile
        self.rng = np.random.RandomState(seed or settings.generation.seed)

        # Build Markov transition matrix from common progressions
        self.transition_matrix = self._build_markov_model()

    def _build_markov_model(self) -> Dict[str, Dict[str, float]]:
        """
        Build first-order Markov model from music theory rules.

        Returns:
            Dictionary mapping current_chord -> {next_chord: probability}
        """
        transitions = {}

        # Get appropriate scale degrees for key
        if self.profile.mode == "major":
            scale_degrees = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
            cadences = MAJOR_CADENCES
        else:
            scale_degrees = ["i", "ii°", "III", "iv", "v", "VI", "VII"]
            cadences = MINOR_CADENCES

        # Initialize with uniform distribution
        for degree in scale_degrees:
            transitions[degree] = {d: 0.1 for d in scale_degrees}

        # Add functional harmony rules
        if self.profile.mode == "major":
            # I can go anywhere, but commonly to IV, V, vi
            transitions["I"]["IV"] = 0.25
            transitions["I"]["V"] = 0.25
            transitions["I"]["vi"] = 0.20

            # ii commonly goes to V
            transitions["ii"]["V"] = 0.50
            transitions["ii"]["I"] = 0.15

            # iii commonly goes to vi or IV
            transitions["iii"]["vi"] = 0.30
            transitions["iii"]["IV"] = 0.25

            # IV commonly goes to V or I
            transitions["IV"]["V"] = 0.35
            transitions["IV"]["I"] = 0.30
            transitions["IV"]["ii"] = 0.15

            # V strongly resolves to I
            transitions["V"]["I"] = 0.60
            transitions["V"]["vi"] = 0.20  # Deceptive cadence

            # vi commonly goes to IV or ii
            transitions["vi"]["IV"] = 0.30
            transitions["vi"]["ii"] = 0.25
            transitions["vi"]["V"] = 0.20

            # vii° resolves to I
            transitions["vii°"]["I"] = 0.70

        else:  # minor
            # i can go to iv, v, VI
            transitions["i"]["iv"] = 0.25
            transitions["i"]["v"] = 0.25
            transitions["i"]["VI"] = 0.20

            # ii° goes to v
            transitions["ii°"]["v"] = 0.50
            transitions["ii°"]["i"] = 0.15

            # III goes to VI or iv
            transitions["III"]["VI"] = 0.30
            transitions["III"]["iv"] = 0.25

            # iv goes to v or i
            transitions["iv"]["v"] = 0.35
            transitions["iv"]["i"] = 0.30
            transitions["iv"]["ii°"] = 0.15

            # v resolves to i
            transitions["v"]["i"] = 0.60
            transitions["v"]["VI"] = 0.20  # Deceptive

            # VI goes to iv or ii°
            transitions["VI"]["iv"] = 0.30
            transitions["VI"]["ii°"] = 0.25
            transitions["VI"]["v"] = 0.20

            # VII resolves to i
            transitions["VII"]["i"] = 0.70

        # Normalize probabilities
        for source in transitions:
            total = sum(transitions[source].values())
            if total > 0:
                transitions[source] = {k: v/total for k, v in transitions[source].items()}

        return transitions

    def _choose_next_chord(self, current: str) -> str:
        """
        Choose next chord based on Markov model.

        Args:
            current: Current Roman numeral

        Returns:
            Next Roman numeral
        """
        if current not in self.transition_matrix:
            # Fallback to random choice
            if self.profile.mode == "major":
                return self.rng.choice(["I", "IV", "V", "vi"])
            else:
                return self.rng.choice(["i", "iv", "v", "VI"])

        transitions = self.transition_matrix[current]
        chords = list(transitions.keys())
        probs = list(transitions.values())

        return self.rng.choice(chords, p=probs)

    def _ensure_cadence(self, progression: List[str]) -> List[str]:
        """
        Ensure progression ends with a proper cadence.

        Args:
            progression: List of Roman numerals

        Returns:
            Modified progression with cadence
        """
        cadences = MAJOR_CADENCES if self.profile.mode == "major" else MINOR_CADENCES

        # Choose a random cadence
        cadence = self.rng.choice(cadences)

        # Weight towards authentic cadence for endings
        if self.rng.random() < settings.generation.cadence_weight:
            cadence = cadences[0]  # V-I or v-i

        # Replace last few chords with cadence
        cadence_length = len(cadence)
        if len(progression) >= cadence_length:
            progression[-cadence_length:] = cadence

        return progression

    @timing_decorator
    def generate(
        self,
        bars: int = 8,
        complexity: int = 0,
        start_chord: Optional[str] = None
    ) -> List[Chord]:
        """
        Generate a chord progression.

        Args:
            bars: Number of bars to generate
            complexity: 0=triads only, 1=add V/V and secondary, 2=add modal mixture
            start_chord: Optional starting chord (default: I or i)

        Returns:
            List of Chord objects
        """
        # Determine number of chords based on harmonic rhythm
        chords_per_bar = 1.0 / self.profile.harmonic_rhythm
        num_chords = max(int(bars * chords_per_bar), bars // 2)

        logger.info(f"Generating {num_chords} chords over {bars} bars")

        # Start with tonic
        if start_chord is None:
            current = "I" if self.profile.mode == "major" else "i"
        else:
            current = start_chord

        roman_progression = [current]

        # Generate progression using Markov chain
        for _ in range(num_chords - 1):
            next_chord = self._choose_next_chord(current)
            roman_progression.append(next_chord)
            current = next_chord

        # Ensure proper cadence at the end
        roman_progression = self._ensure_cadence(roman_progression)

        # Convert Roman numerals to concrete chords
        progression = self._romanize_to_chords(
            roman_progression,
            complexity=complexity
        )

        # Distribute over bars
        progression = self._distribute_timing(progression, bars)

        logger.info(f"Generated progression: {[str(c) for c in progression]}")
        return progression

    def _romanize_to_chords(
        self,
        roman_numerals: List[str],
        complexity: int = 0
    ) -> List[Chord]:
        """
        Convert Roman numerals to concrete Chord objects.

        Args:
            roman_numerals: List of Roman numeral strings
            complexity: Chord complexity level

        Returns:
            List of Chord objects
        """
        key_idx = NOTE_NAMES.index(self.profile.key)

        if self.profile.mode == "major":
            scale = [0, 2, 4, 5, 7, 9, 11]  # Major scale intervals
            scale_qualities = ["maj", "min", "min", "maj", "maj", "min", "dim"]
        else:
            scale = [0, 2, 3, 5, 7, 8, 10]  # Natural minor
            scale_qualities = ["min", "dim", "maj", "min", "min", "maj", "maj"]

        chords = []

        for roman in roman_numerals:
            # Parse Roman numeral
            base_roman = roman.replace("maj7", "").replace("7", "").replace("°", "")

            # Map Roman to scale degree
            roman_map = {"I": 0, "II": 1, "III": 2, "IV": 3, "V": 4, "VI": 5, "VII": 6}
            degree_map = {k.lower(): v for k, v in roman_map.items()}
            degree_map.update(roman_map)

            # Extract degree
            for rn, degree in degree_map.items():
                if base_roman.startswith(rn):
                    # Get root note
                    interval = scale[degree]
                    root = NOTE_NAMES[(key_idx + interval) % 12]

                    # Determine quality
                    if "maj7" in roman:
                        quality = "maj7" if complexity >= 1 else "maj"
                    elif "7" in roman:
                        # Check if it's a dominant or minor 7th
                        base_quality = scale_qualities[degree]
                        if base_quality == "maj":
                            quality = "dom7" if complexity >= 1 else "maj"
                        else:
                            quality = "min7" if complexity >= 1 else "min"
                    elif "°" in roman or base_roman.startswith("vii"):
                        quality = "dim"
                    else:
                        quality = scale_qualities[degree]

                    chord = Chord(root=root, quality=quality, roman=roman)
                    chords.append(chord)
                    break

        return chords

    def _distribute_timing(self, chords: List[Chord], bars: int) -> List[Chord]:
        """
        Distribute chords evenly across bars.

        Args:
            chords: List of chords
            bars: Number of bars

        Returns:
            Chords with timing information
        """
        beats_per_chord = (bars * 4) / len(chords)  # Assuming 4/4 time

        beat = 0
        for chord in chords:
            chord.start_beat = int(beat)
            chord.duration_beats = beats_per_chord
            beat += beats_per_chord

        return chords


def create_style_profile_from_analysis(
    key: str,
    mode: str,
    tempo: float,
    detected_chords: List[Chord]
) -> StyleProfile:
    """
    Create a StyleProfile from analysis results.

    Args:
        key: Detected key
        mode: Detected mode
        tempo: Detected tempo
        detected_chords: List of detected chords

    Returns:
        StyleProfile object
    """
    # Extract chord functions (Roman numerals)
    chord_functions = [c.roman for c in detected_chords if c.roman]

    # Calculate harmonic rhythm
    if detected_chords:
        avg_duration = np.mean([c.duration_beats for c in detected_chords])
        harmonic_rhythm = avg_duration
    else:
        harmonic_rhythm = 1.0

    profile = StyleProfile(
        key=key,
        mode=mode,
        tempo=tempo,
        harmonic_rhythm=harmonic_rhythm,
        chord_functions=chord_functions or None
    )

    logger.info(f"Created style profile: {profile.key} {profile.mode}, {profile.tempo} BPM")
    return profile
