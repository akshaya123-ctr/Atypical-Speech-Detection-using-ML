import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.predictor import load_inference_artifacts

def test_load_inference_artifacts():
    model, scaler, encoder, feature_names = load_inference_artifacts()
    assert model is not None, "Trained ML model should be loaded"
    assert scaler is not None, "Scaler should be loaded"
    assert encoder is not None, "Label encoder should be loaded"
    assert feature_names is not None, "Feature config should be loaded"
