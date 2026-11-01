import os
import sys
import unittest
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.predictor import load_inference_artifacts, predict_audio_sample

def test_svm_rf_mlp_artifacts():
    algorithms = ["SVM", "Random_Forest", "MLP", "best_model"]
    for algo in algorithms:
        model, scaler, encoder, feature_names = load_inference_artifacts(algo)
        assert model is not None, f"Model artifact for {algo} must exist and be loadable"
        assert scaler is not None, f"Scaler must exist"
        assert encoder is not None, f"Label encoder must exist"
        assert feature_names is not None and len(feature_names) > 0, "Feature names config must exist"
        
        # Test synthetic forward prediction
        dummy_feat = np.zeros((1, len(feature_names)))
        scaled = scaler.transform(dummy_feat)
        pred = model.predict(scaled)
        assert len(pred) == 1, f"Prediction shape must match for {algo}"
        
        # Test probability prediction
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(scaled)
            assert probs.shape[1] == len(encoder.classes_), f"Probabilities shape must match number of classes for {algo}"

if __name__ == "__main__":
    test_svm_rf_mlp_artifacts()
    print("All algorithm artifact tests passed!")
