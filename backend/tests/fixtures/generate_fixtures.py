"""Generate synthetic audio fixtures for testing."""

import os

import numpy as np
import soundfile as sf

FIXTURES_DIR = os.path.dirname(__file__)


def generate_sine_wav(
    filename: str,
    duration: float = 2.0,
    sample_rate: int = 44100,
    frequency: float = 440.0,
    channels: int = 1,
) -> str:
    """Generate a sine wave WAV file."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    signal = 0.5 * np.sin(2 * np.pi * frequency * t)
    if channels == 2:
        signal = np.column_stack([signal, signal])
    path = os.path.join(FIXTURES_DIR, filename)
    sf.write(path, signal, sample_rate)
    return path


def generate_silent_wav(
    filename: str, duration: float = 1.0, sample_rate: int = 44100
) -> str:
    """Generate a silent WAV file."""
    signal = np.zeros(int(sample_rate * duration))
    path = os.path.join(FIXTURES_DIR, filename)
    sf.write(path, signal, sample_rate)
    return path


if __name__ == "__main__":
    generate_sine_wav("test_mono.wav", duration=2.0, channels=1)
    generate_sine_wav("test_stereo.wav", duration=2.0, channels=2)
    generate_sine_wav("test_high_sr.wav", duration=1.0, sample_rate=48000)
    generate_silent_wav("test_silent.wav", duration=1.0)
    print("Fixtures generated.")
