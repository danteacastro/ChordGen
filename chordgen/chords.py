"""Chord detection using templates, HMM/Viterbi, and romanization."""

import logging
from typing import List, Tuple, Optional
import numpy as np
from dataclasses import dataclass
from .utils import timing_decorator

logger = logging.getLogger(__name__)


# Roman numeral mappings for major and minor keys
MAJOR_SCALE_DEGREES = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
MINOR_SCALE_DEGREES = ['i', 'ii°', 'III', 'iv', 'v', 'VI', 'VII']

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


@dataclass
class Chord:
    """Represents a detected chord."""
    root: str           # Root note (C, D#, etc.)
    quality: str        # maj, min, maj7, min7, dom7, dim
    roman: Optional[str] = None  # Roman numeral in key
    start_beat: int = 0
    duration_beats: float = 1.0

    def __str__(self):
        if self.roman:
            return f"{self.roman} ({self.root}{self.quality})"
        return f"{self.root}{self.quality}"


def create_chord_templates(extended: bool = False) -> Tuple[List[str], np.ndarray]:
    """
    Create chord templates for matching.

    Args:
        extended: If True, include 7th chords

    Returns:
        Tuple of (chord_labels, template_matrix)
        template_matrix shape: (n_chords, 12) - one-hot pitch class vectors
    """
    templates = []
    labels = []

    # Basic triads for all 12 roots
    for root_idx in range(12):
        root = NOTE_NAMES[root_idx]

        # Major triad: root, maj3, P5
        maj_template = np.zeros(12)
        maj_template[(root_idx + 0) % 12] = 1.0  # Root
        maj_template[(root_idx + 4) % 12] = 1.0  # Major 3rd
        maj_template[(root_idx + 7) % 12] = 1.0  # Perfect 5th
        templates.append(maj_template)
        labels.append(f"{root}:maj")

        # Minor triad: root, min3, P5
        min_template = np.zeros(12)
        min_template[(root_idx + 0) % 12] = 1.0  # Root
        min_template[(root_idx + 3) % 12] = 1.0  # Minor 3rd
        min_template[(root_idx + 7) % 12] = 1.0  # Perfect 5th
        templates.append(min_template)
        labels.append(f"{root}:min")

        # Diminished triad: root, min3, dim5
        dim_template = np.zeros(12)
        dim_template[(root_idx + 0) % 12] = 1.0  # Root
        dim_template[(root_idx + 3) % 12] = 1.0  # Minor 3rd
        dim_template[(root_idx + 6) % 12] = 1.0  # Diminished 5th
        templates.append(dim_template)
        labels.append(f"{root}:dim")

    if extended:
        # Add 7th chords
        for root_idx in range(12):
            root = NOTE_NAMES[root_idx]

            # Major 7th
            maj7_template = np.zeros(12)
            maj7_template[(root_idx + 0) % 12] = 1.0
            maj7_template[(root_idx + 4) % 12] = 1.0
            maj7_template[(root_idx + 7) % 12] = 1.0
            maj7_template[(root_idx + 11) % 12] = 1.0  # Major 7th
            templates.append(maj7_template)
            labels.append(f"{root}:maj7")

            # Minor 7th
            min7_template = np.zeros(12)
            min7_template[(root_idx + 0) % 12] = 1.0
            min7_template[(root_idx + 3) % 12] = 1.0
            min7_template[(root_idx + 7) % 12] = 1.0
            min7_template[(root_idx + 10) % 12] = 1.0  # Minor 7th
            templates.append(min7_template)
            labels.append(f"{root}:min7")

            # Dominant 7th
            dom7_template = np.zeros(12)
            dom7_template[(root_idx + 0) % 12] = 1.0
            dom7_template[(root_idx + 4) % 12] = 1.0
            dom7_template[(root_idx + 7) % 12] = 1.0
            dom7_template[(root_idx + 10) % 12] = 1.0  # Minor 7th
            templates.append(dom7_template)
            labels.append(f"{root}:dom7")

    template_matrix = np.array(templates)
    logger.info(f"Created {len(labels)} chord templates")

    return labels, template_matrix


