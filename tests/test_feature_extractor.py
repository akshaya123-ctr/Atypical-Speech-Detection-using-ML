import numpy as np
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from features.extractor import extract_extended_features, FEATURE_NAMES

def test_feature_extractor_synthetic():
    sr = 16000
    t = np.linspace(0, 1.0, sr)
    audio = 0.5 * np.sin(2 * np.pi * 300 * t).astype(np.float32)
    
    feats = extract_extended_features(audio, sr=sr)
    assert feats is not None
    assert isinstance(feats, dict)
    
    for fn in FEATURE_NAMES:
        assert fn in feats, f"Missing feature: {fn}"
