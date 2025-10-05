"""Pattern Library - Save, load, and manage patterns."""

import streamlit as st
from pathlib import Path
from chordgen.pattern_manager import PatternManager, Pattern
from chordgen.chords import Chord
from dataclasses import asdict
import json

st.set_page_config(page_title="Pattern Library", page_icon="💾", layout="wide")

# Initialize pattern manager
if 'pattern_manager' not in st.session_state:
    st.session_state.pattern_manager = PatternManager(
        Path("/home/dante/Documents/Projects/ChordGen/patterns")
    )

st.title("💾 Pattern Library")
st.markdown("*Save, load, and organize your musical patterns*")

# Main layout
tab1, tab2, tab3 = st.tabs(["📚 Browse", "💾 Save", "🔧 Manage"])

with tab1:
    st.subheader("Browse Patterns")

    # Filter options
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        search_query = st.text_input("🔍 Search", placeholder="Pattern name...")

    with filter_col2:
        filter_key = st.selectbox("Filter by Key", ["All"] + ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])

    with filter_col3:
        filter_mode = st.selectbox("Filter by Mode", ["All", "major", "minor"])

    # List patterns
    user_patterns = st.session_state.pattern_manager.list_user_patterns()
    preset_patterns = st.session_state.pattern_manager.list_presets()

    st.markdown("### 👤 My Patterns")

    if user_patterns:
        for pattern_file in user_patterns:
            info = st.session_state.pattern_manager.get_pattern_info(pattern_file)

            # Apply filters
            if search_query and search_query.lower() not in info['name'].lower():
                continue
            if filter_key != "All" and info['key'] != filter_key:
                continue
            if filter_mode != "All" and info['mode'] != filter_mode:
                continue

            with st.expander(f"**{info['name']}** - {info['key']} {info['mode']} @ {info['tempo']} BPM"):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.caption(f"Chords: {info['num_chords']} | Modified: {info['modified'][:10]}")
                    if info['tags']:
                        st.caption(f"Tags: {', '.join(info['tags'])}")

                with col2:
                    if st.button("📥 Load", key=f"load_{pattern_file.name}", use_container_width=True):
                        try:
                            pattern = st.session_state.pattern_manager.load_pattern(pattern_file)

                            # Load into session state
                            st.session_state.current_pattern = pattern
                            st.session_state.key = pattern.key
                            st.session_state.mode = pattern.mode
                            st.session_state.tempo = pattern.tempo

                            # Reconstruct chords
                            chords = [Chord(**c) for c in pattern.chords]
                            st.session_state.progression = chords

                            st.success(f"✅ Loaded: {pattern.name}")
                        except Exception as e:
                            st.error(f"❌ Load failed: {e}")

                with col3:
                    if st.button("🗑️ Delete", key=f"del_{pattern_file.name}", use_container_width=True):
                        st.session_state.pattern_manager.delete_pattern(pattern_file)
                        st.success("Deleted!")
                        st.rerun()
    else:
        st.info("No user patterns yet. Create one in the Save tab!")

    st.divider()
    st.markdown("### 🎼 Presets")

    if preset_patterns:
        for pattern_file in preset_patterns:
            info = st.session_state.pattern_manager.get_pattern_info(pattern_file)

            with st.expander(f"**{info['name']}** - {info['key']} {info['mode']} @ {info['tempo']} BPM"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.caption(f"Chords: {info['num_chords']}")
                    if info['tags']:
                        st.caption(f"Tags: {', '.join(info['tags'])}")

                with col2:
                    if st.button("📥 Load", key=f"load_preset_{pattern_file.name}", use_container_width=True):
                        pattern = st.session_state.pattern_manager.load_pattern(pattern_file)
                        st.session_state.current_pattern = pattern
                        st.session_state.key = pattern.key
                        st.session_state.mode = pattern.mode
                        st.session_state.tempo = pattern.tempo
                        chords = [Chord(**c) for c in pattern.chords]
                        st.session_state.progression = chords
                        st.success(f"✅ Loaded: {pattern.name}")
    else:
        st.info("No presets found. Create some!")
        if st.button("🔧 Create Default Presets"):
            st.session_state.pattern_manager.create_preset_library()
            st.success("Created default presets!")
            st.rerun()

with tab2:
    st.subheader("💾 Save Current Pattern")

    # Check if we have a progression
    if 'progression' in st.session_state and st.session_state.progression:
        # Pattern name
        pattern_name = st.text_input("Pattern Name", placeholder="My Awesome Progression")

        # Metadata
        col1, col2 = st.columns(2)
        with col1:
            save_key = st.session_state.get('key', 'C')
            save_mode = st.session_state.get('mode', 'major')
            save_tempo = st.session_state.get('final_tempo', 120.0)

        with col2:
            tags_input = st.text_input("Tags (comma-separated)", placeholder="indie, chill, progression")
            tags = [t.strip() for t in tags_input.split(',')] if tags_input else []

        # Arpeggiator settings (if available)
        if 'arp' in st.session_state:
            arp_pattern = st.session_state.arp.pattern.value
            arp_rate = st.session_state.arp.rate.name.lower()
            arp_octaves = st.session_state.arp.octaves
            arp_gate = st.session_state.arp.gate
            arp_swing = st.session_state.arp.swing
        else:
            arp_pattern = "up"
            arp_rate = "eighth"
            arp_octaves = 1
            arp_gate = 0.75
            arp_swing = 0.0

        # Sequencer patterns (if available)
        sequencer_data = {}
        if 'sequencer' in st.session_state:
            for name, pattern in st.session_state.sequencer.patterns.items():
                sequencer_data[name] = {
                    'steps': [asdict(step) for step in pattern.steps],
                    'length': pattern.length
                }

        # Preview
        st.markdown("**Preview:**")
        prog_chords = st.session_state.progression
        chord_str = " → ".join([f"{c.root}{c.quality}" for c in prog_chords[:8]])
        st.code(chord_str + ("..." if len(prog_chords) > 8 else ""), language=None)

        # Save options
        save_col1, save_col2 = st.columns(2)

        with save_col1:
            save_to_presets = st.checkbox("Save as Preset")

        with save_col2:
            if st.button("💾 Save Pattern", use_container_width=True):
                if not pattern_name:
                    st.error("Please enter a pattern name")
                else:
                    try:
                        # Create pattern
                        pattern = Pattern(
                            name=pattern_name,
                            chords=[asdict(c) for c in st.session_state.progression],
                            tempo=save_tempo,
                            key=save_key,
                            mode=save_mode,
                            arp_pattern=arp_pattern,
                            arp_rate=arp_rate,
                            arp_octaves=arp_octaves,
                            arp_gate=arp_gate,
                            arp_swing=arp_swing,
                            sequencer_patterns=sequencer_data,
                            tags=tags
                        )

                        # Save
                        filepath = st.session_state.pattern_manager.save_pattern(
                            pattern,
                            to_presets=save_to_presets
                        )

                        st.success(f"✅ Saved: {filepath}")

                    except Exception as e:
                        st.error(f"❌ Save failed: {e}")

    else:
        st.info("Generate a progression in the Chord Generator first")

with tab3:
    st.subheader("🔧 Manage Library")

    manage_col1, manage_col2 = st.columns(2)

    with manage_col1:
        st.markdown("**Library Stats**")
        user_count = len(st.session_state.pattern_manager.list_user_patterns())
        preset_count = len(st.session_state.pattern_manager.list_presets())

        st.metric("User Patterns", user_count)
        st.metric("Preset Patterns", preset_count)

    with manage_col2:
        st.markdown("**Actions**")

        if st.button("🔄 Refresh Library", use_container_width=True):
            st.rerun()

        if st.button("📦 Create Default Presets", use_container_width=True):
            st.session_state.pattern_manager.create_preset_library()
            st.success("Presets created!")
            st.rerun()

    # Export current pattern to MIDI
    st.divider()
    st.subheader("📤 Export")

    if 'current_pattern' in st.session_state:
        pattern = st.session_state.current_pattern

        export_filename = st.text_input(
            "MIDI Filename",
            value=f"{pattern.name.replace(' ', '_')}.mid"
        )

        if st.button("📤 Export to MIDI", use_container_width=True):
            try:
                export_path = Path("/home/dante/Documents/Projects/ChordGen/exports") / export_filename
                export_path.parent.mkdir(exist_ok=True)

                st.session_state.pattern_manager.export_to_midi(pattern, export_path)

                st.success(f"✅ Exported: {export_path}")

                # Offer download
                with open(export_path, 'rb') as f:
                    st.download_button(
                        "⬇️ Download MIDI",
                        f.read(),
                        file_name=export_filename,
                        mime="audio/midi"
                    )

            except Exception as e:
                st.error(f"❌ Export failed: {e}")
    else:
        st.info("Load a pattern first to export it")

# Sidebar info
with st.sidebar:
    st.header("📖 About Patterns")

    st.markdown("""
    Patterns store:
    - Chord progressions
    - Arpeggiator settings
    - Sequencer data
    - Tempo & key info
    - Custom tags

    **File Format:** JSON
    **Location:** `patterns/user/` or `patterns/presets/`
    """)
