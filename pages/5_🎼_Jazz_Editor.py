"""Jazz Chord Editor - Edit chord structures and view jazz scales."""

import streamlit as st
from chordgen.jazz_theory import JazzTheory, JazzScale, ChordVoicing, ChordStructure
from chordgen.chords import Chord
from chordgen import midi_out
import time

st.set_page_config(page_title="Jazz Editor", page_icon="🎼", layout="wide")

st.title("🎼 Jazz Chord Editor")
st.markdown("*Edit chord voicings and explore jazz scales*")

# Main layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Chord Builder")

    # Chord input
    root = st.selectbox("Root", JazzTheory.NOTE_NAMES, key="jazz_root")

    quality_options = list(JazzTheory.CHORD_INTERVALS.keys())
    quality = st.selectbox("Quality", quality_options, index=quality_options.index('maj7'), key="jazz_quality")

    # Analyze chord
    chord_structure = JazzTheory.analyze_chord(root, quality, octave=4)

    # Display chord info
    st.markdown("### Chord Structure")

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown(f"**Formula:** {JazzTheory.get_chord_formula(quality)}")
        st.markdown(f"**Notes:** {' - '.join(chord_structure.notes)}")

    with info_col2:
        st.markdown(f"**Scale Degrees:** {' - '.join(chord_structure.scale_degrees)}")
        st.markdown(f"**Intervals:** {chord_structure.intervals}")

    # Available tensions
    st.markdown("### Available Tensions")
    if chord_structure.tensions:
        tensions_str = ', '.join(chord_structure.tensions)
        st.success(f"✅ {tensions_str}")
    else:
        st.info("No typical tensions for this chord")

    # Avoid notes
    if chord_structure.avoid_notes:
        st.warning(f"⚠️ Avoid: {', '.join(chord_structure.avoid_notes)}")

    # Voicing selection
    st.divider()
    st.markdown("### Voicing")

    voicing_options = {
        "Root Position (1-3-5-7)": ChordVoicing.ROOT_POSITION,
        "Drop-2 (1-5-7-3)": ChordVoicing.DROP_2,
        "Drop-3 (1-7-3-5)": ChordVoicing.DROP_3,
        "Drop-2&4": ChordVoicing.DROP_2_4,
        "Rootless A (3-5-7-9)": ChordVoicing.ROOTLESS_A,
        "Rootless B (7-9-3-5)": ChordVoicing.ROOTLESS_B,
        "Shell (1-3-7)": ChordVoicing.SHELL,
        "1st Inversion": ChordVoicing.FIRST_INVERSION,
        "2nd Inversion": ChordVoicing.SECOND_INVERSION,
    }

    selected_voicing_name = st.selectbox("Voicing Type", list(voicing_options.keys()))
    selected_voicing = voicing_options[selected_voicing_name]

    # Apply voicing
    voiced_notes = JazzTheory.apply_voicing(chord_structure.midi_notes, selected_voicing)

    # Display voiced notes
    st.markdown("**Voiced Notes:**")
    voiced_note_names = []
    for note in voiced_notes:
        note_name = JazzTheory.NOTE_NAMES[note % 12]
        octave = (note // 12) - 1
        voiced_note_names.append(f"{note_name}{octave}")

    st.code(' - '.join(voiced_note_names), language=None)

with col2:
    st.subheader("Recommended Scale")

    # Get recommended scale
    rec_scale = chord_structure.recommended_scale
    st.info(f"🎵 **{rec_scale.name.replace('_', ' ').title()}**")

    # Scale selector (allow override)
    scale_options = {scale.name.replace('_', ' ').title(): scale for scale in JazzScale}
    selected_scale_name = st.selectbox(
        "Or choose different scale:",
        list(scale_options.keys()),
        index=list(scale_options.keys()).index(rec_scale.name.replace('_', ' ').title())
    )
    selected_scale = scale_options[selected_scale_name]

    # Display scale
    scale_notes = JazzTheory.get_scale_note_names(root, selected_scale)
    st.markdown("### Scale Notes")
    st.code(' - '.join(scale_notes), language=None)

    # Scale degrees
    st.markdown("### Scale Degrees")
    degrees = ['1', '2', 'b3/3', '4', 'b5/5', '#5/b6', '6/b7', '7']
    scale_degree_str = []

    for i, interval in enumerate(selected_scale.value):
        degree_name = JazzTheory._get_scale_degrees([interval])[0]
        scale_degree_str.append(f"{degree_name}: {scale_notes[i]}")

    st.code('\n'.join(scale_degree_str), language=None)

    # Visualize scale on piano roll
    st.markdown("### Piano Roll")

    # Create simple piano visualization
    piano_notes = []
    for i in range(12):
        note_name = JazzTheory.NOTE_NAMES[i]
        if note_name in scale_notes:
            if note_name == root:
                piano_notes.append(f"**{note_name}** (R)")
            elif note_name in chord_structure.notes:
                piano_notes.append(f"**{note_name}** (C)")
            else:
                piano_notes.append(f"{note_name}")
        else:
            piano_notes.append(f"·")

    st.text(' | '.join(piano_notes))
    st.caption("**R** = Root, **C** = Chord tone, · = Not in scale")

# Progression Editor
st.divider()
st.subheader("📝 Edit Current Progression")

if 'progression' in st.session_state and st.session_state.progression:
    st.markdown(f"**Current Progression ({len(st.session_state.progression)} chords):**")

    # Display as editable grid
    num_chords = len(st.session_state.progression)
    cols_per_row = 4
    num_rows = (num_chords + cols_per_row - 1) // cols_per_row

    for row in range(num_rows):
        cols = st.columns(cols_per_row)

        for col_idx, col in enumerate(cols):
            chord_idx = row * cols_per_row + col_idx

            if chord_idx < num_chords:
                chord = st.session_state.progression[chord_idx]

                with col:
                    with st.container():
                        st.markdown(f"**Chord {chord_idx + 1}**")

                        # Edit root
                        new_root = st.selectbox(
                            "Root",
                            JazzTheory.NOTE_NAMES,
                            index=JazzTheory.NOTE_NAMES.index(chord.root) if chord.root in JazzTheory.NOTE_NAMES else 0,
                            key=f"root_{chord_idx}"
                        )

                        # Edit quality
                        new_quality = st.selectbox(
                            "Quality",
                            quality_options,
                            index=quality_options.index(chord.quality) if chord.quality in quality_options else 0,
                            key=f"quality_{chord_idx}"
                        )

                        # Update chord
                        if new_root != chord.root or new_quality != chord.quality:
                            st.session_state.progression[chord_idx].root = new_root
                            st.session_state.progression[chord_idx].quality = new_quality

                        # Show chord formula
                        formula = JazzTheory.get_chord_formula(new_quality)
                        st.caption(f"{formula}")

    # Actions
    st.divider()
    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:
        if st.button("🎹 Play Progression", use_container_width=True):
            available_ports = midi_out.list_ports()
            if available_ports:
                try:
                    port = available_ports[0]
                    sender = midi_out.MIDISender(port)
                    tempo = st.session_state.get('final_tempo', 120.0)
                    beat_duration = 60.0 / tempo

                    for chord in st.session_state.progression:
                        # Use current voicing
                        structure = JazzTheory.analyze_chord(chord.root, chord.quality)
                        voiced = JazzTheory.apply_voicing(structure.midi_notes, selected_voicing)

                        # Play chord
                        for note in voiced:
                            sender.send_note(note, 90)

                        time.sleep(beat_duration * 2)

                        # Note off
                        for note in voiced:
                            sender.send_note(note, 0)

                        time.sleep(beat_duration * 0.5)

                    sender.close()
                    st.success("✅ Played progression!")
                except Exception as e:
                    st.error(f"❌ Playback failed: {e}")
            else:
                st.warning("No MIDI ports available")

    with action_col2:
        if st.button("💾 Save Changes", use_container_width=True):
            st.success("Changes saved to session!")
            st.rerun()

    with action_col3:
        if st.button("🔄 Revert Changes", use_container_width=True):
            st.rerun()

else:
    st.info("Generate a progression in the Chord Generator first")

# Scale Reference
with st.sidebar:
    st.header("🎵 Scale Reference")

    st.markdown("""
    ### Common Jazz Scales

    **Modal Scales:**
    - Dorian: Natural minor with raised 6th
    - Mixolydian: Major with b7
    - Lydian: Major with #11

    **Melodic Minor Modes:**
    - Lydian Dominant: For alt chords
    - Altered: For 7alt chords
    - Locrian #2: For half-diminished

    **Symmetric:**
    - Whole Tone: Augmented chords
    - Diminished: Diminished 7th
    - Whole-Half Dim: Dominant 7

    **Bebop:**
    - Bebop Major: Passing tones
    - Bebop Dominant: For ii-V-I
    """)

    st.divider()

    st.markdown("""
    ### Chord-Scale Relationships

    **Major 7th:** Ionian, Lydian
    **Dominant 7th:** Mixolydian, Lydian Dominant
    **Minor 7th:** Dorian, Aeolian
    **Half-Diminished:** Locrian, Locrian #2
    **Diminished:** Whole-Half Diminished
    """)
