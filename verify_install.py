#!/usr/bin/env python3
"""
Verification script to check ChordGen installation and setup.
Run this after installing dependencies to verify everything works.
"""

import sys
from pathlib import Path

print("🎹 ChordGen Installation Verification")
print("=" * 50)

# Check Python version
print("\n1. Checking Python version...")
if sys.version_info < (3, 9):
    print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} found")
    print(f"   ⚠️  Python 3.9+ required")
    sys.exit(1)
else:
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# Check dependencies
print("\n2. Checking dependencies...")
missing = []

deps = {
    "streamlit": "Streamlit",
    "librosa": "librosa",
    "soundfile": "soundfile",
    "mido": "mido",
    "rtmidi": "python-rtmidi",
    "yaml": "PyYAML",
    "pydantic": "Pydantic",
    "yt_dlp": "yt-dlp",
    "numpy": "NumPy",
    "scipy": "SciPy",
}

for module, name in deps.items():
    try:
        __import__(module)
        print(f"   ✅ {name}")
    except ImportError:
        print(f"   ❌ {name} - NOT INSTALLED")
        missing.append(name)

if missing:
    print(f"\n   ⚠️  Missing dependencies: {', '.join(missing)}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Check ChordGen modules
print("\n3. Checking ChordGen modules...")
try:
    from chordgen import audio_io, analysis, chords, generate, midi_out, effects, config, utils
    print("   ✅ All modules importable")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Check directories
print("\n4. Checking directories...")
from chordgen.config import init_directories, settings

init_directories()
dirs = {
    "Cache": settings.cache_dir,
    "Exports": settings.export_dir,
    "Logs": Path("logs"),
    "Presets": Path("presets"),
}

for name, path in dirs.items():
    if path.exists():
        print(f"   ✅ {name}: {path}")
    else:
        print(f"   ❌ {name}: {path} - NOT FOUND")

# Check MIDI ports
print("\n5. Checking MIDI ports...")
try:
    from chordgen.midi_out import list_ports
    ports = list_ports()
    if ports:
        print(f"   ✅ Found {len(ports)} MIDI port(s):")
        for port in ports:
            print(f"      - {port}")
    else:
        print("   ⚠️  No MIDI ports found")
        print("      Set up virtual MIDI port:")
        print("      - Linux: sudo modprobe snd-virmidi")
        print("      - macOS: Enable IAC Driver in Audio MIDI Setup")
        print("      - Windows: Install and run loopMIDI")
except Exception as e:
    print(f"   ❌ MIDI error: {e}")

# Test basic functionality
print("\n6. Testing basic functionality...")

try:
    # Test note conversion
    from chordgen.utils import note_name_to_number, chord_to_midi_notes
    assert note_name_to_number("C4") == 60
    assert chord_to_midi_notes("C", "maj", 4) == [60, 64, 67]
    print("   ✅ Note conversion works")
except AssertionError:
    print("   ❌ Note conversion failed")

try:
    # Test chord templates
    from chordgen.chords import create_chord_templates
    labels, templates = create_chord_templates()
    assert len(labels) == 36
    print("   ✅ Chord templates work")
except Exception as e:
    print(f"   ❌ Chord templates failed: {e}")

try:
    # Test progression generation
    from chordgen.generate import StyleProfile, ProgressionGenerator
    profile = StyleProfile(key="C", mode="major", tempo=120)
    generator = ProgressionGenerator(profile, seed=42)
    progression = generator.generate(bars=4)
    assert len(progression) > 0
    print(f"   ✅ Progression generation works ({len(progression)} chords)")
except Exception as e:
    print(f"   ❌ Generation failed: {e}")

try:
    # Test effects recommender
    from chordgen.effects import EffectsRecommender
    recommender = EffectsRecommender()
    recs = recommender.recommend(style="Indie / Synth-Pop", tempo=120)
    assert "tracks" in recs
    print("   ✅ Effects recommender works")
except Exception as e:
    print(f"   ❌ Effects recommender failed: {e}")

# Summary
print("\n" + "=" * 50)
print("✅ Installation verification complete!")
print("\nNext steps:")
print("1. Set up virtual MIDI port (if not detected)")
print("2. Run: streamlit run app.py")
print("3. Upload audio or paste URL")
print("4. Analyze, generate, and export!")
print("\nSee QUICKSTART.md for detailed instructions.")
