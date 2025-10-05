"""Step Sequencer page - 16-step programmable sequencer."""

import streamlit as st
from chordgen.sequencer import Sequencer, Step
from chordgen import midi_out
import time

st.set_page_config(page_title="Sequencer", page_icon="🎵", layout="wide")

# Initialize session state
if 'sequencer' not in st.session_state:
    st.session_state.sequencer = Sequencer(num_patterns=4)
if 'seq_playing' not in st.session_state:
    st.session_state.seq_playing = False

st.title("🎵 Step Sequencer")
st.markdown("*16-step programmable sequencer with patterns*")

# Pattern selector
pattern_col, length_col = st.columns([2, 1])
with pattern_col:
    pattern_name = st.selectbox(
        "Pattern",
        list(st.session_state.sequencer.patterns.keys()),
        key="pattern_select"
    )
    st.session_state.sequencer.switch_pattern(pattern_name)

with length_col:
    pattern_length = st.slider("Length", 1, 16,
                                st.session_state.sequencer.current_pattern.length,
                                key="pattern_length")
    st.session_state.sequencer.set_pattern_length(pattern_length)

# Step grid
st.subheader("🎹 Step Grid")

# Create 16-step grid
grid_col1, grid_col2 = st.columns([3, 1])

with grid_col1:
    # Display steps in rows of 4
    for row in range(4):
        cols = st.columns(4)
        for col_idx, col in enumerate(cols):
            step_num = row * 4 + col_idx
            step = st.session_state.sequencer.current_pattern.steps[step_num]

            with col:
                # Step container
                step_active = st.checkbox(
                    f"Step {step_num + 1}",
                    value=step.active,
                    key=f"step_{step_num}_active"
                )

                if step_active:
                    # Note input
                    note_val = st.number_input(
                        "Note",
                        0, 127,
                        step.note if step.note else 60,
                        key=f"step_{step_num}_note"
                    )

                    # Velocity
                    vel_val = st.slider(
                        "Vel",
                        0, 127,
                        step.velocity,
                        key=f"step_{step_num}_vel"
                    )

                    # Update step
                    st.session_state.sequencer.set_step(
                        step_num,
                        note=note_val,
                        velocity=vel_val,
                        active=step_active
                    )
                else:
                    st.session_state.sequencer.clear_step(step_num)

with grid_col2:
    st.subheader("Pattern Info")
    summary = st.session_state.sequencer.get_pattern_summary()
    st.metric("Active Steps", summary['active_steps'])
    st.metric("Density", f"{summary['density']*100:.0f}%")

    st.divider()

    # Quick actions
    st.subheader("Quick Actions")

    if st.button("Clear", use_container_width=True):
        st.session_state.sequencer.clear_pattern()
        st.rerun()

    if st.button("Randomize", use_container_width=True):
        density = st.slider("Density", 0.0, 1.0, 0.5, key="random_density")
        st.session_state.sequencer.randomize(density=density)
        st.rerun()

    if st.button("Copy", use_container_width=True):
        st.session_state.sequencer.copy_pattern()
        st.success("Pattern copied!")

    if st.button("Paste", use_container_width=True):
        st.session_state.sequencer.paste_pattern()
        st.rerun()

# Transport controls
st.divider()
st.subheader("🎛️ Transport")

transport_col1, transport_col2, transport_col3 = st.columns(3)

with transport_col1:
    # MIDI port
    available_ports = midi_out.list_ports()
    if available_ports:
        selected_port = st.selectbox("MIDI Port", available_ports, key="seq_port")
    else:
        st.warning("⚠️ No MIDI ports")
        selected_port = None

with transport_col2:
    tempo = st.number_input("Tempo (BPM)", 40.0, 200.0, 120.0, 1.0, key="seq_tempo")

with transport_col3:
    loop = st.checkbox("Loop", value=True)

# Playback buttons
play_col, stop_col, record_col = st.columns(3)

