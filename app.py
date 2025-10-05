"""
ChordGen - AI-Powered MIDI Device
Main entry point / Home page
"""

import streamlit as st
from pathlib import Path

# Initialize before importing modules
from chordgen.config import init_directories, settings
from chordgen.utils import setup_logging

# Setup
init_directories()
setup_logging()

# Page config
st.set_page_config(
    page_title="ChordGen - MIDI Device",
    page_icon="🎹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and intro
st.title("🎹 ChordGen - AI-Powered MIDI Device")
st.markdown("### *Professional chord progression generator, arpeggiator, and step sequencer*")

st.divider()

# Feature overview
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🎼 Chord Generator
    - Audio analysis & chord detection
    - AI-powered progression generation
    - Style profiling (Indie, Jazz, Lo-Fi, House, Ambient)
    - Real-time MIDI output
    - Effects chain suggestions

    **→ Start in Chord Generator page**
    """)

with col2:
    st.markdown("""
    ### 🎹 Performance Tools
    - **Arpeggiator**: Multiple patterns, rates, swing
    - **Step Sequencer**: 16-step programmable
    - **Pattern Library**: Save/load presets
    - **Live Mode**: Real-time transport control

    **→ Explore performance pages**
    """)

with col3:
    st.markdown("""
    ### 🔌 MIDI Output
    - Virtual MIDI ports
    - Multi-track export (Chords, Bass, Pad)
    - Real-time playback to DAW
    - MIDI clock sync
    - Tempo & time signature control

    **→ Configure in Live page**
    """)

st.divider()

# Quick Start Guide
st.subheader("🚀 Quick Start")

with st.expander("**1. Generate a Chord Progression**", expanded=True):
    st.markdown("""
    1. Go to **🎼 Chord Generator** page
    2. Upload audio file or enter a URL
    3. Click **Analyze** to detect chords and key
    4. Click **Generate Progression** to create AI chords
    5. Export to MIDI or play live
    """)

with st.expander("**2. Add Arpeggiation**"):
    st.markdown("""
    1. Go to **🎹 Arpeggiator** page
    2. Choose pattern (Up, Down, Random, etc.)
    3. Set rate, octaves, and gate
    4. Use progression from Chord Generator
    5. Play arpeggiated output
    """)

with st.expander("**3. Create Sequencer Patterns**"):
    st.markdown("""
    1. Go to **🎵 Sequencer** page
    2. Program 16 steps with notes
    3. Adjust velocity and length per step
    4. Randomize or use presets
    5. Play and loop patterns
    """)

with st.expander("**4. Save & Manage Patterns**"):
    st.markdown("""
    1. Go to **💾 Patterns** page
    2. Save current progression + settings
    3. Browse user patterns and presets
    4. Load patterns instantly
    5. Export to MIDI files
    """)

with st.expander("**5. Live Performance**"):
    st.markdown("""
    1. Go to **🎸 Live** page
    2. Set tempo and MIDI port
    3. Enable modules (Chord/Arp/Seq)
    4. Hit **PLAY** for real-time output
    5. Use quick actions for live changes
    """)

st.divider()

# System Status
st.subheader("📊 System Status")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    # Check MIDI ports
    from chordgen import midi_out
    ports = midi_out.list_ports()
    if ports:
        st.success(f"✅ {len(ports)} MIDI port(s) available")
        for port in ports:
            st.caption(f"  • {port}")
    else:
        st.warning("⚠️ No MIDI ports found")
        st.caption("Create a virtual MIDI port or connect a device")

with status_col2:
    # Check session state
    if 'progression' in st.session_state and st.session_state.progression:
        st.success(f"✅ Progression loaded ({len(st.session_state.progression)} chords)")
    else:
        st.info("ℹ️ No progression loaded")

    if 'arp' in st.session_state:
        st.success("✅ Arpeggiator ready")
    else:
        st.info("ℹ️ Arpeggiator not initialized")

with status_col3:
    if 'sequencer' in st.session_state:
        patterns = len(st.session_state.sequencer.patterns)
        st.success(f"✅ Sequencer ready ({patterns} patterns)")
    else:
        st.info("ℹ️ Sequencer not initialized")

    if 'midi_clock' in st.session_state:
        clock = st.session_state.midi_clock
        st.success(f"✅ Clock: {clock.tempo:.1f} BPM")
    else:
        st.info("ℹ️ Clock not initialized")

st.divider()

# Navigation
st.subheader("🧭 Navigation")

nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)

with nav_col1:
    st.page_link("pages/0_🎼_Chord_Generator.py", label="🎼 Chord Generator", use_container_width=True)

with nav_col2:
    st.page_link("pages/1_🎹_Arpeggiator.py", label="🎹 Arpeggiator", use_container_width=True)

with nav_col3:
    st.page_link("pages/2_🎵_Sequencer.py", label="🎵 Sequencer", use_container_width=True)

with nav_col4:
    st.page_link("pages/3_💾_Patterns.py", label="💾 Patterns", use_container_width=True)

with nav_col5:
    st.page_link("pages/4_🎸_Live.py", label="🎸 Live", use_container_width=True)

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")

    st.markdown("""
    **ChordGen** is a complete MIDI device for:
    - Analyzing music and detecting chords
    - Generating AI-powered progressions
    - Arpeggiation with multiple patterns
    - Step sequencing with 16 steps
    - Real-time MIDI output to your DAW

    **Technologies:**
    - Audio: librosa, soundfile
    - MIDI: mido, python-rtmidi
    - UI: Streamlit
    - ML: Custom HMM, Markov chains
    """)

    st.divider()

    st.markdown("**Quick Links:**")
    st.markdown("- [README](README.md)")
    st.markdown("- [Quick Start](QUICKSTART.md)")
    st.markdown("- [Documentation](PROJECT_SUMMARY.md)")

    st.divider()

    st.caption("ChordGen v1.0 - Full MIDI Device")
    st.caption("Built with Claude Code")
