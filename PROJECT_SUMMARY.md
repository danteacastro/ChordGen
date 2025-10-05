# ChordGen - Project Summary

## Overview

**ChordGen** is an AI-powered chord progression generator that analyzes music from various sources (YouTube, SoundCloud, local files), detects chord progressions using signal processing and Hidden Markov Models, and generates new progressions in similar styles. It outputs MIDI live to Ableton Live and suggests Ableton effects chains.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI (app.py)                │
│  - File upload / URL input                              │
│  - Analysis controls                                     │
│  - Generation parameters                                 │
│  - MIDI output controls                                  │
│  - Effects display                                       │
└────────────────┬────────────────────────────────────────┘
                 │
    ┌────────────┴───────────────┐
    │                            │
    ▼                            ▼
┌─────────┐                 ┌────────────┐
│audio_io │                 │  analysis  │
│         │                 │            │
│ - Load  │────────────────▶│ - Tempo    │
│ - Download                │ - Key      │
│ - Stream│                 │ - Chroma   │
└─────────┘                 │ - Beats    │
                            └──────┬─────┘
                                   │
                                   ▼
                            ┌────────────┐
                            │   chords   │
                            │            │
                            │ - Templates│
                            │ - HMM      │
                            │ - Viterbi  │
                            │ - Roman    │
                            └──────┬─────┘
                                   │
                                   ▼
                            ┌────────────┐
                            │  generate  │
                            │            │
                            │ - Profile  │
                            │ - Markov   │
                            │ - Cadences │
                            └──────┬─────┘
                                   │
                      ┌────────────┴───────────┐
                      │                        │
                      ▼                        ▼
               ┌────────────┐           ┌──────────┐
               │  midi_out  │           │ effects  │
               │            │           │          │
               │ - Live     │           │ - Chains │
               │ - Export   │           │ - Presets│
               │ - 3 tracks │           │ - Styles │
               └────────────┘           └──────────┘
