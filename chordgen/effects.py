"""Ableton effects chain recommendations based on detected style."""

import logging
from typing import Dict, List
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


# Default effects chains for different styles
DEFAULT_EFFECTS = {
    "Indie / Synth-Pop": {
        "Chords": [
            {"device": "EQ Eight", "params": {"HP": 60, "shelf_high": "+2 dB @ 8k"}},
            {"device": "Chorus-Ensemble", "params": {"amount": 35, "rate": 0.8}},
            {"device": "Compressor", "params": {"ratio": 2.5, "threshold": -18, "attack_ms": 5, "release_ms": 100}},
            {"device": "Reverb", "params": {"size": 55, "pre_delay_ms": 15, "wet": 18, "decay_ms": 1200}},
        ],
        "Bass": [
            {"device": "EQ Eight", "params": {"LP": 120, "notch": "250 Hz -2 dB", "HP": 40}},
            {"device": "Saturator", "params": {"drive": 3.0, "soft_clip": True}},
            {"device": "Glue Compressor", "params": {"attack_ms": 3, "release_ms": 100, "ratio": 3.0, "makeup": 2}},
        ],
        "Pad/Lead": [
            {"device": "Auto Filter", "params": {"mode": "LP", "freq_Hz": 2000, "resonance": 10, "LFO_rate_Hz": 0.25}},
            {"device": "Delay", "params": {"sync": "1/4", "feedback": 35, "wet": 20}},
            {"device": "Reverb", "params": {"size": 70, "wet": 22, "decay_ms": 1800}},
        ],
    },
    "Neo-Soul / Jazz": {
        "Chords": [
            {"device": "EQ Eight", "params": {"HP": 80, "bell": "+1.5 dB @ 2k"}},
            {"device": "Compressor", "params": {"ratio": 1.8, "threshold": -20, "attack_ms": 10, "release_ms": 150}},
            {"device": "Echo", "params": {"delay_L_ms": 375, "delay_R_ms": 500, "feedback": 15, "wet": 12}},
            {"device": "Reverb", "params": {"size": 45, "wet": 15, "decay_ms": 1000}},
        ],
        "Bass": [
            {"device": "EQ Eight", "params": {"LP": 100, "boost": "+3 dB @ 80 Hz", "HP": 35}},
            {"device": "Saturator", "params": {"drive": 2.0, "analog_clip": True}},
            {"device": "Compressor", "params": {"ratio": 4.0, "threshold": -22, "attack_ms": 5, "release_ms": 80}},
        ],
        "Pad/Lead": [
            {"device": "EQ Eight", "params": {"HP": 200, "shelf_high": "+1 dB @ 6k"}},
            {"device": "Phaser", "params": {"rate_Hz": 0.15, "feedback": 30, "poles": 8}},
            {"device": "Delay", "params": {"sync": "1/8 dotted", "feedback": 25, "wet": 15}},
            {"device": "Reverb", "params": {"size": 60, "wet": 20, "decay_ms": 1500}},
        ],
    },
    "Lo-Fi / Bedroom": {
        "Chords": [
            {"device": "EQ Eight", "params": {"LP": 800, "HP": 100, "notch": "500 Hz -3 dB"}},
            {"device": "Redux", "params": {"bit_depth": 12, "sample_reduce": 4}},
            {"device": "Vinyl Distortion", "params": {"tracing_model": "70s", "crackle": 0.35}},
            {"device": "Reverb", "params": {"size": 40, "wet": 25, "decay_ms": 800}},
        ],
        "Bass": [
            {"device": "EQ Eight", "params": {"LP": 120, "boost": "+4 dB @ 60 Hz"}},
            {"device": "Saturator", "params": {"drive": 5.0, "soft_clip": True, "color": "warm"}},
            {"device": "Compressor", "params": {"ratio": 6.0, "threshold": -20, "release_ms": 60}},
        ],
        "Pad/Lead": [
            {"device": "EQ Eight", "params": {"HP": 300, "LP": 5000}},
            {"device": "Chorus", "params": {"rate": 1.2, "amount": 40}},
            {"device": "Delay", "params": {"delay_L_ms": 450, "delay_R_ms": 600, "feedback": 40, "wet": 30}},
        ],
    },
    "House / Disco": {
        "Chords": [
            {"device": "EQ Eight", "params": {"HP": 100, "shelf_high": "+2.5 dB @ 10k"}},
            {"device": "Compressor", "params": {"ratio": 3.0, "threshold": -16, "attack_ms": 3, "release_ms": 80}},
            {"device": "Flanger", "params": {"rate_Hz": 0.3, "feedback": 20}},
            {"device": "Reverb", "params": {"size": 50, "wet": 14, "decay_ms": 1100}},
        ],
        "Bass": [
            {"device": "EQ Eight", "params": {"LP": 90, "boost": "+5 dB @ 50 Hz", "HP": 30}},
            {"device": "Saturator", "params": {"drive": 4.0, "analog_clip": True}},
            {"device": "Glue Compressor", "params": {"attack_ms": 1, "release_ms": 60, "ratio": 4.0, "makeup": 3}},
            {"device": "Sidechain Compressor", "params": {"ratio": 8.0, "threshold": -24, "attack_ms": 1}},
        ],
        "Pad/Lead": [
            {"device": "Auto Filter", "params": {"mode": "LP", "freq_Hz": 3000, "LFO_sync": "1/2", "LFO_amt": 40}},
            {"device": "Delay", "params": {"sync": "1/16", "feedback": 30, "wet": 18, "ping_pong": True}},
            {"device": "Reverb", "params": {"size": 65, "wet": 16, "decay_ms": 1400}},
        ],
    },
    "Ambient": {
        "Chords": [
            {"device": "EQ Eight", "params": {"HP": 50, "shelf_high": "+1 dB @ 12k"}},
            {"device": "Reverb", "params": {"size": 90, "wet": 40, "decay_ms": 4000, "freeze": False}},
            {"device": "Delay", "params": {"delay_L_ms": 800, "delay_R_ms": 1200, "feedback": 50, "wet": 35}},
            {"device": "Compressor", "params": {"ratio": 1.5, "threshold": -24, "attack_ms": 50, "release_ms": 300}},
        ],
        "Bass": [
            {"device": "EQ Eight", "params": {"LP": 150, "HP": 45}},
            {"device": "Saturator", "params": {"drive": 1.5, "soft_clip": True}},
            {"device": "Compressor", "params": {"ratio": 2.0, "threshold": -20, "release_ms": 200}},
        ],
        "Pad/Lead": [
            {"device": "EQ Eight", "params": {"HP": 400, "shelf_high": "+2 dB @ 8k"}},
            {"device": "Auto Pan", "params": {"rate_Hz": 0.1, "amount": 30}},
            {"device": "Delay", "params": {"delay_L_ms": 1000, "delay_R_ms": 1500, "feedback": 60, "wet": 45}},
            {"device": "Reverb", "params": {"size": 95, "wet": 50, "decay_ms": 6000}},
        ],
    },
}


