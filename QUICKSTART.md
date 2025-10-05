# ChordGen - Quick Start Guide

## Installation

### 1. Install Dependencies

```bash
cd /home/dante/Documents/Projects/ChordGen

# Option A: Using pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Option B: Using poetry (recommended)
poetry install
```

### 2. Set Up Virtual MIDI Port

**Linux (ALSA):**
```bash
# Load virtual MIDI module
sudo modprobe snd-virmidi

# Check available ports
aconnect -l

# You should see virtual MIDI ports (e.g., VirMIDI 0-0, 0-1, etc.)
```

**macOS:**
1. Open **Audio MIDI Setup** (/Applications/Utilities)
2. Window → Show MIDI Studio
3. Double-click **IAC Driver**
4. Check "Device is online"
5. Add port named "ChordGen"

**Windows:**
1. Download [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html)
2. Install and run
3. Click "+" to create port named "ChordGen"
4. Leave running

## Usage

### Run the App

```bash
# With pip/venv
streamlit run app.py

# With poetry
poetry run streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Basic Workflow

1. **Input Audio**
   - Upload a WAV/MP3 file, OR
   - Paste YouTube/SoundCloud URL

2. **Configure Options**
   - Bars: 4-16
   - Complexity: Basic/7ths/Extended
   - Style: Auto or select
   - Tempo: Auto or manual

3. **Analyze**
   - Click "🔍 Analyze"
   - Wait for detection (10-30s)
   - View detected key, tempo, chords

4. **Generate**
   - Click "🎲 Generate Progression"
   - View Roman numerals and concrete chords

5. **Output**
   - **Play to MIDI**: Select port, click "▶️ Play"
   - **Export MIDI**: Click "💾 Export MIDI"

6. **Effects**
   - View Ableton device chain suggestions
   - Copy settings for each track

## Connect to Ableton Live

### 1. Enable MIDI in Ableton

1. Open Ableton Live
2. Preferences → Link/Tempo/MIDI
3. Find your virtual MIDI port (ChordGen, VirMIDI, IAC Driver, etc.)
4. Enable **Track** and **Remote**

### 2. Create MIDI Track

1. Insert → MIDI Track
2. MIDI From: Select your virtual port
3. Monitor: **In**
4. Arm track (record button)

### 3. Load Instrument

Drag any instrument to the track:
- Wavetable
- Electric Piano
- Analog
- Sampler
- etc.

### 4. Receive MIDI from ChordGen

1. In ChordGen, select your virtual port
2. Click "▶️ Play to MIDI"
3. Chords should play in Ableton!

### 5. Apply Effects (Optional)

Copy the suggested device chain from ChordGen:

1. View effects suggestions for "Chords Track"
2. In Ableton, drag devices to track in order:
   - EQ Eight
   - Chorus/Flanger/etc.
   - Compressor
   - Reverb
3. Adjust parameters as suggested

## Example: Quick Test

### Test with Local File

1. Find any audio file (WAV/MP3)
2. Upload in ChordGen
3. Click Analyze
4. Expected: Key detected, tempo shown, chords listed
5. Click Generate
6. Expected: New progression appears
7. Click Export MIDI
8. Expected: File saved to `exports/` folder

### Test with YouTube

1. Find a simple chord progression video
   - Example: "C G Am F progression"
2. Paste URL
3. Analyze (takes longer due to download)
4. Generate similar progression
5. Export or play live

## Troubleshooting

### "No MIDI ports found"
- **Linux**: Run `sudo modprobe snd-virmidi`
- **macOS**: Enable IAC Driver in Audio MIDI Setup
- **Windows**: Ensure loopMIDI is running
- Restart ChordGen after setting up ports

### "Failed to download audio"
- Check internet connection
- Verify URL is accessible
- Try a different URL
- Use local file instead

### "Analysis taking too long"
- Long tracks: Try shorter clips
- Use `duration_limit` in code (default 3 minutes)
- Check CPU usage

### "Ableton not receiving MIDI"
- Verify MIDI track is armed
- Check Ableton MIDI preferences
- Ensure correct virtual port selected
- Try "Test Note" in Ableton MIDI setup

### "Chord detection inaccurate"
- Try cleaner audio source
- Adjust complexity setting
- Manual key override (edit code)
- Works best with clear harmonic content

## Advanced Usage

### Custom Effects Presets

Edit `presets/effects.yaml`:

```yaml
"My Custom Style":
  Chords:
    - device: "EQ Eight"
      params:
        HP: 80
    - device: "Reverb"
      params:
        size: 60
        wet: 20
  Bass:
    - device: "Saturator"
      params:
        drive: 4.0
```

### Programmatic Usage

```python
from chordgen import audio_io, analysis, chords, generate, midi_out

# Load and analyze
audio, sr = audio_io.load_audio("song.wav")
tempo, beats = analysis.detect_tempo_beats(audio, sr)
key, mode = analysis.detect_key(audio, sr)

# Detect chords
chroma = analysis.compute_chroma(audio, sr, beats)
detector = chords.ChordDetector()
detected = detector.detect(chroma, key, mode)

# Generate new progression
profile = generate.StyleProfile(key=key, mode=mode, tempo=tempo)
generator = generate.ProgressionGenerator(profile)
progression = generator.generate(bars=8)

# Export MIDI
midi_out.export_midi(progression, "output.mid", tempo=tempo)
```

## Next Steps

- Try different music styles
- Experiment with complexity levels
- Customize effects presets
- Integrate into your production workflow
- Add your own style profiles

## Performance Tips

- Use shorter audio clips for faster analysis
- Cache downloads (automatic)
- Close unnecessary apps during analysis
- Use SSD for temp files

## Getting Help

- Check logs in `logs/app.log`
- Enable debug mode: Set `log_level: "DEBUG"` in config
- Report issues with:
  - Audio file format
  - Detection results
  - Error messages from logs

Enjoy creating chord progressions! 🎹
