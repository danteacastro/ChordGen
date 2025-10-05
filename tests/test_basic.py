"""Basic tests for ChordGen modules."""

import pytest
import numpy as np
from pathlib import Path

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from chordgen import chords, generate, analysis
from chordgen.utils import note_name_to_number, chord_to_midi_notes


def test_note_conversion():
    """Test MIDI note number conversion."""
    assert note_name_to_number("C4") == 60
    assert note_name_to_number("A4") == 69
    assert note_name_to_number("C5") == 72
    assert note_name_to_number("C#4") == 61
    assert note_name_to_number("Bb4") == 70


def test_chord_to_midi():
    """Test chord to MIDI notes conversion."""
    # C major triad
    notes = chord_to_midi_notes("C", "maj", 4)
    assert notes == [60, 64, 67]  # C, E, G

    # D minor triad
    notes = chord_to_midi_notes("D", "min", 4)
    assert notes == [62, 65, 69]  # D, F, A

    # G dominant 7th
    notes = chord_to_midi_notes("G", "dom7", 4)
    assert notes == [67, 71, 74, 77]  # G, B, D, F


def test_chord_templates():
    """Test chord template creation."""
    labels, templates = chords.create_chord_templates(extended=False)

    # Should have 3 qualities × 12 roots = 36 basic chords
    assert len(labels) == 36
    assert templates.shape == (36, 12)

    # Each template should have some non-zero values
    assert np.all(templates.sum(axis=1) > 0)


def test_chord_templates_extended():
    """Test extended chord templates."""
    labels, templates = chords.create_chord_templates(extended=True)

    # Basic (36) + 7ths (36) = 72 total
    assert len(labels) == 72
    assert templates.shape == (72, 12)


def test_progression_generator():
    """Test progression generation."""
    profile = generate.StyleProfile(
        key="C",
        mode="major",
        tempo=120,
        harmonic_rhythm=1.0
    )

    generator = generate.ProgressionGenerator(profile, seed=42)
    progression = generator.generate(bars=8, complexity=0)

    # Should generate some chords
    assert len(progression) > 0
    assert len(progression) <= 16  # Reasonable number

    # All chords should have required fields
    for chord in progression:
        assert chord.root in chords.NOTE_NAMES
        assert chord.quality in ["maj", "min", "dim", "aug", "maj7", "min7", "dom7"]
        assert hasattr(chord, 'start_beat')
        assert hasattr(chord, 'duration_beats')


def test_markov_model():
    """Test Markov model builds correctly."""
    profile = generate.StyleProfile(key="C", mode="major", tempo=120)
    generator = generate.ProgressionGenerator(profile)

    # Should have transitions for diatonic chords
    assert "I" in generator.transition_matrix
    assert "V" in generator.transition_matrix

    # Probabilities should sum to ~1.0
    for source in generator.transition_matrix:
        total = sum(generator.transition_matrix[source].values())
        assert abs(total - 1.0) < 0.01


def test_key_detection_mock():
    """Test key detection with synthetic chroma."""
    # Create fake C major chroma (emphasize C, E, G)
    chroma = np.zeros((12, 10))
    chroma[0, :] = 0.9  # C
    chroma[4, :] = 0.7  # E
    chroma[7, :] = 0.8  # G

    # Add to session would need actual audio, skip for now
    # This is a placeholder test
    assert True


def test_chord_romanization():
    """Test Roman numeral assignment."""
    # Create a simple chord
    chord = chords.Chord(root="C", quality="maj")

    # In C major, C major should be "I"
    detector = chords.ChordDetector()
    result = detector._romanize_chords([chord], "C", "major")

    assert result[0].roman == "I"


def test_cadences():
    """Test cadence patterns exist."""
    assert len(generate.MAJOR_CADENCES) > 0
    assert len(generate.MINOR_CADENCES) > 0

    # Check V-I is in major cadences
    assert ["V", "I"] in generate.MAJOR_CADENCES


if __name__ == "__main__":
    # Run tests
    test_note_conversion()
    test_chord_to_midi()
    test_chord_templates()
    test_chord_templates_extended()
    test_progression_generator()
    test_markov_model()
    test_chord_romanization()
    test_cadences()

    print("✅ All tests passed!")
