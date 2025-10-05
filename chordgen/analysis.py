"""Audio analysis: tempo, key, chroma, beat tracking."""

import logging
from typing import Tuple, Optional
import numpy as np
import librosa
from scipy import stats
from .config import settings
from .utils import timing_decorator

logger = logging.getLogger(__name__)


# Krumhansl-Schmuckler key profiles
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


@timing_decorator
def detect_tempo_beats(
    audio: np.ndarray,
    sr: int,
    hop_length: Optional[int] = None
) -> Tuple[float, np.ndarray]:
    """
    Detect tempo and beat positions.

    Args:
        audio: Audio time series
        sr: Sample rate
        hop_length: Hop length for analysis

    Returns:
        Tuple of (tempo_bpm, beat_frames)
    """
    if hop_length is None:
        hop_length = settings.analysis.hop_length

    try:
        # Detect tempo and beats
        tempo, beat_frames = librosa.beat.beat_track(
            y=audio,
            sr=sr,
            hop_length=hop_length,
            units='frames'
        )

        logger.info(f"Detected tempo: {tempo:.1f} BPM, {len(beat_frames)} beats")
        return float(tempo), beat_frames

    except Exception as e:
        logger.warning(f"Beat tracking failed: {e}, using default 120 BPM")
        # Fallback: assume 120 BPM and create regular beats
        beat_interval = int((60 / 120) * sr / hop_length)
        total_frames = len(audio) // hop_length
        beat_frames = np.arange(0, total_frames, beat_interval)
        return 120.0, beat_frames


@timing_decorator
def detect_key(
    audio: np.ndarray,
    sr: int,
    hop_length: Optional[int] = None
) -> Tuple[str, str]:
    """
    Detect musical key using chromagram and Krumhansl-Schmuckler profiles.

    Args:
        audio: Audio time series
        sr: Sample rate
        hop_length: Hop length for analysis

    Returns:
        Tuple of (key_note, mode) e.g., ("C", "major")
    """
    if hop_length is None:
        hop_length = settings.analysis.hop_length

    try:
        # Compute chromagram
        chroma = librosa.feature.chroma_cqt(
            y=audio,
            sr=sr,
            hop_length=hop_length
        )

        # Average over time to get pitch class distribution
        pitch_class_dist = np.mean(chroma, axis=1)

        # Correlate with major and minor profiles at all 12 rotations
        major_cors = []
        minor_cors = []

        for i in range(12):
            # Rotate profiles to test each possible key
            rotated_major = np.roll(MAJOR_PROFILE, i)
            rotated_minor = np.roll(MINOR_PROFILE, i)

            # Compute correlation
            major_cor = stats.pearsonr(pitch_class_dist, rotated_major)[0]
            minor_cor = stats.pearsonr(pitch_class_dist, rotated_minor)[0]

            major_cors.append(major_cor)
            minor_cors.append(minor_cor)

        # Find best matches
        best_major_idx = np.argmax(major_cors)
        best_minor_idx = np.argmax(minor_cors)
        best_major_cor = major_cors[best_major_idx]
        best_minor_cor = minor_cors[best_minor_idx]

        # Choose major or minor
        if best_major_cor > best_minor_cor:
            key = NOTE_NAMES[best_major_idx]
            mode = "major"
        else:
            key = NOTE_NAMES[best_minor_idx]
            mode = "minor"

        logger.info(f"Detected key: {key} {mode}")
        return key, mode

    except Exception as e:
        logger.warning(f"Key detection failed: {e}, defaulting to C major")
        return "C", "major"


@timing_decorator
def compute_chroma(
    audio: np.ndarray,
    sr: int,
    beats: Optional[np.ndarray] = None,
    hop_length: Optional[int] = None
) -> np.ndarray:
    """
    Compute beat-synchronized chromagram.

    Args:
        audio: Audio time series
        sr: Sample rate
        beats: Beat frame positions (optional)
        hop_length: Hop length for analysis

    Returns:
        Chromagram array of shape (12, n_beats) if beats provided,
        otherwise (12, n_frames)
    """
    if hop_length is None:
        hop_length = settings.analysis.hop_length

    try:
        # Compute CQT chromagram (more accurate than STFT for music)
        chroma = librosa.feature.chroma_cqt(
            y=audio,
            sr=sr,
            hop_length=hop_length,
            n_chroma=settings.analysis.n_chroma
        )

        # Optionally sync to beats
        if beats is not None and len(beats) > 0:
            chroma = librosa.util.sync(chroma, beats, aggregate=np.median)

        # Normalize
        chroma = librosa.util.normalize(chroma, axis=0)

        logger.info(f"Computed chroma: shape {chroma.shape}")
        return chroma

    except Exception as e:
        logger.error(f"Chroma computation failed: {e}")
        raise


def estimate_harmonic_rhythm(
    chroma: np.ndarray,
    beats: np.ndarray,
    tempo: float
) -> float:
    """
    Estimate average chord duration in beats.

    Args:
        chroma: Chromagram
        beats: Beat frames
        tempo: Tempo in BPM

    Returns:
        Average beats per chord change
    """
    if chroma.shape[1] != len(beats):
        # If not beat-synced, this is approximate
        logger.warning("Chroma not beat-synced for harmonic rhythm estimation")
        return 1.0

    # Detect chord changes by looking at chroma difference
    chroma_diff = np.diff(chroma, axis=1)
    change_magnitude = np.linalg.norm(chroma_diff, axis=0)

    # Threshold for detecting significant changes
    threshold = np.median(change_magnitude) + np.std(change_magnitude)
    changes = change_magnitude > threshold

    if np.sum(changes) == 0:
        return 1.0  # Default to 1 beat

    # Average beats between changes
    change_positions = np.where(changes)[0]
    if len(change_positions) < 2:
        return 1.0

    avg_beats_per_chord = np.mean(np.diff(change_positions))
    return float(avg_beats_per_chord)


def get_chord_functions_distribution(roman_numerals: list[str]) -> dict:
    """
    Get distribution of chord functions.

    Args:
        roman_numerals: List of Roman numeral chord labels

    Returns:
        Dictionary of function: count
    """
    function_counts = {}
    for rn in roman_numerals:
        # Extract base roman numeral (ignore quality markers)
        base = ''.join(c for c in rn if c.upper() in 'IVXLCDM')
        if not base:
            continue
        function_counts[base] = function_counts.get(base, 0) + 1

    return function_counts
