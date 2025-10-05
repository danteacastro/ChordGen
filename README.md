# ChordGen - AI-Powered Chord Progression Generator

Generate chord progressions by analyzing music from SoundCloud, YouTube, or local files, with live MIDI output to Ableton and effects suggestions.

## Features

- 🎵 **Audio Analysis**: Analyze tracks from SoundCloud, YouTube, or local files
- 🎹 **Chord Detection**: Extract chord progressions using chromagram analysis and HMM
- 🎨 **Style Learning**: Detect key, tempo, mode, and harmonic patterns
- ✨ **Generation**: Create new progressions in similar style using Markov chains
- 🎛️ **MIDI Output**: Send live to Ableton via virtual MIDI port or export MIDI files
- 🔊 **Effects Suggestions**: Get Ableton device chain recommendations per track

## Installation

### Using Poetry (Recommended)

```bash
# Install Poetry if needed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
cd ChordGen
poetry install

# Run the app
poetry run streamlit run app.py
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## Virtual MIDI Setup

### Linux (ALSA)
```bash
# Load virtual MIDI kernel module
sudo modprobe snd-virmidi

# Check available ports
aconnect -l

# Connect ChordGen to Ableton
aconnect [ChordGen_port] [Ableton_port]
```

### macOS (IAC Driver)
1. Open **Audio MIDI Setup** (in Applications/Utilities)
2. Window → Show MIDI Studio
3. Double-click **IAC Driver**
4. Check "Device is online"
5. Add a port named "ChordGen"

### Windows (loopMIDI)
1. Download and install [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
2. Run loopMIDI
3. Click "+" to create a new port named "ChordGen"
4. Leave loopMIDI running

## Quick Start

1. **Launch the app:**
   ```bash
   streamlit run app.py
   ```

2. **Input audio:**
   - Paste a SoundCloud or YouTube URL, OR
   - Upload a local WAV/MP3 file

3. **Configure options:**
   - Bars: 4-8
   - Complexity: Basic triads / Extended 7ths
   - Style: Auto-detect or choose
   - Tempo: Follow detected or manual

4. **Analyze:**
   - Click "Analyze" to detect key, tempo, and chords

5. **Generate:**
   - Click "Generate" to create a new progression

6. **Output:**
   - **Play to MIDI**: Send live to selected virtual port
   - **Export MIDI**: Save 3-track MIDI file (Chords, Bass, Pad)

7. **Effects:**
   - View recommended Ableton device chains for each track
   - Copy settings and apply in Ableton

## Architecture

```
ChordGen/
├── app.py                 # Streamlit UI (main entry point)
├── chordgen/
│   ├── audio_io.py        # Audio download/loading
│   ├── analysis.py        # Tempo, key, chroma, segmentation
│   ├── chords.py          # Chord templates, HMM, romanization
│   ├── generate.py        # Markov generation + style model
│   ├── midi_out.py        # Live MIDI + file export
│   ├── effects.py         # Effects recommender
│   ├── config.py          # Settings models
│   └── utils.py           # Helpers, logging
├── presets/
│   ├── styles.yaml        # Genre/style defaults
│   └── effects.yaml       # Device chains per style
└── examples/
    └── test_local.wav     # Test audio file
```

## Usage Examples

### Analyze Local File
```python
from chordgen import audio_io, analysis, chords

# Load audio
audio, sr = audio_io.load_audio("examples/test_local.wav")

# Analyze
tempo, beats = analysis.detect_tempo_beats(audio, sr)
key, mode = analysis.detect_key(audio, sr)
chroma = analysis.compute_chroma(audio, sr, beats)

# Detect chords
detector = chords.ChordDetector()
detected_chords = detector.detect(chroma, key, mode)
```

### Generate Progression
```python
from chordgen import generate

# Create style profile from analysis
profile = generate.StyleProfile(
    key="C", mode="major", tempo=120,
    harmonic_rhythm=1.0, chord_functions=["I", "IV", "V", "vi"]
)

# Generate new progression
generator = generate.ProgressionGenerator(profile)
progression = generator.generate(bars=8, complexity=1)
```

### Send to Ableton
```python
from chordgen import midi_out

# List available ports
ports = midi_out.list_ports()

# Send live MIDI
sender = midi_out.MIDISender(port_name="ChordGen")
sender.send_progression(progression, tempo=120)

# Export MIDI file
midi_out.export_midi(progression, "output.mid", tempo=120)
```

## Ableton Setup

1. **Enable MIDI Input:**
   - Preferences → Link/Tempo/MIDI
   - MIDI Ports → Track: ON for your virtual port
   - Remote: ON (optional)

2. **Create MIDI Track:**
   - Insert → MIDI Track
   - MIDI From: [Your Virtual Port]
   - Monitor: In

3. **Load Instrument:**
   - Drag instrument (Wavetable, Electric, Analog, etc.)
   - Arm track for recording

4. **Apply Effects:**
   - Copy suggested device chain from ChordGen
   - Add devices in order
   - Adjust parameters as suggested

## Effects Suggestions

ChordGen suggests Ableton stock device chains for:
- **Chords Track**: EQ, Chorus, Compression, Reverb
- **Bass Track**: EQ, Saturation, Glue Compressor
- **Pad/Lead Track**: Auto Filter, Delay, Reverb

Styles supported:
- Neo-Soul / Jazz
- Indie / Synth-Pop
- Lo-Fi / Bedroom
- House / Disco
- Ambient

## Development

### Run Tests
```bash
poetry run pytest tests/
```

### Type Checking
```bash
poetry run mypy chordgen/
```

### Format Code
```bash
poetry run black chordgen/
```

## Troubleshooting

### "No MIDI ports found"
- Verify virtual MIDI port is created and running
- Check OS-specific setup instructions above
- Restart ChordGen after creating virtual port

### "Failed to download audio"
- Check internet connection
- Verify URL is accessible
- Try using local file instead
- Some SoundCloud tracks may be restricted

### "Chord detection not accurate"
- Try different audio source (cleaner recording)
- Adjust complexity setting
- Manual key override in analysis step

### "Ableton not receiving MIDI"
- Verify MIDI track is armed and monitoring
- Check Ableton MIDI preferences
- Ensure virtual port is connected
- Try different virtual port

## License

MIT License - See LICENSE file

## Credits

- Built with librosa, mido, streamlit
- Chord detection inspired by music information retrieval research
- Effects suggestions based on common production techniques
