"""Live Performance - Real-time MIDI device control."""

import streamlit as st
from chordgen.midi_clock import MIDIClock, TransportState
from chordgen import midi_out
import time
import threading

st.set_page_config(page_title="Live Performance", page_icon="🎸", layout="wide")

# Initialize session state
if 'midi_clock' not in st.session_state:
    st.session_state.midi_clock = MIDIClock(tempo=120.0)
if 'live_running' not in st.session_state:
    st.session_state.live_running = False

st.title("🎸 Live Performance")
st.markdown("*Real-time MIDI control and performance*")

# MIDI Sync Toggle
sync_col1, sync_col2 = st.columns([1, 3])

with sync_col1:
    external_sync = st.checkbox("🔗 Sync to Ableton", value=st.session_state.midi_clock.is_externally_synced())

with sync_col2:
    if external_sync:
        from chordgen.midi_sync import MIDIClockSync
        sync = MIDIClockSync()
        input_ports = sync.list_input_ports()

        if input_ports:
            sync_port = st.selectbox("MIDI Sync Input", input_ports, key="sync_port")

            if st.button("🔗 Connect Sync"):
                if st.session_state.midi_clock.enable_external_sync(sync_port):
                    st.success(f"✅ Synced to {sync_port}")
                    st.rerun()
                else:
                    st.error("Failed to connect")
        else:
            st.warning("No MIDI input ports found. Configure Ableton to send MIDI clock.")

        # Show sync status
        if st.session_state.midi_clock.is_externally_synced():
            ext_tempo = st.session_state.midi_clock.get_external_tempo()
            if ext_tempo:
                st.info(f"🎵 Synced! Ableton tempo: {ext_tempo:.1f} BPM")
    else:
        if st.session_state.midi_clock.is_externally_synced():
            st.session_state.midi_clock.disable_external_sync()

st.divider()

# Transport controls
st.subheader("🎛️ Transport")

transport_col1, transport_col2, transport_col3, transport_col4 = st.columns(4)

with transport_col1:
    if st.button("▶️ PLAY", use_container_width=True, type="primary"):
        st.session_state.midi_clock.start()
        st.session_state.live_running = True
        st.rerun()

with transport_col2:
    if st.button("⏹ STOP", use_container_width=True):
        st.session_state.midi_clock.stop()
        st.session_state.live_running = False
        st.rerun()

with transport_col3:
    if st.button("⏸ PAUSE", use_container_width=True):
        st.session_state.midi_clock.pause()
        st.session_state.live_running = False
        st.rerun()

with transport_col4:
    if st.button("⏺ RECORD", use_container_width=True, disabled=True):
        st.info("Recording coming soon!")

# Status display
status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    state = st.session_state.midi_clock.state.value.upper()
    if state == "PLAYING":
        st.success(f"🟢 {state}")
    elif state == "STOPPED":
        st.error(f"🔴 {state}")
    else:
        st.warning(f"🟡 {state}")

with status_col2:
    position = st.session_state.midi_clock.get_position()
    st.metric("Position", f"Bar {position.bar} | Beat {position.beat}")

with status_col3:
    st.metric("Tempo", f"{st.session_state.midi_clock.tempo:.1f} BPM")

# Tempo control
st.divider()
tempo_col1, tempo_col2 = st.columns([3, 1])

with tempo_col1:
    new_tempo = st.slider(
        "Tempo",
        20.0, 300.0,
        st.session_state.midi_clock.tempo,
        0.1,
        key="tempo_slider"
    )
    st.session_state.midi_clock.set_tempo(new_tempo)

with tempo_col2:
    if st.button("🔄 Reset Position", use_container_width=True):
        st.session_state.midi_clock.reset()
        st.rerun()

# Module control
st.divider()
st.subheader("🎹 Active Modules")

module_col1, module_col2, module_col3 = st.columns(3)

with module_col1:
    st.markdown("**Chord Generator**")
    chord_enabled = st.checkbox("Enable", value=True, key="chord_enabled")

    if 'progression' in st.session_state and st.session_state.progression:
        current_bar = st.session_state.midi_clock.get_position().bar
        chord_index = (current_bar - 1) % len(st.session_state.progression)
        current_chord = st.session_state.progression[chord_index]
        st.info(f"Currently: {current_chord.root}{current_chord.quality}")
    else:
        st.warning("No progression loaded")

with module_col2:
    st.markdown("**Arpeggiator**")
    arp_enabled = st.checkbox("Enable", value=False, key="arp_enabled")

    if 'arp' in st.session_state:
        st.info(f"Pattern: {st.session_state.arp.pattern.value}")
        st.caption(f"Rate: {st.session_state.arp.rate.name}")
    else:
        st.warning("Arp not initialized")