```

## Core Modules

### 1. audio_io.py
- **Purpose**: Audio loading and downloading
- **Key Functions**:
  - `load_audio()`: Load WAV/MP3/FLAC/etc.
  - `download_audio()`: Download from YouTube/SoundCloud using yt-dlp
  - `load_or_download()`: Unified interface
- **Dependencies**: librosa, soundfile, yt-dlp

### 2. analysis.py
- **Purpose**: Audio analysis and feature extraction
- **Key Functions**:
  - `detect_tempo_beats()`: Tempo detection and beat tracking
  - `detect_key()`: Key detection using Krumhansl-Schmuckler profiles
  - `compute_chroma()`: Beat-synchronized chromagram
  - `estimate_harmonic_rhythm()`: Chord change rate
- **Algorithm**: CQT chromagram + Pearson correlation with key profiles
- **Dependencies**: librosa, scipy

### 3. chords.py
- **Purpose**: Chord detection and recognition
- **Key Classes**:
  - `ChordHMM`: Hidden Markov Model for chord sequence smoothing
  - `ChordDetector`: Main detection class
  - `Chord`: Data class for chord representation
- **Algorithm**:
  1. Create chord templates (12-note vectors for each chord type)
  2. Compute emission probabilities (cosine similarity)
  3. Build transition matrix from music theory rules
  4. Viterbi algorithm to find most likely sequence
  5. Romanize relative to detected key
- **Supported Chords**: maj, min, dim, aug, maj7, min7, dom7
- **Dependencies**: numpy

### 4. generate.py
- **Purpose**: Generate new chord progressions
- **Key Classes**:
  - `StyleProfile`: Musical style representation
  - `ProgressionGenerator`: Markov-based generator
- **Algorithm**:
  1. Build first-order Markov model from functional harmony rules
  2. Generate sequence using weighted random selection
  3. Ensure proper cadences (V-I, ii-V-I, etc.)
  4. Convert Roman numerals to concrete chords
  5. Distribute timing across bars
- **Features**:
  - Complexity levels (0=triads, 1=7ths, 2=extensions)
  - Cadence enforcement
  - Style-aware transitions
- **Dependencies**: numpy

### 5. midi_out.py
- **Purpose**: MIDI output (live and file export)
- **Key Classes**:
  - `MIDISender`: Real-time MIDI output
- **Key Functions**:
  - `send_progression()`: Play chords live
  - `export_midi()`: Export 3-track MIDI file (Chords, Bass, Pad)
- **Features**:
  - Virtual MIDI port support (ALSA, IAC, loopMIDI)
  - Multi-track export
  - Tempo-synced playback
- **Dependencies**: mido, python-rtmidi

### 6. effects.py
- **Purpose**: Ableton effects chain recommendations
- **Key Classes**:
  - `EffectsRecommender`: Style-based effects suggester
- **Presets**:
  - Indie / Synth-Pop
  - Neo-Soul / Jazz
  - Lo-Fi / Bedroom
  - House / Disco
  - Ambient
- **Output**: Device chains with parameters for 3 tracks
- **Dependencies**: pyyaml

### 7. config.py
- **Purpose**: Configuration management
- **Models**: Pydantic settings for audio, analysis, generation, MIDI
- **Features**: YAML loading, directory initialization

### 8. utils.py
- **Purpose**: Helper functions
- **Functions**:
  - `note_name_to_number()`: MIDI conversion
  - `chord_to_midi_notes()`: Chord to note list
  - `timing_decorator`: Performance logging
  - `SimpleCache`: File-based caching

## Data Flow

1. **Input**: User provides URL or file
2. **Download/Load**: `audio_io` gets audio data
3. **Analysis**: `analysis` extracts tempo, key, chroma
4. **Chord Detection**: `chords` uses HMM to find progression
5. **Style Profiling**: `generate` creates style model
6. **Generation**: `generate` creates new progression
7. **Output**:
   - `midi_out` sends to Ableton or exports file
   - `effects` suggests device chains

## Key Algorithms

### Chord Detection HMM

**States**: All possible chord labels (36-72 depending on complexity)

**Observations**: Chromagram frames (12-dimensional vectors)

**Emission Probabilities**:
```python
P(chroma_frame | chord) = cosine_similarity(chroma_frame, chord_template)
```

**Transition Probabilities**: Based on functional harmony:
- I → IV, V, vi (common)
- ii → V (very common)
- V → I (strong cadence)
- etc.

**Inference**: Viterbi algorithm finds most likely path

### Key Detection

**Algorithm**: Krumhansl-Schmuckler

1. Compute pitch class distribution from chromagram
2. Correlate with major/minor profiles at all 12 transpositions
3. Choose key with highest correlation

**Profiles**: Empirically derived weightings for each scale degree

### Progression Generation

**Model**: First-order Markov chain with music theory constraints

**States**: Roman numerals (I, ii, iii, IV, V, vi, vii°)

**Transitions**: Weighted by common progressions:
- High probability: functional moves (ii→V, V→I)
- Medium probability: common alternatives (I→vi, vi→IV)
- Low probability: rare but valid moves

**Cadence Enforcement**: Last 1-3 chords replaced with authentic/plagal cadence

## Performance

- **Analysis Time**: 10-30 seconds (depends on audio length)
- **Generation Time**: < 1 second
- **MIDI Export**: < 1 second
- **Memory**: ~200-500 MB during analysis

## Testing

Run tests:
```bash
python tests/test_basic.py
```

Tests cover:
- Note conversions
- Chord template creation
- Progression generation
- Markov model validity
- Romanization

## Limitations & Future Work

### Current Limitations

1. **Chord Detection Accuracy**: ~70-80% on clean recordings
   - Struggles with dense/distorted audio
   - Better on solo piano/guitar

2. **Key Detection**: Works well for tonal music
   - Fails on atonal/chromatic music
   - No mode mixture detection

3. **Style Learning**: Basic heuristics
   - Could use ML for better style modeling
   - Limited to 5 preset styles

4. **MIDI Playback**: Blocking (freezes UI)
   - Should use threading
   - No real-time control

### Future Enhancements

**Audio Analysis**:
- [ ] Deep learning chord recognition (Chordino, CREMA)
- [ ] Mode mixture detection (borrowed chords)
- [ ] Rhythm/groove extraction
- [ ] Multi-instrument separation

**Generation**:
- [ ] Higher-order Markov models
- [ ] LSTM/Transformer for progression generation
- [ ] Voice leading optimization
- [ ] Melody generation

**MIDI**:
- [ ] Real-time control (start/stop/loop)
- [ ] Velocity variation
- [ ] Humanization
- [ ] Ableton Link sync

**Effects**:
- [ ] Parameter automation
- [ ] Max4Live integration
- [ ] Custom device creation
- [ ] Genre classification

**UI**:
- [ ] Waveform visualization
- [ ] Chord diagram display
- [ ] Piano roll view
- [ ] Real-time analysis

## File Structure

```
ChordGen/
├── app.py                      # Streamlit UI (MAIN ENTRY)
├── chordgen/
│   ├── __init__.py
│   ├── audio_io.py             # Audio loading (226 lines)
│   ├── analysis.py             # Analysis (220 lines)
│   ├── chords.py               # Chord detection (415 lines)
│   ├── generate.py             # Generation (310 lines)
│   ├── midi_out.py             # MIDI output (240 lines)
│   ├── effects.py              # Effects suggestions (230 lines)
│   ├── config.py               # Configuration (80 lines)
│   └── utils.py                # Utilities (150 lines)
├── presets/
│   ├── styles.yaml             # Style presets
│   └── effects.yaml            # Effects presets
├── tests/
│   └── test_basic.py           # Unit tests
├── examples/                   # Example audio (add your own)
├── logs/                       # Application logs
├── exports/                    # MIDI exports
├── .cache/                     # Downloaded audio cache
├── pyproject.toml              # Poetry dependencies
├── requirements.txt            # Pip dependencies
├── README.md                   # Main documentation
├── QUICKSTART.md               # Quick start guide
└── PROJECT_SUMMARY.md          # This file
```

**Total Lines of Code**: ~1,900 lines (excluding tests/docs)

## Dependencies

**Core**:
- Python 3.9+
- NumPy, SciPy (numerical computing)
- librosa (audio analysis)
- soundfile (audio I/O)

**MIDI**:
- mido (MIDI file handling)
- python-rtmidi (real-time MIDI)

**UI**:
- Streamlit (web interface)

**Download**:
- yt-dlp (YouTube/SoundCloud)

**Config**:
- PyYAML (presets)
- Pydantic (settings)

## Credits

**Algorithms**:
- Krumhansl-Schmuckler key detection
- Hidden Markov Model chord recognition
- Functional harmony theory

**Libraries**:
- librosa (audio analysis)
- mido (MIDI)
- Streamlit (UI)

**Built by**: Dante Castro
**Date**: October 2025
**License**: MIT

## Getting Started

See [QUICKSTART.md](QUICKSTART.md) for installation and usage instructions.

## Support

For issues, questions, or feature requests, check:
- `logs/app.log` for errors
- README.md for detailed documentation
- Code comments for implementation details
