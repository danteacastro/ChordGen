# ChordGen MIDI Device - Architecture Design

## Overview

Transform ChordGen into a full-featured MIDI device with:
- **Chord Generator**: AI-powered progression creation (existing)
- **Arpeggiator**: Multiple arp patterns with tempo sync
- **Step Sequencer**: 16-step programmable sequencer
- **Pattern Storage**: Save/load patterns and progressions
- **Live Performance**: Real-time control and playback

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   ChordGen MIDI Device                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────┐  ┌──────────────────────────────┐  │
│  │  Chord Engine   │  │      Arpeggiator             │  │
│  │  - Analysis     │  │  - Up/Down/Random            │  │
│  │  - Generation   │──▶  - Rate (1/4, 1/8, 1/16)     │  │
│  │  - Progression  │  │  - Gate length               │  │
│  └─────────────────┘  │  - Octave range              │  │
│                       └────────────┬─────────────────┘  │
│  ┌─────────────────┐              │                     │
│  │  Step Sequencer │              │                     │
│  │  - 16 steps     │              │                     │
│  │  - Note/vel/len │──────────────┤                     │
│  │  - Pattern bank │              │                     │
│  └─────────────────┘              │                     │
│                                    ▼                     │
│                          ┌─────────────────┐            │
│                          │  MIDI Router    │            │
│                          │  - Virtual port │            │
│                          │  - Clock sync   │            │
│                          │  - Transport    │            │
│                          └─────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

## New Modules

### 1. arpeggiator.py

**Features:**
- Arp patterns: Up, Down, Up-Down, Random, As Played
- Note rates: 1/4, 1/8, 1/16, 1/32
- Octave range: 1-4 octaves
- Gate length: 10%-200%
- Swing amount: 0%-75%
- Latch mode

**Class Structure:**
```python
class Arpeggiator:
    def __init__(self, tempo: float, pattern: str, rate: str):
        self.tempo = tempo
        self.pattern = pattern  # "up", "down", "updown", "random"
        self.rate = rate        # "1/4", "1/8", "1/16", "1/32"
        self.octaves = 1
        self.gate = 0.75        # 75% gate
        self.swing = 0.0
        self.latch = False

    def arpeggiate(self, chord: Chord) -> List[ArpNote]
        """Generate arp sequence from chord."""

    def get_next_note(self) -> Optional[ArpNote]
        """Get next note in sequence (for real-time)."""
```

### 2. sequencer.py

**Features:**
- 16-step sequencer
- Per-step: Note, Velocity, Length, Probability
- Multiple patterns (A, B, C, D)
- Pattern chaining
- Step recording
- Randomization

**Class Structure:**
```python
class Step:
    note: Optional[int]
    velocity: int = 100
    length: float = 1.0     # 1.0 = full step
    probability: float = 1.0 # 0.0-1.0
    active: bool = True

class SequencerPattern:
    steps: List[Step]        # 16 steps
    length: int = 16
    scale: Optional[str] = None

class Sequencer:
    patterns: Dict[str, SequencerPattern]
    current_pattern: str

    def step(self) -> Optional[Step]:
        """Advance sequencer and return current step."""

    def record_step(self, step_num: int, note: int):
        """Record note to step."""

    def randomize(self, density: float = 0.5):
        """Randomize pattern."""
```

### 3. midi_clock.py

**Features:**
- Internal clock or external sync
- Transport controls (play/stop/record)
- BPM control
- Bar/beat position tracking

**Class Structure:**
```python
class MIDIClock:
    def __init__(self, tempo: float = 120):
        self.tempo = tempo
        self.playing = False
        self.position = 0.0  # in beats

    def tick(self, delta_time: float):
        """Advance clock by delta time."""

    def get_position(self) -> Tuple[int, int, int]:
        """Return (bar, beat, tick)."""

    def sync_to_midi_clock(self, midi_message):
        """Sync to external MIDI clock."""
```

### 4. pattern_manager.py

**Features:**
- Save/load patterns
- Progression library
- User presets
- Export/import

