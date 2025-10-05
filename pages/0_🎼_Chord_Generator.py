"""
ChordGen - AI-Powered Chord Progression Generator
Streamlit UI
"""

import streamlit as st
from pathlib import Path
import tempfile
import json

# Initialize before importing modules
from chordgen.config import init_directories, settings
from chordgen.utils import setup_logging

# Setup
init_directories()
setup_logging()

# Now import other modules
from chordgen import audio_io, analysis, chords, generate, midi_out, effects


# Page config
st.set_page_config(
    page_title="ChordGen - AI Chord Progression Generator",
    page_icon="🎹",
    layout="wide"
)

# Initialize session state
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
if 'generated' not in st.session_state:
    st.session_state.generated = False
if 'playing' not in st.session_state:
    st.session_state.playing = False


def main():
    st.title("🎹 ChordGen - AI Chord Progression Generator")
    st.markdown("*Analyze music, detect chords, generate progressions, output MIDI with effects suggestions*")

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Settings")

        # Input source
        input_type = st.radio("Input Source", ["Upload File", "URL (YouTube/SoundCloud)"])

        if input_type == "Upload File":
            uploaded_file = st.file_uploader("Choose audio file", type=['wav', 'mp3', 'flac', 'ogg'])
            audio_source = uploaded_file
        else:
            url_input = st.text_input("Enter URL")
            audio_source = url_input

        st.divider()

        # Generation options
        st.subheader("Generation Options")
        num_bars = st.slider("Bars", 4, 16, 8)
        complexity = st.select_slider("Complexity", options=[0, 1, 2],
                                      format_func=lambda x: ["Basic Triads", "7th Chords", "Extended"][x])
        use_7ths = complexity >= 1

        style_options = ["Auto-detect", "Indie / Synth-Pop", "Neo-Soul / Jazz",
                        "Lo-Fi / Bedroom", "House / Disco", "Ambient"]
        selected_style = st.selectbox("Style", style_options)

        tempo_mode = st.radio("Tempo", ["Auto-detect", "Manual"])
        if tempo_mode == "Manual":
            manual_tempo = st.number_input("BPM", 40.0, 200.0, 120.0, 0.1)
        else:
            manual_tempo = None

        st.divider()

        # MIDI output options
        st.subheader("MIDI Output")
        available_ports = midi_out.list_ports()
        if available_ports:
            selected_port = st.selectbox("MIDI Port", available_ports)
        else:
            st.warning("⚠️ No MIDI ports found")
            selected_port = None

        include_bass = st.checkbox("Include Bass Track", value=True)
        include_pad = st.checkbox("Include Pad Track", value=False)

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📊 Analysis")

        # Analyze button
        can_analyze = (input_type == "Upload File" and uploaded_file) or \
                     (input_type == "URL (YouTube/SoundCloud)" and url_input)

        if st.button("🔍 Analyze", disabled=not can_analyze, use_container_width=True):
            with st.spinner("Analyzing audio..."):
                try:
                    # Load audio
                    if input_type == "Upload File":
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                            tmp.write(uploaded_file.read())
                            tmp_path = tmp.name

                        audio, sr = audio_io.load_audio(Path(tmp_path))
                    else:
                        audio, sr = audio_io.load_or_download(url_input)

                    # Analyze
                    tempo, beats = analysis.detect_tempo_beats(audio, sr)
                    key, mode = analysis.detect_key(audio, sr)
                    chroma = analysis.compute_chroma(audio, sr, beats)

                    # Detect chords
                    detector = chords.ChordDetector(extended=use_7ths)
                    detected_chords = detector.detect(chroma, key, mode)

                    # Create style profile
                    style_profile = generate.create_style_profile_from_analysis(
                        key, mode, tempo, detected_chords
                    )

                    # Store in session state
                    st.session_state.tempo = tempo
                    st.session_state.key = key
                    st.session_state.mode = mode
                    st.session_state.detected_chords = detected_chords
                    st.session_state.style_profile = style_profile
                    st.session_state.analyzed = True

                    st.success("✅ Analysis complete!")

                except Exception as e:
                    st.error(f"❌ Analysis failed: {e}")
                    return

        # Display analysis results
        if st.session_state.analyzed:
            st.subheader("🎵 Detected Properties")

            result_col1, result_col2, result_col3 = st.columns(3)
            with result_col1:
                st.metric("Key", f"{st.session_state.key} {st.session_state.mode}")
            with result_col2:
                st.metric("Tempo", f"{st.session_state.tempo:.1f} BPM")
            with result_col3:
                st.metric("Chords", len(st.session_state.detected_chords))

            # Show chord timeline
            with st.expander("🎼 Detected Chord Timeline"):
                chord_list = [str(c) for c in st.session_state.detected_chords[:16]]  # First 16
                st.write(" → ".join(chord_list))
                if len(st.session_state.detected_chords) > 16:
                    st.caption(f"... and {len(st.session_state.detected_chords) - 16} more")

    with col2:
        st.header("✨ Generation")

        # Generate button
        if st.button("🎲 Generate Progression", disabled=not st.session_state.analyzed, use_container_width=True):
            with st.spinner("Generating progression..."):
                try:
                    # Get tempo
                    tempo_to_use = manual_tempo if manual_tempo else st.session_state.tempo

                    # Update style profile with manual settings
                    profile = st.session_state.style_profile
                    if manual_tempo:
                        profile.tempo = manual_tempo

                    # Generate
                    generator = generate.ProgressionGenerator(profile)
                    progression = generator.generate(bars=num_bars, complexity=complexity)

                    # Store
                    st.session_state.progression = progression
                    st.session_state.final_tempo = tempo_to_use
                    st.session_state.generated = True

                    st.success(f"✅ Generated {len(progression)} chord progression!")

                except Exception as e:
                    st.error(f"❌ Generation failed: {e}")
                    return

        # Display generated progression
        if st.session_state.generated:
            st.subheader("🎼 Generated Progression")

            # Display chords
            prog_text = " | ".join([f"{c.roman} ({c.root}{c.quality})" for c in st.session_state.progression])
            st.code(prog_text, language=None)

            # MIDI Output buttons
            st.subheader("🎛️ MIDI Output")

            button_col1, button_col2 = st.columns(2)

            with button_col1:
                if st.button("▶️ Play to MIDI", disabled=not selected_port, use_container_width=True):
                    try:
                        sender = midi_out.MIDISender(selected_port)
                        st.info(f"Playing to {selected_port}...")

                        # Send progression (non-blocking for now)
                        for chord in st.session_state.progression:
                            sender.send_chord(chord)
                            import time
                            time.sleep(60.0 / st.session_state.final_tempo * chord.duration_beats)
                            sender.stop_all_notes()

                        sender.close()
                        st.success("✅ Playback complete")
                    except Exception as e:
                        st.error(f"❌ MIDI output failed: {e}")

            with button_col2:
                if st.button("💾 Export MIDI", use_container_width=True):
                    try:
                        # Generate filename
                        filename = f"chordgen_{st.session_state.key}_{st.session_state.mode}_{num_bars}bars.mid"
                        output_path = settings.export_dir / filename

                        # Export
                        midi_out.export_midi(
                            st.session_state.progression,
                            output_path,
                            tempo=st.session_state.final_tempo,
                            include_bass=include_bass,
                            include_pad=include_pad
                        )

                        st.success(f"✅ Exported to: `{output_path}`")

                        # Offer download
                        with open(output_path, 'rb') as f:
                            st.download_button(
                                "⬇️ Download MIDI",
                                f.read(),
                                file_name=filename,
                                mime="audio/midi"
                            )

                    except Exception as e:
                        st.error(f"❌ Export failed: {e}")

    # Effects suggestions (full width)
    if st.session_state.analyzed:
        st.divider()
        st.header("🔊 Effects Suggestions")

        # Get recommendations
        recommender = effects.EffectsRecommender()

        auto_style = selected_style if selected_style != "Auto-detect" else None
        recommendations = recommender.recommend(
            style=auto_style,
            tempo=st.session_state.tempo,
            key=st.session_state.key,
            mode=st.session_state.mode
        )

        st.subheader(f"📋 {recommendations['style']} Style")

        # Display in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🎹 Chords Track", "🎸 Bass Track", "🎵 Pad/Lead Track", "📦 JSON"])

        with tab1:
            _display_effects_chain(recommendations['tracks'].get('Chords', []))

        with tab2:
            _display_effects_chain(recommendations['tracks'].get('Bass', []))

        with tab3:
            _display_effects_chain(recommendations['tracks'].get('Pad/Lead', []))

        with tab4:
            st.json(recommendations)

        # Third-party alternatives
        with st.expander("🎛️ Optional Third-Party Alternatives"):
            for category, alts in recommendations.get('third_party_alts', {}).items():
                st.markdown(f"**{category}:**")
                for alt in alts:
                    st.markdown(f"- {alt}")


def _display_effects_chain(chain: list):
    """Display effects chain in a nice format."""
    if not chain:
        st.info("No effects for this track")
        return

    for i, device in enumerate(chain, 1):
        with st.container():
            st.markdown(f"**{i}. {device['device']}**")
            if device.get('params'):
                params_text = " | ".join([f"{k}: {v}" for k, v in device['params'].items()])
                st.caption(params_text)
            st.divider()


if __name__ == "__main__":
    main()
