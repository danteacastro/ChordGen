"""Audio input/output: download from URLs or load local files."""

import logging
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
import soundfile as sf
import librosa
from .config import settings
from .utils import timing_decorator, cache

logger = logging.getLogger(__name__)


@timing_decorator
def download_audio(url: str, output_path: Optional[Path] = None) -> Path:
    """
    Download audio from YouTube or SoundCloud URL.

    Args:
        url: YouTube or SoundCloud URL
        output_path: Optional output path (defaults to cache)

    Returns:
        Path to downloaded audio file

    Raises:
        RuntimeError: If download fails
    """
    import yt_dlp

    if output_path is None:
        output_path = settings.cache_dir / "downloaded_audio.wav"

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': str(output_path.with_suffix('')),
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading from {url}")
            ydl.download([url])
            logger.info(f"Download complete: {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"Failed to download audio: {e}")
        raise RuntimeError(f"Download failed: {e}")


@timing_decorator
def load_audio(
    path: Path,
    sr: Optional[int] = None,
    mono: Optional[bool] = None,
    duration: Optional[float] = None,
    offset: float = 0.0
) -> Tuple[np.ndarray, int]:
    """
    Load audio file and resample.

    Args:
        path: Path to audio file (WAV, MP3, FLAC, etc.)
        sr: Target sample rate (defaults to config)
        mono: Convert to mono (defaults to config)
        duration: Maximum duration to load in seconds
        offset: Start offset in seconds

    Returns:
        Tuple of (audio_data, sample_rate)

    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If loading fails
    """
    if sr is None:
        sr = settings.audio.sample_rate
    if mono is None:
        mono = settings.audio.mono
    if duration is None:
        duration = settings.audio.duration_limit

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        logger.info(f"Loading audio: {path}")
        audio, orig_sr = librosa.load(
            path,
            sr=sr,
            mono=mono,
            duration=duration,
            offset=offset
        )
        logger.info(f"Loaded {len(audio)/sr:.1f}s at {sr}Hz")
        return audio, sr

    except Exception as e:
        logger.error(f"Failed to load audio: {e}")
        raise RuntimeError(f"Audio loading failed: {e}")


def save_audio(audio: np.ndarray, sr: int, path: Path):
    """
    Save audio to file.

    Args:
        audio: Audio data
        sr: Sample rate
        path: Output path
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        sf.write(path, audio, sr)
        logger.info(f"Saved audio: {path}")
    except Exception as e:
        logger.error(f"Failed to save audio: {e}")
        raise RuntimeError(f"Audio saving failed: {e}")


def get_audio_info(path: Path) -> dict:
    """
    Get audio file metadata.

    Args:
        path: Path to audio file

    Returns:
        Dictionary with duration, sample_rate, channels
    """
    try:
        info = sf.info(path)
        return {
            "duration": info.duration,
            "sample_rate": info.samplerate,
            "channels": info.channels,
            "format": info.format,
        }
    except Exception as e:
        logger.error(f"Failed to read audio info: {e}")
        return {}


def is_valid_url(url: str) -> bool:
    """Check if URL is likely a valid audio source."""
    valid_domains = [
        "youtube.com", "youtu.be",
        "soundcloud.com", "snd.sc",
    ]
    return any(domain in url.lower() for domain in valid_domains)


@timing_decorator
def load_or_download(source: str) -> Tuple[np.ndarray, int]:
    """
    Load audio from file or download from URL.

    Args:
        source: File path or URL

    Returns:
        Tuple of (audio_data, sample_rate)
    """
    # Check if it's a URL
    if is_valid_url(source):
        audio_path = download_audio(source)
        return load_audio(audio_path)

    # Treat as local file
    return load_audio(Path(source))
