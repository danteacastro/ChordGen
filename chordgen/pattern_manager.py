"""Pattern storage, management, and preset library."""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import json
import yaml
from datetime import datetime
from .chords import Chord
from .sequencer import SequencerPattern
from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Complete pattern including chords, arp, and sequencer settings."""
    name: str
    chords: List[Dict]  # Serialized chords
    tempo: float = 120.0
    key: str = "C"
    mode: str = "major"

    # Arp settings
    arp_pattern: str = "up"
    arp_rate: str = "eighth"
    arp_octaves: int = 1
    arp_gate: float = 0.75
    arp_swing: float = 0.0

    # Sequencer data
    sequencer_patterns: Dict[str, Dict] = None

    # Metadata
    created: str = ""
    modified: str = ""
    tags: List[str] = None

    def __post_init__(self):
        if self.created == "":
            self.created = datetime.now().isoformat()
        if self.modified == "":
            self.modified = self.created
        if self.tags is None:
            self.tags = []
        if self.sequencer_patterns is None:
            self.sequencer_patterns = {}


class PatternManager:
    """
    Manage patterns: save, load, organize, and provide presets.
    """

    def __init__(self, patterns_dir: Path = None):
        """
        Initialize pattern manager.

        Args:
            patterns_dir: Directory for user patterns
        """
        self.patterns_dir = patterns_dir or Path("patterns")
        self.user_dir = self.patterns_dir / "user"
        self.presets_dir = self.patterns_dir / "presets"

        # Create directories
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.presets_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Pattern manager initialized: {self.patterns_dir}")

    def save_pattern(
        self,
        pattern: Pattern,
        filename: Optional[str] = None,
        to_presets: bool = False
    ) -> Path:
        """
        Save pattern to file.

        Args:
            pattern: Pattern to save
            filename: Optional filename (generated from name if not provided)
            to_presets: Save to presets dir instead of user dir

        Returns:
            Path to saved file
        """
        # Update modified time
        pattern.modified = datetime.now().isoformat()

        # Generate filename
        if filename is None:
            safe_name = "".join(c if c.isalnum() or c in "_ -" else "_" for c in pattern.name)
            filename = f"{safe_name}.json"

        # Choose directory
        save_dir = self.presets_dir if to_presets else self.user_dir
        filepath = save_dir / filename

        # Save as JSON
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(pattern), f, indent=2)
            logger.info(f"Saved pattern: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save pattern: {e}")
            raise

    def load_pattern(self, filepath: Path) -> Pattern:
        """
        Load pattern from file.

        Args:
            filepath: Path to pattern file

        Returns:
            Pattern object
        """
        try:
            with open(filepath) as f:
                data = json.load(f)
            pattern = Pattern(**data)
            logger.info(f"Loaded pattern: {filepath}")
            return pattern
        except Exception as e:
            logger.error(f"Failed to load pattern: {e}")
            raise

    def list_user_patterns(self) -> List[Path]:
        """List all user patterns."""
        return sorted(self.user_dir.glob("*.json"))

    def list_presets(self) -> List[Path]:
        """List all preset patterns."""
        return sorted(self.presets_dir.glob("*.json"))

    def delete_pattern(self, filepath: Path):
        """Delete a pattern file."""
        try:
            filepath.unlink()
            logger.info(f"Deleted pattern: {filepath}")
        except Exception as e:
            logger.error(f"Failed to delete pattern: {e}")
            raise

    def export_to_midi(self, pattern: Pattern, output_path: Path):
        """
        Export pattern as MIDI file.

        Args:
            pattern: Pattern to export
            output_path: MIDI file path
        """
        from . import midi_out
        from .chords import Chord

        # Reconstruct chords from dict
        chords = []
        for chord_data in pattern.chords:
            chord = Chord(**chord_data)
            chords.append(chord)

        # Export
        midi_out.export_midi(
            chords,
            output_path,
            tempo=pattern.tempo,
            include_bass=True,
            include_pad=True
        )
        logger.info(f"Exported pattern to MIDI: {output_path}")

    def create_preset_library(self):
        """Create default preset patterns."""
        presets = [
            Pattern(
                name="Classic ii-V-I",
                chords=[
                    {"root": "D", "quality": "min7", "roman": "ii"},
                    {"root": "G", "quality": "dom7", "roman": "V"},
                    {"root": "C", "quality": "maj7", "roman": "I"},
                ],
                key="C",
                mode="major",
                tempo=120,
                arp_pattern="up",
                tags=["jazz", "progression"]
            ),
            Pattern(
                name="Pop Progression",
                chords=[
                    {"root": "C", "quality": "maj", "roman": "I"},
                    {"root": "G", "quality": "maj", "roman": "V"},
                    {"root": "A", "quality": "min", "roman": "vi"},
                    {"root": "F", "quality": "maj", "roman": "IV"},
                ],
                key="C",
                mode="major",
                tempo=115,
                arp_pattern="updown",
                tags=["pop", "progression"]
            ),
            Pattern(
                name="Minor Groove",
                chords=[
                    {"root": "A", "quality": "min7", "roman": "i"},
                    {"root": "D", "quality": "min7", "roman": "iv"},
                    {"root": "E", "quality": "dom7", "roman": "V"},
                    {"root": "A", "quality": "min7", "roman": "i"},
                ],
                key="A",
                mode="minor",
                tempo=95,
                arp_pattern="random",
                tags=["minor", "groove"]
            ),
        ]

        for preset in presets:
            self.save_pattern(preset, to_presets=True)

        logger.info(f"Created {len(presets)} preset patterns")

    def search_patterns(
        self,
        query: str = "",
        tags: List[str] = None,
        key: str = None,
        mode: str = None
    ) -> List[Pattern]:
        """
        Search patterns by various criteria.

        Args:
            query: Text search in name
            tags: Filter by tags
            key: Filter by key
            mode: Filter by mode

        Returns:
            List of matching patterns
        """
        results = []

        # Search both user and presets
        all_files = list(self.user_dir.glob("*.json")) + list(self.presets_dir.glob("*.json"))

        for filepath in all_files:
            try:
                pattern = self.load_pattern(filepath)

                # Apply filters
                if query and query.lower() not in pattern.name.lower():
                    continue
                if tags and not any(t in pattern.tags for t in tags):
                    continue
                if key and pattern.key != key:
                    continue
                if mode and pattern.mode != mode:
                    continue

                results.append(pattern)

            except Exception as e:
                logger.warning(f"Error loading {filepath}: {e}")

        logger.info(f"Search found {len(results)} patterns")
        return results

    def get_pattern_info(self, filepath: Path) -> Dict:
        """Get pattern metadata without full load."""
        try:
            with open(filepath) as f:
                data = json.load(f)
            return {
                "name": data.get("name", "Unknown"),
                "key": data.get("key", "C"),
                "mode": data.get("mode", "major"),
                "tempo": data.get("tempo", 120),
                "num_chords": len(data.get("chords", [])),
                "tags": data.get("tags", []),
                "modified": data.get("modified", ""),
            }
        except Exception as e:
            logger.error(f"Error reading pattern info: {e}")
            return {}
