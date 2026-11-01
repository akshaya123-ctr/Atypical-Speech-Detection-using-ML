import os
import librosa
import numpy as np
import noisereduce as nr

def clean_audio(y: np.ndarray, sr: int) -> np.ndarray:
    """
    Unified audio preprocessing pipeline used for BOTH training and live inference.
    1. Silence trimming
    2. Non-stationary noise reduction
    3. Peak / RMS loudness normalization
    """
    if y is None or len(y) == 0:
        return np.array([], dtype=np.float32)
        
    # 1. Trim silence (top_db=25)
    y_trimmed, _ = librosa.effects.trim(y, top_db=25)
    if len(y_trimmed) == 0:
        return np.array([], dtype=np.float32)
        
    # 2. Stationary / Non-stationary noise reduction
    try:
        y_denoised = nr.reduce_noise(y=y_trimmed, sr=sr, stationary=False)
    except Exception:
        y_denoised = y_trimmed
        
    # 3. Peak normalization
    y_norm = librosa.util.normalize(y_denoised)
    return y_norm

def preprocess_audio_file(audio_path: str, target_sr: int = 16000):
    """
    Loads an audio file, converts to 16kHz mono, and applies the clean_audio pipeline.
    Returns (cleaned_audio_array, sample_rate)
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
    y, sr = librosa.load(audio_path, sr=target_sr, mono=True)
    y_cleaned = clean_audio(y, sr)
    return y_cleaned, sr