class ChordHMM:
    """
    Hidden Markov Model for chord detection using Viterbi algorithm.
    """

    def __init__(self, chord_labels: List[str], key: str, mode: str):
        """
        Initialize HMM.

        Args:
            chord_labels: List of possible chord labels
            key: Key note (C, D, etc.)
            mode: major or minor
        """
        self.chord_labels = chord_labels
        self.key = key
        self.mode = mode
        self.n_states = len(chord_labels)

        # Build transition matrix based on music theory
        self.transition_matrix = self._build_transition_matrix()

    def _build_transition_matrix(self) -> np.ndarray:
        """
        Build transition probability matrix based on functional harmony.

        Returns:
            Matrix of shape (n_states, n_states)
        """
        # Initialize uniform with small probability
        trans = np.ones((self.n_states, self.n_states)) * 0.01

        # Self-transitions (chord repetition)
        np.fill_diagonal(trans, 0.5)

        # Parse key and mode to find diatonic chords
        key_idx = NOTE_NAMES.index(self.key)

        if self.mode == "major":
            # Major key: I, ii, iii, IV, V, vi, vii°
            scale = [0, 2, 4, 5, 7, 9, 11]  # Major scale intervals
            qualities = ["maj", "min", "min", "maj", "maj", "min", "dim"]
        else:
            # Minor key: i, ii°, III, iv, v, VI, VII
            scale = [0, 2, 3, 5, 7, 8, 10]  # Natural minor scale intervals
            qualities = ["min", "dim", "maj", "min", "min", "maj", "maj"]

        # Find indices of diatonic chords
        diatonic_indices = []
        for degree_idx, (interval, quality) in enumerate(zip(scale, qualities)):
            root = NOTE_NAMES[(key_idx + interval) % 12]
            label = f"{root}:{quality}"
            if label in self.chord_labels:
                idx = self.chord_labels.index(label)
                diatonic_indices.append((degree_idx, idx))

        # Enhance probabilities for functional progressions
        for i, (deg_i, idx_i) in enumerate(diatonic_indices):
            for j, (deg_j, idx_j) in enumerate(diatonic_indices):
                # Common progressions
                if self.mode == "major":
                    # I → IV, I → V, I → vi
                    if deg_i == 0 and deg_j in [3, 4, 5]:
                        trans[idx_i, idx_j] = 0.15
                    # ii → V
                    elif deg_i == 1 and deg_j == 4:
                        trans[idx_i, idx_j] = 0.25
                    # IV → V, IV → I
                    elif deg_i == 3 and deg_j in [4, 0]:
                        trans[idx_i, idx_j] = 0.20
                    # V → I (strong cadence)
                    elif deg_i == 4 and deg_j == 0:
                        trans[idx_i, idx_j] = 0.30
                    # vi → IV, vi → ii
                    elif deg_i == 5 and deg_j in [3, 1]:
                        trans[idx_i, idx_j] = 0.15

                else:  # minor
                    # i → iv, i → v, i → VI
                    if deg_i == 0 and deg_j in [3, 4, 5]:
                        trans[idx_i, idx_j] = 0.15
                    # ii° → v
                    elif deg_i == 1 and deg_j == 4:
                        trans[idx_i, idx_j] = 0.25
                    # iv → v, iv → i
                    elif deg_i == 3 and deg_j in [4, 0]:
                        trans[idx_i, idx_j] = 0.20
                    # v → i (cadence)
                    elif deg_i == 4 and deg_j == 0:
                        trans[idx_i, idx_j] = 0.30
                    # VI → iv
                    elif deg_i == 5 and deg_j == 3:
                        trans[idx_i, idx_j] = 0.15

        # Normalize rows to sum to 1
        trans = trans / trans.sum(axis=1, keepdims=True)

        return trans

    def viterbi(self, emission_probs: np.ndarray) -> List[int]:
        """
        Viterbi algorithm to find most likely chord sequence.

        Args:
            emission_probs: Matrix of shape (n_frames, n_states)
                          Each row is P(observation | state)

        Returns:
            List of state indices (chord indices)
        """
        n_frames = emission_probs.shape[0]

        # Initialize
        delta = np.zeros((n_frames, self.n_states))
        psi = np.zeros((n_frames, self.n_states), dtype=int)

        # Initial probabilities (uniform start)
        delta[0] = emission_probs[0] / self.n_states

        # Forward pass
        for t in range(1, n_frames):
            for j in range(self.n_states):
                # Find best previous state
                trans_prob = delta[t-1] * self.transition_matrix[:, j]
                psi[t, j] = np.argmax(trans_prob)
                delta[t, j] = np.max(trans_prob) * emission_probs[t, j]

            # Normalize to prevent underflow
            if delta[t].sum() > 0:
                delta[t] /= delta[t].sum()

        # Backtrack to find best path
        path = np.zeros(n_frames, dtype=int)
        path[-1] = np.argmax(delta[-1])

        for t in range(n_frames - 2, -1, -1):
            path[t] = psi[t + 1, path[t + 1]]

        return path.tolist()