# Third-party alternatives
THIRD_PARTY_ALTERNATIVES = {
    "Reverb": [
        "Valhalla VintageVerb: Plate 80s, Decay 1.6s, Mix 18%",
        "FabFilter Pro-R: Space preset, Size 40%, Decay 1.2s",
    ],
    "Saturation": [
        "Soundtoys Decapitator: Style E (Neve), Drive 2-4",
        "FabFilter Saturn: Tape mode, Drive 30-50%",
    ],
    "Delay": [
        "Valhalla Delay: Mod Delay, Time 1/4, Feedback 30%",
        "Soundtoys EchoBoy: ModEcho mode",
    ],
    "Compression": [
        "FabFilter Pro-C 2: Vocal preset, adjust threshold",
        "Waves CLA-76: All buttons mode (4:1)",
    ],
}


class EffectsRecommender:
    """Recommend Ableton effects chains based on musical style."""

    def __init__(self, effects_yaml: Path = None):
        """
        Initialize recommender.

        Args:
            effects_yaml: Optional path to custom effects YAML
        """
        self.effects_db = DEFAULT_EFFECTS.copy()

        if effects_yaml and Path(effects_yaml).exists():
            self._load_effects_yaml(effects_yaml)

    def _load_effects_yaml(self, path: Path):
        """Load custom effects from YAML file."""
        try:
            with open(path) as f:
                custom = yaml.safe_load(f)
                self.effects_db.update(custom)
            logger.info(f"Loaded custom effects from {path}")
        except Exception as e:
            logger.warning(f"Failed to load effects YAML: {e}")

    def recommend(
        self,
        style: str = None,
        tempo: float = 120,
        key: str = "C",
        mode: str = "major"
    ) -> Dict:
        """
        Get effects recommendations.

        Args:
            style: Musical style (auto-detected or user-specified)
            tempo: Tempo in BPM (affects delay timings)
            key: Musical key
            mode: Major or minor

        Returns:
            Dictionary with effects chains per track
        """
        # Auto-detect style if not provided
        if style is None:
            style = self._auto_detect_style(tempo, mode)

        # Get effects for style (fallback to Indie if unknown)
        if style not in self.effects_db:
            logger.warning(f"Unknown style '{style}', using Indie / Synth-Pop")
            style = "Indie / Synth-Pop"

        effects = self.effects_db[style]

        result = {
            "style": style,
            "tempo": tempo,
            "key": f"{key} {mode}",
            "tracks": effects,
            "third_party_alts": THIRD_PARTY_ALTERNATIVES,
        }

        logger.info(f"Generated effects recommendations for {style}")
        return result

    def _auto_detect_style(self, tempo: float, mode: str) -> str:
        """
        Auto-detect style from tempo and mode.

        Args:
            tempo: BPM
            mode: major or minor

        Returns:
            Style name
        """
        # Simple heuristic-based detection
        if tempo < 80:
            return "Ambient"
        elif tempo < 100:
            if mode == "minor":
                return "Lo-Fi / Bedroom"
            return "Neo-Soul / Jazz"
        elif tempo < 115:
            return "Indie / Synth-Pop"
        elif tempo >= 120:
            return "House / Disco"
        else:
            return "Indie / Synth-Pop"

    def format_for_display(self, recommendations: Dict) -> str:
        """
        Format recommendations as readable text.

        Args:
            recommendations: Output from recommend()

        Returns:
            Formatted string
        """
        lines = []
        lines.append(f"## Effects Suggestions for {recommendations['style']}\n")
        lines.append(f"**Key:** {recommendations['key']} | **Tempo:** {recommendations['tempo']} BPM\n")

        for track_name, chain in recommendations['tracks'].items():
            lines.append(f"\n### {track_name} Track\n")
            for i, device in enumerate(chain, 1):
                lines.append(f"{i}. **{device['device']}**")
                if device.get('params'):
                    params = ", ".join(f"{k}: {v}" for k, v in device['params'].items())
                    lines.append(f"   - {params}")

        lines.append("\n### Optional Third-Party Alternatives\n")
        for category, alts in recommendations['third_party_alts'].items():
            lines.append(f"**{category}:**")
            for alt in alts:
                lines.append(f"- {alt}")

        return "\n".join(lines)
