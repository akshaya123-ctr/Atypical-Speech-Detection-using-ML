import numpy as np
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from preprocessing.audio_pipeline import clean_audio

def test_clean_audio_synthetic():
    sr = 16000
    t = np.linspace(0, 1.0, sr)
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)
    noise = 0.05 * np.random.randn(sr)
    audio = (signal + noise).astype(np.float32)
    
    cleaned = clean_audio(audio, sr)
    assert isinstance(cleaned, np.ndarray)
    assert len(cleaned) > 0
    assert np.max(np.abs(cleaned)) <= 1.0
