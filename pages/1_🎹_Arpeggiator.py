"""Arpeggiator page - Pattern-based arpeggiation with live control."""

import streamlit as st
from chordgen.arpeggiator import Arpeggiator, ArpPattern, ArpRate
from chordgen.chords import Chord
from chordgen import midi_out

st.set_page_config(page_title="Arpeggiator", page_icon="🎹", layout="wide")

# Initialize session state
if 'arp' not in st.session_state:
    st.session_state.arp = Arpeggiator()
if 'arp_playing' not in st.session_state:
    st.session_state.arp_playing = False

st.title("🎹 Arpeggiator")
st.markdown("*Transform chords into arpeggiated patterns*")

# Controls
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Pattern Settings")

    # Pattern selection
    pattern_options = {
        "Up": ArpPattern.UP,
        "Down": ArpPattern.DOWN,
        "Up-Down": ArpPattern.UP_DOWN,
        "Down-Up": ArpPattern.DOWN_UP,
        "Random": ArpPattern.RANDOM,
        "As Played": ArpPattern.AS_PLAYED,
        "Chord": ArpPattern.CHORD
    }
    selected_pattern = st.selectbox("Pattern", list(pattern_options.keys()))

    # Rate selection
    rate_options = {
        "Whole (1/1)": ArpRate.WHOLE,
        "Half (1/2)": ArpRate.HALF,
        "Quarter (1/4)": ArpRate.QUARTER,
        "Eighth (1/8)": ArpRate.EIGHTH,
        "Sixteenth (1/16)": ArpRate.SIXTEENTH,
        "Thirty-Second (1/32)": ArpRate.THIRTY_SECOND
    }
    selected_rate = st.selectbox("Rate", list(rate_options.keys()), index=3)

    # Octave range
    octaves = st.slider("Octave Range", 1, 4, 1)

    # Gate length
    gate = st.slider("Gate Length", 0.1, 2.0, 0.75, 0.05)

    # Swing
    swing = st.slider("Swing Amount", 0.0, 0.75, 0.0, 0.05)

    # Update arpeggiator
    st.session_state.arp.set_pattern(pattern_options[selected_pattern])
    st.session_state.arp.set_rate(rate_options[selected_rate])
    st.session_state.arp.set_octaves(octaves)
    st.session_state.arp.set_gate(gate)
    st.session_state.arp.set_swing(swing)

with col2:
    st.subheader("Input Chord")

    # Manual chord input
    chord_root = st.selectbox("Root", ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
    chord_quality = st.selectbox("Quality", ["maj", "min", "maj7", "min7", "dom7", "dim", "aug", "sus4", "sus2"])

    # Create chord
    input_chord = Chord(root=chord_root, quality=chord_quality, roman="I")

    # Preview arpeggio
    st.markdown("**Preview:**")
    duration = 4.0  # 4 beats
    arp_notes = st.session_state.arp.arpeggiate(input_chord, duration_beats=duration)

    # Display notes
    note_names = []
    for arp_note in arp_notes[:16]:  # Show first 16 notes
        note_num = arp_note.note % 12
        note_map = {0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
                   6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"}
        octave = arp_note.note // 12 - 1
        note_names.append(f"{note_map[note_num]}{octave}")

    st.code(" | ".join(note_names) + ("..." if len(arp_notes) > 16 else ""), language=None)
    st.caption(f"Total notes: {len(arp_notes)}")

# Playback controls
st.divider()
st.subheader("🎛️ Playback")

control_col1, control_col2, control_col3 = st.columns([1, 1, 2])

with control_col1:
    # MIDI port selection
    available_ports = midi_out.list_ports()
    if available_ports:
        selected_port = st.selectbox("MIDI Port", available_ports)
    else:
        st.warning("⚠️ No MIDI ports found")
        selected_port = None

with control_col2:
    tempo = st.number_input("Tempo (BPM)", 40.0, 200.0, 120.0, 1.0)

with control_col3:
    play_col, stop_col = st.columns(2)

    with play_col:
        if st.button("▶️ Play", disabled=not selected_port, use_container_width=True):
            try:
                sender = midi_out.MIDISender(selected_port)
                st.session_state.arp_playing = True

                # Send arp notes
                import time
                beat_duration = 60.0 / tempo

                for arp_note in arp_notes:
                    sender.send_note(arp_note.note, arp_note.velocity)
                    time.sleep(arp_note.duration * beat_duration)
                    sender.send_note(arp_note.note, 0)  # Note off

                    # Gap between notes
                    gap = (st.session_state.arp.rate.value - arp_note.duration) * beat_duration
                    if gap > 0:
                        time.sleep(gap)

                sender.close()
                st.session_state.arp_playing = False
                st.success("✅ Playback complete")

            except Exception as e:
                st.error(f"❌ Playback failed: {e}")

    with stop_col:
        if st.button("⏹ Stop", use_container_width=True):
            st.session_state.arp_playing = False
            st.info("Stopped")

# Use from Chord Generator
st.divider()
st.subheader("📥 From Chord Generator")

if 'progression' in st.session_state and st.session_state.progression:
    st.markdown("**Current Progression:**")
    prog_chords = st.session_state.progression[:8]
    chord_str = " → ".join([f"{c.root}{c.quality}" for c in prog_chords])
    st.code(chord_str, language=None)

    if st.button("🎵 Arpeggiate Progression", use_container_width=True):
        if selected_port:
            try:
                sender = midi_out.MIDISender(selected_port)
                beat_duration = 60.0 / tempo

                for chord in st.session_state.progression:
                    # Arpeggiate each chord for its duration
                    arp_notes = st.session_state.arp.arpeggiate(
                        chord,
                        duration_beats=chord.duration_beats
                    )

                    import time
                    for arp_note in arp_notes:
                        sender.send_note(arp_note.note, arp_note.velocity)
                        time.sleep(arp_note.duration * beat_duration)
                        sender.send_note(arp_note.note, 0)

                        gap = (st.session_state.arp.rate.value - arp_note.duration) * beat_duration
                        if gap > 0:
                            time.sleep(gap)

                sender.close()
                st.success("✅ Progression arpeggiated!")

            except Exception as e:
                st.error(f"❌ Failed: {e}")
        else:
            st.warning("No MIDI port selected")
else:
    st.info("Generate a progression in the Chord Generator to use it here")

# Presets
with st.sidebar:
    st.header("🎼 Presets")

    if st.button("Classic Up", use_container_width=True):
        st.session_state.arp.set_pattern(ArpPattern.UP)
        st.session_state.arp.set_rate(ArpRate.EIGHTH)
        st.session_state.arp.set_octaves(1)
        st.session_state.arp.set_gate(0.75)
        st.session_state.arp.set_swing(0.0)
        st.rerun()

    if st.button("Triplet Feel", use_container_width=True):
        st.session_state.arp.set_pattern(ArpPattern.UP_DOWN)
        st.session_state.arp.set_rate(ArpRate.EIGHTH)
        st.session_state.arp.set_octaves(2)
        st.session_state.arp.set_gate(0.5)
        st.session_state.arp.set_swing(0.33)
        st.rerun()

    if st.button("Random Sparkle", use_container_width=True):
        st.session_state.arp.set_pattern(ArpPattern.RANDOM)
        st.session_state.arp.set_rate(ArpRate.SIXTEENTH)
        st.session_state.arp.set_octaves(3)
        st.session_state.arp.set_gate(0.3)
        st.session_state.arp.set_swing(0.0)
        st.rerun()