**Class Structure:**
```python
class Pattern:
    name: str
    chords: List[Chord]
    arp_settings: dict
    sequencer_data: dict
    tempo: float

class PatternManager:
    def save_pattern(self, pattern: Pattern, path: Path):
        """Save pattern to file."""

    def load_pattern(self, path: Path) -> Pattern:
        """Load pattern from file."""

    def get_preset_library(self) -> List[Pattern]:
        """Get built-in presets."""
```

## Enhanced GUI Layout

### Main Window (Streamlit Multi-Page App)

**Page 1: Chord Generator** (existing)
- Audio analysis
- Chord detection
- Progression generation

**Page 2: Arpeggiator** (NEW)
```
┌─────────────────────────────────────────┐
│  🎹 ARPEGGIATOR                         │
├─────────────────────────────────────────┤
│  Pattern: [Up ▼]  Rate: [1/8 ▼]        │
│  Octaves: [▬▬●▬] 2   Gate: [▬▬▬●] 75%  │
│  Swing:   [▬●▬▬] 25% Latch: [☐]        │
│                                          │
│  Input Chord: [Cmaj7________________]   │
│  Output:      C E G B | C E G B         │
│                                          │
│  [▶ Play] [⏹ Stop] [⏺ Latch]          │
└─────────────────────────────────────────┘
```

**Page 3: Sequencer** (NEW)
```
┌─────────────────────────────────────────────────────────┐
│  🎵 STEP SEQUENCER                     Pattern: A ▼     │
├─────────────────────────────────────────────────────────┤
│  Step:  [1][2][3][4][5][6][7][8][9][10][11][12][13][14][15][16]
│  Note:  [●][●][·][●][●][·][●][·][●][·][●][·][●][·][·][·]
│  Vel:   [▬][▬][·][▬][▬][·][▬][·][▬][·][▬][·][▬][·][·][·]
│  Len:   [▬][▬][·][▬][▬][·][▬][·][▬][·][▬][·][▬][·][·][·]
│                                                          │
│  Scale: [C Minor ▼]  Density: [▬▬●▬] 60%              │
│  [Clear] [Randomize] [Copy] [Paste]                    │
│                                                          │
│  [▶ Play] [⏹ Stop] [⏺ Record] [🔄 Loop]               │
└─────────────────────────────────────────────────────────┘
```

**Page 4: Patterns** (NEW)
```
┌─────────────────────────────────────────┐
│  💾 PATTERN LIBRARY                     │
├─────────────────────────────────────────┤
│  Current: "Indie Progression 1"         │
│                                          │
│  My Patterns:                            │
│  ☑ Indie Progression 1                  │
│  ☐ Neo Soul Groove                      │
│  ☐ House Loop                           │
│                                          │
│  Presets:                                │
│  ☐ Classic ii-V-I                       │
│  ☐ Pop Progression                      │
│  ☐ Jazz Turnaround                      │
│                                          │
│  [Save] [Load] [Export] [Import]        │
└─────────────────────────────────────────┘
```

**Page 5: Live Performance** (NEW)
```
┌─────────────────────────────────────────────────────────┐
│  🎸 LIVE CONTROL                                         │
├─────────────────────────────────────────────────────────┤
│  Transport: [▶ PLAY] [⏹ STOP] [⏺ REC]                  │
│  Tempo: [120.0 BPM] ●━━━━━━━━━━━━━━━━━━━━━━━━━━━●      │
│  Position: Bar 4 | Beat 3 | Tick 240                    │
│                                                          │
│  Active Modules:                                         │
│  ☑ Chord Generator  → Currently: Cmaj7                  │
│  ☑ Arpeggiator     → Pattern: Up, Rate: 1/8            │
│  ☐ Sequencer       → Pattern: A (OFF)                   │
│                                                          │
│  MIDI Output:                                            │
│  Port: [ChordGen ▼]  Channel: [1 ▼]                    │
│  [●] Sending MIDI...                                    │
│                                                          │
│  Quick Actions:                                          │
│  [Randomize Chord] [Next Pattern] [Tap Tempo]          │
└─────────────────────────────────────────────────────────┘
```

## Integration Points

