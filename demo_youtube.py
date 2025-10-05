#!/usr/bin/env python3
"""
Demo: Analyze YouTube video and show ChordGen capabilities
YouTube: https://www.youtube.com/watch?v=t_4Nh4H95Nc
"""

import sys
from pathlib import Path

# Add chordgen to path
sys.path.insert(0, str(Path(__file__).parent))

from chordgen import audio_io, analysis, chords, generate
from chordgen.jazz_theory import JazzTheory, JazzScale, ChordVoicing
from chordgen.utils import setup_logging

# Setup logging
setup_logging()

print("=" * 70)
print("ChordGen - YouTube Analysis Demo")
print("=" * 70)
print(f"Video: https://www.youtube.com/watch?v=t_4Nh4H95Nc")
print("=" * 70)
print()

# Step 1: Download and load audio
print("📥 STEP 1: Downloading audio from YouTube...")
print("-" * 70)

url = "https://www.youtube.com/watch?v=t_4Nh4H95Nc"

try:
    audio, sr = audio_io.load_or_download(url)
    print(f"✅ Downloaded! Sample rate: {sr} Hz, Duration: {len(audio)/sr:.1f}s")
except Exception as e:
    print(f"❌ Download failed: {e}")
    print("Note: Make sure yt-dlp is installed: pip install yt-dlp")
    sys.exit(1)

print()

# Step 2: Analyze audio
print("🔍 STEP 2: Analyzing audio (tempo, key, chords)...")
print("-" * 70)

# Detect tempo
tempo, beats = analysis.detect_tempo_beats(audio, sr)
print(f"🥁 Tempo: {tempo:.1f} BPM")

# Detect key
key, mode = analysis.detect_key(audio, sr)
print(f"🎵 Key: {key} {mode}")

# Compute chroma
chroma = analysis.compute_chroma(audio, sr, beats)
print(f"📊 Chromagram shape: {chroma.shape}")

# Detect chords
detector = chords.ChordDetector(extended=True)
detected_chords = detector.detect(chroma, key, mode)

print(f"🎹 Detected {len(detected_chords)} chords")
print(f"First 8 chords: {' → '.join([str(c) for c in detected_chords[:8]])}")

print()

# Step 3: Generate new progression
print("✨ STEP 3: Generating new AI progression...")
print("-" * 70)

# Create style profile
style_profile = generate.create_style_profile_from_analysis(
    key, mode, tempo, detected_chords
)

print(f"Style profile created:")
print(f"  - Key: {style_profile.key} {style_profile.mode}")
print(f"  - Tempo: {style_profile.tempo:.1f} BPM")
print(f"  - Common progressions learned: {len(style_profile.progressions)}")

# Generate progression
generator = generate.ProgressionGenerator(style_profile)
progression = generator.generate(bars=8, complexity=1)

print(f"\n🎲 Generated progression ({len(progression)} chords):")
for i, chord in enumerate(progression, 1):
    print(f"  {i}. {chord.root}{chord.quality} ({chord.roman})")

print()

# Step 4: Jazz analysis
print("🎼 STEP 4: Jazz theory analysis...")
print("-" * 70)

print("\nDetailed analysis of first 4 chords:\n")

for i, chord in enumerate(progression[:4], 1):
    structure = JazzTheory.analyze_chord(chord.root, chord.quality)

    print(f"Chord {i}: {chord.root}{chord.quality}")
    print(f"  Formula: {JazzTheory.get_chord_formula(chord.quality)}")
    print(f"  Notes: {' - '.join(structure.notes)}")
    print(f"  Scale Degrees: {' - '.join(structure.scale_degrees)}")
    print(f"  Recommended Scale: {structure.recommended_scale.name.replace('_', ' ')}")

    if structure.tensions:
        print(f"  Available Tensions: {', '.join(structure.tensions)}")
    if structure.avoid_notes:
        print(f"  Avoid: {', '.join(structure.avoid_notes)}")

    print()

# Step 5: Show scale
print("🎵 STEP 5: Scale visualization...")
print("-" * 70)

first_chord = progression[0]
structure = JazzTheory.analyze_chord(first_chord.root, first_chord.quality)
scale = structure.recommended_scale

print(f"\nScale for {first_chord.root}{first_chord.quality}:")
print(f"  {scale.name.replace('_', ' ').title()}")

scale_notes = JazzTheory.get_scale_note_names(first_chord.root, scale)
print(f"  Notes: {' - '.join(scale_notes)}")

# Show scale degrees
print("\n  Scale Degrees:")
for i, interval in enumerate(scale.value):
    degree = JazzTheory._get_scale_degrees([interval])[0]
    print(f"    {degree}: {scale_notes[i]}")

print()

# Step 6: Voicing examples
print("🎹 STEP 6: Chord voicing examples...")
print("-" * 70)

first_chord_structure = JazzTheory.analyze_chord(progression[0].root, progression[0].quality)

voicings = [
    ("Root Position", ChordVoicing.ROOT_POSITION),
    ("Drop-2", ChordVoicing.DROP_2),
    ("Rootless A", ChordVoicing.ROOTLESS_A),
    ("Shell", ChordVoicing.SHELL),
]

print(f"\nVoicings for {progression[0].root}{progression[0].quality}:\n")

for name, voicing in voicings:
    voiced_notes = JazzTheory.apply_voicing(first_chord_structure.midi_notes, voicing)

    # Convert to note names
    note_names = []
    for note in voiced_notes:
        note_name = JazzTheory.NOTE_NAMES[note % 12]
        octave = (note // 12) - 1
        note_names.append(f"{note_name}{octave}")

    print(f"  {name:15s}: {' - '.join(note_names)}")

print()

# Step 7: Summary
print("=" * 70)
print("📊 SUMMARY - What ChordGen Can Do:")
print("=" * 70)
print()
print("✅ Audio Analysis:")
print(f"   - Detected tempo: {tempo:.1f} BPM")
print(f"   - Detected key: {key} {mode}")
print(f"   - Analyzed {len(detected_chords)} chords from audio")
print()
print("✅ AI Generation:")
print(f"   - Learned style from input track")
print(f"   - Generated {len(progression)} new chords")
print(f"   - Maintains key and harmonic structure")
print()
print("✅ Jazz Theory:")
print(f"   - Chord formulas and scale degrees")
print(f"   - 20+ scale recommendations")
print(f"   - Tension analysis (9, 11, 13)")
print(f"   - Professional voicings (Drop-2, Rootless, etc.)")
print()
print("✅ MIDI Output:")
print(f"   - Real-time playback to Ableton")
print(f"   - Sync to Ableton's tempo (MIDI clock)")
print(f"   - Arpeggiator with 7 patterns")
print(f"   - 16-step sequencer")
print()
print("🚀 Next Steps:")
print("   1. Run the Streamlit app: streamlit run app.py")
print("   2. Go to Chord Generator → paste YouTube URL")
print("   3. Click Analyze → Generate")
print("   4. Explore Jazz Editor for scale analysis")
print("   5. Use Live page to sync with Ableton")
print()
print("=" * 70)