class ChordDetector:
    """Main chord detection class."""

    def __init__(self, extended: bool = False):
        """
        Initialize detector.

        Args:
            extended: Use extended chord set (7ths)
        """
        self.extended = extended
        self.chord_labels, self.templates = create_chord_templates(extended)

    @timing_decorator
    def detect(
        self,
        chroma: np.ndarray,
        key: str,
        mode: str,
        use_hmm: bool = True
    ) -> List[Chord]:
        """
        Detect chords from chromagram.

        Args:
            chroma: Chromagram of shape (12, n_frames)
            key: Key note
            mode: major or minor
            use_hmm: Use HMM smoothing

        Returns:
            List of detected Chord objects
        """
        n_frames = chroma.shape[1]

        # Compute emission probabilities (cosine similarity with templates)
        emission_probs = np.zeros((n_frames, len(self.chord_labels)))

        for t in range(n_frames):
            chroma_frame = chroma[:, t]
            # Cosine similarity with each template
            for i, template in enumerate(self.templates):
                similarity = np.dot(chroma_frame, template) / (
                    np.linalg.norm(chroma_frame) * np.linalg.norm(template) + 1e-10
                )
                emission_probs[t, i] = max(0, similarity)  # Clip negative

        # Use HMM to smooth chord sequence
        if use_hmm:
            hmm = ChordHMM(self.chord_labels, key, mode)
            chord_indices = hmm.viterbi(emission_probs)
        else:
            # Simple max-likelihood
            chord_indices = np.argmax(emission_probs, axis=1).tolist()

        # Convert to Chord objects and compress consecutive identical chords
        chords = []
        current_chord = None
        start_beat = 0

        for beat, idx in enumerate(chord_indices):
            label = self.chord_labels[idx]
            root, quality = label.split(':')

            if current_chord is None or current_chord.root != root or current_chord.quality != quality:
                # Save previous chord
                if current_chord is not None:
                    current_chord.duration_beats = beat - start_beat
                    chords.append(current_chord)

                # Start new chord
                current_chord = Chord(root=root, quality=quality, start_beat=beat)
                start_beat = beat

        # Add final chord
        if current_chord is not None:
            current_chord.duration_beats = n_frames - start_beat
            chords.append(current_chord)

        # Romanize chords
        chords = self._romanize_chords(chords, key, mode)

        logger.info(f"Detected {len(chords)} unique chords")
        return chords

    def _romanize_chords(self, chords: List[Chord], key: str, mode: str) -> List[Chord]:
        """Add Roman numeral analysis to chords."""
        key_idx = NOTE_NAMES.index(key)

        if mode == "major":
            scale = [0, 2, 4, 5, 7, 9, 11]
            numerals = MAJOR_SCALE_DEGREES
        else:
            scale = [0, 2, 3, 5, 7, 8, 10]
            numerals = MINOR_SCALE_DEGREES

        for chord in chords:
            root_idx = NOTE_NAMES.index(chord.root)
            # Find interval from key
            interval = (root_idx - key_idx) % 12

            # Check if diatonic
            if interval in scale:
                degree = scale.index(interval)
                roman = numerals[degree]

                # Adjust quality notation
                if chord.quality == "maj7":
                    roman = roman + "maj7"
                elif chord.quality == "min7":
                    roman = roman + "7"
                elif chord.quality == "dom7":
                    roman = roman + "7"

                chord.roman = roman
            else:
                # Non-diatonic (borrowed or secondary dominant)
                chord.roman = f"{chord.root}{chord.quality}"

        return chords