with play_col:
    if st.button("▶️ Play", disabled=not selected_port, use_container_width=True):
        try:
            sender = midi_out.MIDISender(selected_port)
            st.session_state.seq_playing = True
            st.session_state.sequencer.reset()

            beat_duration = 60.0 / tempo / 4  # 16th note duration

            # Play loop
            loops = 0
            max_loops = 100 if loop else 1

            while loops < max_loops:
                for i in range(st.session_state.sequencer.current_pattern.length):
                    step = st.session_state.sequencer.step()

                    if step and step.should_play():
                        # Send note on
                        sender.send_note(step.note, step.velocity)
                        time.sleep(beat_duration * step.length * 0.9)
                        # Send note off
                        sender.send_note(step.note, 0)
                        time.sleep(beat_duration * step.length * 0.1)
                    else:
                        time.sleep(beat_duration)

                loops += 1
                if not loop:
                    break

            sender.close()
            st.session_state.seq_playing = False
            st.success("✅ Playback complete")

        except Exception as e:
            st.error(f"❌ Failed: {e}")
            st.session_state.seq_playing = False

with stop_col:
    if st.button("⏹ Stop", use_container_width=True):
        st.session_state.seq_playing = False
        st.info("Stopped")

with record_col:
    if st.button("⏺ Record", disabled=True, use_container_width=True):
        st.info("Recording coming soon!")

# Scale quantization
st.divider()
st.subheader("🎼 Scale Tools")

scale_col1, scale_col2 = st.columns(2)

with scale_col1:
    root = st.selectbox("Scale Root", ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"], key="scale_root")
    scale_type = st.selectbox("Scale Type", ["Major", "Minor", "Dorian", "Phrygian", "Pentatonic"], key="scale_type")

with scale_col2:
    if st.button("Quantize to Scale", use_container_width=True):
        # Generate scale notes (simplified)
        root_note = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"].index(root)

        if scale_type == "Major":
            intervals = [0, 2, 4, 5, 7, 9, 11]
        elif scale_type == "Minor":
            intervals = [0, 2, 3, 5, 7, 8, 10]
        elif scale_type == "Dorian":
            intervals = [0, 2, 3, 5, 7, 9, 10]
        elif scale_type == "Phrygian":
            intervals = [0, 1, 3, 5, 7, 8, 10]
        else:  # Pentatonic
            intervals = [0, 2, 4, 7, 9]

        # Generate scale notes across octaves
        scale_notes = []
        for octave in range(11):
            for interval in intervals:
                scale_notes.append(root_note + interval + (octave * 12))

        st.session_state.sequencer.quantize_to_scale(scale_notes)
        st.success(f"Quantized to {root} {scale_type}")
        st.rerun()

    if st.button("Transpose +12", use_container_width=True):
        st.session_state.sequencer.shift_notes(12)
        st.rerun()

    if st.button("Transpose -12", use_container_width=True):
        st.session_state.sequencer.shift_notes(-12)
        st.rerun()

# Sidebar presets
with st.sidebar:
    st.header("🎼 Presets")

    if st.button("Basic Beat", use_container_width=True):
        st.session_state.sequencer.clear_pattern()
        st.session_state.sequencer.set_step(0, note=36, velocity=100)  # Kick
        st.session_state.sequencer.set_step(4, note=38, velocity=90)   # Snare
        st.session_state.sequencer.set_step(8, note=36, velocity=100)  # Kick
        st.session_state.sequencer.set_step(12, note=38, velocity=90)  # Snare
        st.rerun()

    if st.button("Bassline", use_container_width=True):
        st.session_state.sequencer.clear_pattern()
        for i in [0, 3, 7, 10, 14]:
            st.session_state.sequencer.set_step(i, note=36 + (i % 12), velocity=100)
        st.rerun()

    if st.button("Random Melody", use_container_width=True):
        st.session_state.sequencer.randomize(
            density=0.6,
            note_range=(60, 84),
            vel_range=(80, 120)
        )
        st.rerun()
