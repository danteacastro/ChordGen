#!/usr/bin/env python3
"""
Test ChordGen with second YouTube video
URL: https://www.youtube.com/watch?v=ZYMgj2gBbMA
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from chordgen import audio_io, analysis, chords, generate
from chordgen.jazz_theory import JazzTheory, JazzScale
from chordgen.utils import setup_logging

setup_logging()

print("=" * 70)
print("ChordGen - Analyzing New YouTube Video")
print("=" * 70)
print("URL: https://www.youtube.com/watch?v=ZYMgj2gBbMA")
print("=" * 70)
print()

# Download and analyze
print("📥 Downloading audio...")
url = "https://www.youtube.com/watch?v=ZYMgj2gBbMA"

try:
    audio, sr = audio_io.load_or_download(url)
    print(f"✅ Downloaded! Duration: {len(audio)/sr:.1f}s, SR: {sr}Hz")
    print()

    # Analyze
    print("🔍 Analyzing...")
    tempo, beats = analysis.detect_tempo_beats(audio, sr)
    key, mode = analysis.detect_key(audio, sr)
    chroma = analysis.compute_chroma(audio, sr, beats)

    print(f"🥁 Tempo: {tempo:.1f} BPM")
    print(f"🎵 Key: {key} {mode}")
    print(f"📊 Chromagram: {chroma.shape}")
    print()

    # Detect chords
    print("🎹 Detecting chords...")
    detector = chords.ChordDetector(extended=True)
    detected_chords = detector.detect(chroma, key, mode)

    print(f"Found {len(detected_chords)} chords")
    print()
    print("First 12 chords:")
    for i, chord in enumerate(detected_chords[:12], 1):
        print(f"  {i}. {chord.root}{chord.quality} ({chord.roman})")
    print()

    # Generate new progression
    print("✨ Generating AI progression...")
    style_profile = generate.create_style_profile_from_analysis(
        key, mode, tempo, detected_chords
    )

    generator = generate.ProgressionGenerator(style_profile)
    progression = generator.generate(bars=8, complexity=1)

    print(f"Generated {len(progression)} chord progression:")
    for i, chord in enumerate(progression, 1):
        print(f"  Bar {i}: {chord.root}{chord.quality} ({chord.roman})")
    print()

    # Jazz analysis of first 3 chords
    print("=" * 70)
    print("🎼 JAZZ THEORY ANALYSIS")
    print("=" * 70)
    print()

    for i, chord in enumerate(progression[:3], 1):
        structure = JazzTheory.analyze_chord(chord.root, chord.quality)

        print(f"Chord {i}: {chord.root}{chord.quality}")
        print(f"  Formula: {JazzTheory.get_chord_formula(chord.quality)}")
        print(f"  Notes: {' - '.join(structure.notes)}")
        print(f"  Recommended Scale: {structure.recommended_scale.name.replace('_', ' ').title()}")

        scale_notes = JazzTheory.get_scale_note_names(chord.root, structure.recommended_scale)
        print(f"  Scale Notes: {' - '.join(scale_notes)}")

        if structure.tensions:
            print(f"  Tensions: {', '.join(structure.tensions)}")
        if structure.avoid_notes:
            print(f"  Avoid: {', '.join(structure.avoid_notes)}")
        print()

    # Show comparison
    print("=" * 70)
    print("📊 COMPARISON WITH FIRST VIDEO")
    print("=" * 70)
    print()
    print("Video 1 (t_4Nh4H95Nc):")
    print("  - Key: C major")
    print("  - Tempo: 120 BPM")
    print("  - Style: Pop/Indie (vi-V-IV progression)")
    print("  - Chords: Am7, G7, Fmaj7...")
    print()
    print("Video 2 (ZYMgj2gBbMA):")
    print(f"  - Key: {key} {mode}")
    print(f"  - Tempo: {tempo:.1f} BPM")
    print(f"  - Detected {len(detected_chords)} unique chords")
    print()

    # Show what you can do
    print("=" * 70)
    print("🎯 WHAT YOU CAN DO WITH THIS")
    print("=" * 70)
    print()
    print("In ChordGen GUI (streamlit run app.py):")
    print()
    print("1. CHORD GENERATOR PAGE:")
    print("   - Paste this URL")
    print("   - Click Analyze → See detected chords")
    print("   - Click Generate → Get AI progression in same style")
    print()
    print("2. JAZZ EDITOR PAGE:")
    print("   - View each chord's recommended scale")
    print("   - See available tensions (9, 11, 13)")
    print("   - Try different voicings (Drop-2, Rootless)")
    print("   - Edit chords manually")
    print()
    print("3. ARPEGGIATOR PAGE:")
    print("   - Choose pattern (Up, Down, Random)")
    print("   - Set rate (1/16 for fast, 1/8 for medium)")
    print("   - Adjust octaves and swing")
    print("   - Play arpeggiated version")
    print()
    print("4. LIVE PAGE:")
    print("   - Enable 'Sync to Ableton'")
    print("   - ChordGen follows Ableton's tempo")
    print("   - Send MIDI to your synth in real-time")
    print()
    print("5. PATTERNS PAGE:")
    print("   - Save this progression")
    print("   - Load it later")
    print("   - Export as MIDI file")
    print()
    print("=" * 70)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