with module_col3:
    st.markdown("**Sequencer**")
    seq_enabled = st.checkbox("Enable", value=False, key="seq_enabled")

    if 'sequencer' in st.session_state:
        pattern = st.session_state.sequencer.current_pattern
        st.info(f"Pattern: {pattern.name}")
        summary = st.session_state.sequencer.get_pattern_summary()
        st.caption(f"Active: {summary['active_steps']}/{pattern.length}")
    else:
        st.warning("Sequencer not initialized")

# MIDI Output
st.divider()
st.subheader("🔌 MIDI Output")

midi_col1, midi_col2 = st.columns(2)

with midi_col1:
    available_ports = midi_out.list_ports()
    if available_ports:
        selected_port = st.selectbox("MIDI Port", available_ports, key="live_port")
        midi_channel = st.number_input("MIDI Channel", 1, 16, 1, key="midi_channel")
    else:
        st.warning("⚠️ No MIDI ports found")
        selected_port = None

with midi_col2:
    if st.session_state.live_running:
        st.success("● MIDI Output Active")
    else:
        st.info("○ MIDI Output Idle")

    # MIDI activity indicator
    st.caption(f"Port: {selected_port if selected_port else 'None'}")

# Quick Actions
st.divider()
st.subheader("⚡ Quick Actions")

action_col1, action_col2, action_col3 = st.columns(3)

with action_col1:
    if st.button("🎲 Randomize Chord", use_container_width=True):
        if 'progression' in st.session_state and st.session_state.progression:
            import random
            st.session_state.progression = random.sample(
                st.session_state.progression,
                len(st.session_state.progression)
            )
            st.success("Shuffled progression!")
        else:
            st.warning("No progression to randomize")

with action_col2:
    if st.button("➡️ Next Pattern", use_container_width=True):
        if 'sequencer' in st.session_state:
            patterns = list(st.session_state.sequencer.patterns.keys())
            current = st.session_state.sequencer.current_pattern_name
            current_idx = patterns.index(current)
            next_idx = (current_idx + 1) % len(patterns)
            st.session_state.sequencer.switch_pattern(patterns[next_idx])
            st.success(f"Switched to Pattern {patterns[next_idx]}")
            st.rerun()

with action_col3:
    if st.button("👆 Tap Tempo", use_container_width=True):
        st.info("Tap tempo coming soon!")

# Performance stats
st.divider()

with st.expander("📊 Performance Stats"):
    stats_col1, stats_col2, stats_col3 = st.columns(3)

    with stats_col1:
        st.metric("Total Beats", f"{st.session_state.midi_clock.get_position().total_beats:.1f}")

    with stats_col2:
        if 'progression' in st.session_state:
            st.metric("Progression Length", len(st.session_state.progression))

    with stats_col3:
        st.metric("Active Modules", sum([
            chord_enabled,
            arp_enabled,
            seq_enabled
        ]))

# Live playback info
if st.session_state.live_running:
    st.info("🎵 Live mode active! The MIDI clock is running. Stop playback to make changes.")

# Sidebar controls
with st.sidebar:
    st.header("🎚️ Quick Controls")

    st.markdown("**Time Signature**")
    time_sig_num = st.selectbox("Numerator", [3, 4, 5, 6, 7], index=1)
    time_sig_den = st.selectbox("Denominator", [4, 8], index=0)

    if st.button("Apply Time Signature"):
        st.session_state.midi_clock.time_signature = (time_sig_num, time_sig_den)
        st.success(f"Set to {time_sig_num}/{time_sig_den}")

    st.divider()

    st.markdown("**Presets**")

    if st.button("🎹 Chord + Arp", use_container_width=True):
        st.session_state.chord_enabled = True
        st.session_state.arp_enabled = True
        st.session_state.seq_enabled = False
        st.rerun()

    if st.button("🎵 Sequencer Only", use_container_width=True):
        st.session_state.chord_enabled = False
        st.session_state.arp_enabled = False
        st.session_state.seq_enabled = True
        st.rerun()

    if st.button("🎸 Full Stack", use_container_width=True):
        st.session_state.chord_enabled = True
        st.session_state.arp_enabled = True
        st.session_state.seq_enabled = True
        st.rerun()

    st.divider()

    st.markdown("**Help**")
    st.caption("""
    - **Play**: Start MIDI clock and output
    - **Stop**: Stop all output
    - **Modules**: Enable/disable each engine
    - **Quick Actions**: Instant performance changes
    """)
