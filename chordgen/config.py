"""Configuration models and settings."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import yaml


class AudioConfig(BaseModel):
    """Audio processing configuration."""
    sample_rate: int = Field(default=22050, description="Target sample rate")
    mono: bool = Field(default=True, description="Convert to mono")
    duration_limit: Optional[float] = Field(default=180.0, description="Max duration in seconds")


class AnalysisConfig(BaseModel):
    """Analysis configuration."""
    hop_length: int = Field(default=512, description="Hop length for analysis")
    n_fft: int = Field(default=2048, description="FFT size")
    n_chroma: int = Field(default=12, description="Number of chroma bins")


class GenerationConfig(BaseModel):
    """Generation configuration."""
    default_bars: int = Field(default=8, ge=4, le=16, description="Default progression length")
    seed: Optional[int] = Field(default=42, description="Random seed for reproducibility")
    cadence_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="Weight for cadential endings")


class MIDIConfig(BaseModel):
    """MIDI output configuration."""
    default_velocity: int = Field(default=80, ge=0, le=127, description="Default note velocity")
    default_tempo: float = Field(default=120.0, ge=40.0, le=200.0, description="Default tempo (BPM)")
    channel: int = Field(default=0, ge=0, le=15, description="MIDI channel")


class Settings(BaseModel):
    """Global application settings."""
    audio: AudioConfig = Field(default_factory=AudioConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    midi: MIDIConfig = Field(default_factory=MIDIConfig)

    log_level: str = Field(default="INFO", description="Logging level")
    cache_dir: Path = Field(default=Path(".cache"), description="Cache directory")
    export_dir: Path = Field(default=Path("exports"), description="MIDI export directory")

    @classmethod
    def load_from_yaml(cls, path: Path) -> "Settings":
        """Load settings from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def save_to_yaml(cls, path: Path):
        """Save settings to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(self.model_dump(), f)


# Global settings instance
settings = Settings()


def init_directories():
    """Initialize required directories."""
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