### Chord Generator → Arpeggiator
```python
# User generates progression
progression = generator.generate(bars=8)

# Send to arpeggiator
arp = Arpeggiator(tempo=120, pattern="up", rate="1/8")
for chord in progression:
    arp_notes = arp.arpeggiate(chord)
    midi_sender.send_notes(arp_notes)
```

### Chord Generator → Sequencer
```python
# Use chords to create sequencer pattern
sequencer = Sequencer()
for i, chord in enumerate(progression[:4]):  # First 4 chords
    root = chord_to_midi_notes(chord.root, "maj", 4)[0]
    sequencer.patterns["A"].steps[i*4].note = root
```

### Combined Workflow
```python
# 1. Analyze and generate progression
progression = analyze_and_generate(audio_file)

# 2. Create arp from progression
arp.set_chords(progression)

# 3. Create sequencer pattern from chords
sequencer.create_from_chords(progression)

# 4. Live performance
clock = MIDIClock(tempo=120)
while clock.playing:
    # Get current chord
    current_chord = progression[clock.bar % len(progression)]

    # Arpeggiate it
    if arp.enabled:
        note = arp.get_next_note(current_chord)
        midi_sender.send_note(note)

    # Or play sequencer
    if sequencer.enabled:
        step = sequencer.get_current_step()
        if step.active:
            midi_sender.send_note(step.note, step.velocity)

    clock.tick()
```

## File Structure (New Additions)

```
ChordGen/
├── chordgen/
│   ├── arpeggiator.py      # NEW: Arp engine
│   ├── sequencer.py        # NEW: Step sequencer
│   ├── midi_clock.py       # NEW: Clock/transport
│   ├── pattern_manager.py  # NEW: Pattern storage
│   └── live_engine.py      # NEW: Live performance coordinator
├── app_pages/              # NEW: Multi-page Streamlit
│   ├── 1_chord_generator.py
│   ├── 2_arpeggiator.py
│   ├── 3_sequencer.py
│   ├── 4_patterns.py
│   └── 5_live.py
├── patterns/               # NEW: User patterns
│   ├── user/
│   └── presets/
└── app.py                  # Updated: Multi-page launcher
```

## Features Summary

### Arpeggiator
- ✅ Multiple patterns (Up, Down, Up-Down, Random, As Played)
- ✅ Note rates (1/4, 1/8, 1/16, 1/32)
- ✅ Octave range control
- ✅ Gate length
- ✅ Swing
- ✅ Latch mode
- ✅ Tempo sync

### Sequencer
- ✅ 16-step sequencer
- ✅ Per-step note/velocity/length/probability
- ✅ Multiple patterns (A/B/C/D)
- ✅ Pattern chaining
- ✅ Randomization
- ✅ Scale quantization
- ✅ Step recording

### Pattern Management
- ✅ Save/load patterns
- ✅ Preset library
- ✅ Export/import (JSON/MIDI)
- ✅ Pattern organization

### Live Performance
- ✅ Transport controls
- ✅ Tempo control
- ✅ Module routing
- ✅ Quick actions
- ✅ MIDI output monitor

## Implementation Order

1. **Phase 1: Core MIDI Components**
   - midi_clock.py
   - Enhanced midi_out.py with real-time scheduling

2. **Phase 2: Arpeggiator**
   - arpeggiator.py
   - Arp GUI page
   - Integration with chord generator

3. **Phase 3: Sequencer**
   - sequencer.py
   - Sequencer GUI page
   - Pattern creation from chords

4. **Phase 4: Pattern Management**
   - pattern_manager.py
   - Pattern library GUI
   - Save/load functionality

5. **Phase 5: Live Performance**
   - live_engine.py (coordinator)
   - Live performance GUI
   - Module routing

6. **Phase 6: Polish**
   - Presets
   - Keyboard shortcuts
   - MIDI learn
   - Performance optimizations

## Next Steps

Would you like me to:
1. **Start with Phase 1** - Implement MIDI clock and real-time engine
2. **Build the arpeggiator first** - Get arp working quickly
3. **Create the sequencer** - Step sequencer implementation
4. **Build all at once** - Complete transformation

Which approach would you prefer?
