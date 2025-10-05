# ChordGen Usage Example

## Using ChordGen with Your YouTube Video

Video: https://www.youtube.com/watch?v=t_4Nh4H95Nc

### Step-by-Step Workflow

#### 1. **Analyze the YouTube Video**

Go to **🎼 Chord Generator** page:

1. Select "URL (YouTube/SoundCloud)"
2. Paste: `https://www.youtube.com/watch?v=t_4Nh4H95Nc`
3. Click **🔍 Analyze**

ChordGen will:
- Download the audio
- Detect tempo (BPM)
- Detect key/mode (e.g., "F# minor")
- Analyze chord progression from the track
- Create a style profile

**Expected Output:**
```
Key: F# minor
Tempo: ~128 BPM (typical house/dance tempo)
Detected Chords: F#m, C#m, D, A, E, etc.
```

#### 2. **Generate New Progression**

Still in Chord Generator:

1. Set bars: 8
2. Set complexity: Extended (for rich chords)
3. Style: Auto-detect (or House/Disco)
4. Click **🎲 Generate Progression**

ChordGen creates a new progression using the learned style.

#### 3. **View in Jazz Theory**

Go to **🎼 Jazz Editor** page:

The generated progression will show with:
- **Scale degrees** (e.g., i-iv-VI-III in F# minor)
- **Recommended scales** (F# Aeolian, Dorian)
- **Available tensions** (9ths, 11ths, 13ths)
- **Chord formulas** (1-b3-5-b7 for min7)

You can:
- Change voicings (Drop-2, Rootless, etc.)
- Edit individual chords
- See which scale fits each chord

#### 4. **Arpeggiate It**

Go to **🎹 Arpeggiator** page:

1. Select pattern: "Up" or "Random"
2. Rate: 1/16 (for fast house-style arps)
3. Octaves: 2-3
4. Gate: 30% (short, plucky notes)
5. Swing: 0% (straight house groove)

Click **🎵 Arpeggiate Progression** to hear the result.

#### 5. **Sequence It**

Go to **🎵 Sequencer** page:

1. Use detected chords to create a bassline pattern
2. Program 16 steps with the root notes
3. Add variations with velocity and probability
4. Quantize to F# minor scale

#### 6. **Sync with Ableton**

Go to **🎸 Live** page:

**Setup Ableton:**
1. In Ableton: Preferences → Link/Tempo/MIDI
2. Enable "Sync" on a MIDI output (e.g., IAC Driver or loopMIDI)
3. Set Ableton to send MIDI clock

**In ChordGen:**
1. Check "🔗 Sync to Ableton"
2. Select the MIDI sync input port
3. Click **🔗 Connect Sync**

Now ChordGen will:
- Follow Ableton's tempo automatically
- Start/stop when Ableton plays/stops
- Stay perfectly in time

#### 7. **Send MIDI to Ableton**

**In Ableton:**
1. Create a MIDI track
2. Set input to ChordGen's MIDI output
3. Arm the track for recording
4. Load a synth (Serum, Analog, etc.)

**In ChordGen (Live page):**
1. Select MIDI output port
2. Enable modules (Chord + Arp)
3. Click **▶️ PLAY**

ChordGen sends MIDI notes to Ableton in real-time!

---

## What ChordGen Does With Your Track

### Audio Analysis
```
Input: YouTube video
↓
Download & convert to audio
↓
Analyze: Tempo, Key, Chords
↓
Create StyleProfile
```

### Chord Detection
Uses **Hidden Markov Model (HMM)** with Viterbi algorithm:
```
Audio → Chromagram → Chord Templates → HMM → Detected Chords
```

### Progression Generation
Uses **Markov Chains**:
```
Learned transitions (e.g., i → iv: 40%, i → VI: 30%)
↓
Generate new progression
↓
Apply style rules (cadences, voice leading)
```

### Jazz Analysis
```
Chord: F#min7
↓
Formula: 1-b3-5-b7
↓
Recommended Scale: F# Dorian
↓
Tensions: 9, 11
↓
Voicing: Drop-2, Rootless A/B
```

---

## Key Features Demonstrated

### ✅ **Ableton Sync (NEW!)**
- Listens to MIDI clock messages
- Auto-adjusts tempo
- Transport control (play/stop)

### ✅ **Jazz Scales (NEW!)**
- 20+ jazz scales (Dorian, Lydian, Altered, etc.)
- Scale-chord relationships
- Avoid notes highlighted

### ✅ **Chord Voicings (NEW!)**
- Drop-2, Drop-3, Drop-2&4
- Rootless voicings (A & B)
- Shell voicings
- Inversions

### ✅ **Chord Editor (NEW!)**
- Edit any chord in progression
- See formula and tensions
- Real-time MIDI playback

---

## Expected Results with Your Video

Based on the typical house/trance style:

**Detected:**
- Key: F# minor or D major
- Tempo: 125-130 BPM
- Progression: Likely i-VI-III-VII or i-iv-v-i

**Generated:**
- Similar energy progression
- Extended chords (9ths, sus chords)
- Uplifting house vibe

**Jazz View:**
- F#m7 → Recommended: F# Dorian
- D maj7 → Recommended: D Lydian
- Available tensions for rich voicings

---

## Troubleshooting

### "No MIDI ports found"
**Solution:** Create a virtual MIDI port:
- **Mac:** IAC Driver (Audio MIDI Setup)
- **Windows:** loopMIDI
- **Linux:** `sudo modprobe snd-virmidi`

### "MIDI sync not working"
**Checklist:**
1. Ableton sending MIDI clock? (Prefs → MIDI → Sync → Track: On)
2. Correct input port selected in ChordGen?
3. Try clicking "Connect Sync" again

### "Chords don't sound right"
- The HMM might misdetect complex chords
- Use **Jazz Editor** to manually correct
- Try different complexity levels

---

## Next Steps

1. **Save your pattern** (💾 Patterns page)
2. **Export to MIDI** for use in your DAW
3. **Create variations** with arpeggiator
4. **Experiment with voicings** in Jazz Editor
5. **Perform live** with Ableton sync!

Enjoy! 🎹🎵
