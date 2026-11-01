import numpy as np
import librosa
import os
from typing import Dict, Any, Optional, List
from preprocessing.audio_pipeline import preprocess_audio_file, clean_audio

FEATURE_NAMES: List[str] = []
for i in range(1, 14):
    FEATURE_NAMES.extend([f"mfcc_{i}", f"mfcc_delta_{i}", f"mfcc_delta2_{i}"])
FEATURE_NAMES.extend([
    "pitch_mean", "pitch_std",
    "rms_mean", "rms_std",
    "zcr_mean", "zcr_std",
    "spec_centroid_mean", "spec_centroid_std",
    "spec_bw_mean", "spec_bw_std",
    "spec_rolloff_mean", "spec_rolloff_std"
])
for i in range(1, 13):
    FEATURE_NAMES.append(f"chroma_{i}")
FEATURE_NAMES.extend(["jitter", "shimmer"])

def calculate_jitter_shimmer(y: np.ndarray, sr: int, f0: Optional[np.ndarray] = None) -> tuple:
    """
    Estimates relative jitter (frequency instability) and shimmer (amplitude instability)
    from pitch periods and peak amplitudes.
    """
    try:
        if f0 is None:
            f0 = librosa.yin(y, fmin=50, fmax=500, sr=sr, hop_length=512)
        f0_valid = f0[~np.isnan(f0)]
        if len(f0_valid) < 5:
            return 0.0, 0.0
            
        periods = 1.0 / (f0_valid + 1e-6)
        period_diffs = np.abs(np.diff(periods))
        jitter = np.mean(period_diffs) / (np.mean(periods) + 1e-6)
        
        # Amplitude shimmer estimation over pitch frames
        frame_length = int(sr * 0.025)
        hop_length = int(sr * 0.010)
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        rms_valid = rms[rms > 1e-4]
        if len(rms_valid) < 5:
            shimmer = 0.0
        else:
            rms_diffs = np.abs(np.diff(rms_valid))
            shimmer = np.mean(rms_diffs) / (np.mean(rms_valid) + 1e-6)
            
        return float(np.clip(jitter, 0.0, 1.0)), float(np.clip(shimmer, 0.0, 1.0))
    except Exception:
        return 0.0, 0.0

def extract_extended_features(audio_input, sr: int = 16000) -> Optional[Dict[str, float]]:
    """
    Extracts comprehensive acoustic features from audio path or audio numpy array.
    Returns dictionary mapping feature name to numeric value.
    """
    try:
        if isinstance(audio_input, str):
            if not os.path.exists(audio_input):
                return None
            y_cleaned, sr = preprocess_audio_file(audio_input, target_sr=sr)
        else:
            y_cleaned = clean_audio(audio_input, sr)
            
        if len(y_cleaned) < sr * 0.1:  # Less than 100ms
            return None
            
        # 1. 13 MFCCs + Deltas + Delta-Deltas (39)
        mfccs = librosa.feature.mfcc(y=y_cleaned, sr=sr, n_mfcc=13)
        delta_mfccs = librosa.feature.delta(mfccs)
        delta2_mfccs = librosa.feature.delta(mfccs, order=2)
        
        mfccs_mean = np.mean(mfccs, axis=1)
        delta_mean = np.mean(delta_mfccs, axis=1)
        delta2_mean = np.mean(delta2_mfccs, axis=1)
        
        # 2. Pitch (F0) with fast hop_length=512
        f0 = librosa.yin(y_cleaned, fmin=50, fmax=500, sr=sr, hop_length=512)
        f0_valid = f0[~np.isnan(f0)]
        pitch_mean = float(np.mean(f0_valid)) if len(f0_valid) > 0 else 0.0
        pitch_std = float(np.std(f0_valid)) if len(f0_valid) > 0 else 0.0
        
        # 3. Energy / RMS
        rms = librosa.feature.rms(y=y_cleaned)[0]
        rms_mean = float(np.mean(rms))
        rms_std = float(np.std(rms))
        
        # 4. Zero Crossing Rate
        zcr = librosa.feature.zero_crossing_rate(y_cleaned)[0]
        zcr_mean = float(np.mean(zcr))
        zcr_std = float(np.std(zcr))
        
        # 5. Spectral Centroid
        sc = librosa.feature.spectral_centroid(y=y_cleaned, sr=sr)[0]
        sc_mean = float(np.mean(sc))
        sc_std = float(np.std(sc))
        
        # 6. Spectral Bandwidth
        sb = librosa.feature.spectral_bandwidth(y=y_cleaned, sr=sr)[0]
        sb_mean = float(np.mean(sb))
        sb_std = float(np.std(sb))
        
        # 7. Spectral Roll-off
        sro = librosa.feature.spectral_rolloff(y=y_cleaned, sr=sr)[0]
        sro_mean = float(np.mean(sro))
        sro_std = float(np.std(sro))
        
        # 8. Chroma Features (12)
        chroma = librosa.feature.chroma_stft(y=y_cleaned, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        
        # 9. Jitter & Shimmer (reusing f0)
        jitter, shimmer = calculate_jitter_shimmer(y_cleaned, sr, f0=f0)
        
        # Build dict
        feature_dict = {}
        for i in range(13):
            feature_dict[f"mfcc_{i+1}"] = float(mfccs_mean[i])
            feature_dict[f"mfcc_delta_{i+1}"] = float(delta_mean[i])
            feature_dict[f"mfcc_delta2_{i+1}"] = float(delta2_mean[i])
            
        feature_dict["pitch_mean"] = pitch_mean
        feature_dict["pitch_std"] = pitch_std
        feature_dict["rms_mean"] = rms_mean
        feature_dict["rms_std"] = rms_std
        feature_dict["zcr_mean"] = zcr_mean
        feature_dict["zcr_std"] = zcr_std
        feature_dict["spec_centroid_mean"] = sc_mean
        feature_dict["spec_centroid_std"] = sc_std
        feature_dict["spec_bw_mean"] = sb_mean
        feature_dict["spec_bw_std"] = sb_std
        feature_dict["spec_rolloff_mean"] = sro_mean
        feature_dict["spec_rolloff_std"] = sro_std
        
        for i in range(12):
            feature_dict[f"chroma_{i+1}"] = float(chroma_mean[i])
            
        feature_dict["jitter"] = jitter
        feature_dict["shimmer"] = shimmer
        
        return feature_dict
    except Exception as e:
        print(f"Error extracting features: {e}")
        return None
