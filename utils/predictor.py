import os
import json
import joblib
import numpy as np

from features.extractor import extract_extended_features
from utils.whisper_stt import transcribe_speech

MODEL_DIR = "models/stage_1"

_models_cache = {}
_scaler = None
_encoder = None
_feature_names = None

def load_inference_artifacts(model_name: str = None):
    global _models_cache, _scaler, _encoder, _feature_names
    
    # Resolve target model filename
    if model_name and model_name.lower() not in ["auto", "best model (auto)", "best_model", "best model"]:
        clean_name = model_name.strip().replace(" ", "_")
        filename = f"{clean_name}.joblib"
    else:
        filename = "best_model.joblib"
        
    model_path = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(model_path):
        model_path = os.path.join(MODEL_DIR, "best_model.joblib")
        
    scaler_path = os.path.join(MODEL_DIR, "scaler.joblib")
    encoder_path = os.path.join(MODEL_DIR, "label_encoder.joblib")
    config_path = os.path.join(MODEL_DIR, "feature_config.json")
    
    if _scaler is None and os.path.exists(scaler_path):
        _scaler = joblib.load(scaler_path)
    if _encoder is None and os.path.exists(encoder_path):
        _encoder = joblib.load(encoder_path)
    if _feature_names is None and os.path.exists(config_path):
        with open(config_path, "r") as f:
            cfg = json.load(f)
            _feature_names = cfg.get("feature_names", [])
            
    if model_path not in _models_cache and os.path.exists(model_path):
        _models_cache[model_path] = joblib.load(model_path)
        
    model = _models_cache.get(model_path, None)
    return model, _scaler, _encoder, _feature_names

def predict_audio_sample(audio_path: str, model_name: str = None):
    """
    Complete inference pipeline for live audio:
    1. Transcribe speech using faster-whisper.
    2. Extract acoustic features using unified pipeline.
    3. Predict disorder classification, confidence score, and severity percentage + category.
    """
    # 1. Transcribe speech
    stt_res = transcribe_speech(audio_path)
    
    # 2. Load model
    model, scaler, encoder, feature_names = load_inference_artifacts(model_name)
    
    if model is None or scaler is None or encoder is None:
        return {
            "error": "ML model artifacts not loaded. Please train models first.",
            "stt": stt_res
        }
        
    # 3. Extract features
    feat_dict = extract_extended_features(audio_path)
    if feat_dict is None:
        return {
            "error": "No clear speech detected in audio recording. Please speak clearly into the microphone.",
            "stt": stt_res
        }
        
    # Ensure feature vector matches training feature names
    if feature_names:
        feat_vector = np.array([feat_dict.get(fn, 0.0) for fn in feature_names]).reshape(1, -1)
    else:
        feat_vector = np.array(list(feat_dict.values())).reshape(1, -1)
        
    # 4. Predict Raw ML Probabilities
    feat_scaled = scaler.transform(feat_vector)
    
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(feat_scaled)[0]
        raw_probs = {cls: float(probs[i]) for i, cls in enumerate(encoder.classes_)}
    else:
        pred_raw_idx = model.predict(feat_scaled)[0]
        pred_raw_label = encoder.inverse_transform([pred_raw_idx])[0]
        raw_probs = {cls: (0.85 if cls == pred_raw_label else 0.075) for cls in encoder.classes_}

    # 5. Speech Fluency & Acoustic Verification Engine
    # Prevents false positive stammer classifications caused by microphone channel frequency bias
    p_dys = raw_probs.get("dysarthria", 0.0)
    p_stm = raw_probs.get("stammer", 0.0)
    p_typ = raw_probs.get("typical", 0.0)

    try:
        import soundfile as sf
        import librosa
        y, file_sr = sf.read(audio_path)
        total_dur = len(y) / file_sr
        intervals = librosa.effects.split(y, top_db=22)
        active_dur = sum((end - start) for start, end in intervals) / file_sr if len(intervals) > 0 else total_dur
        active_dur = max(0.4, active_dur)
    except Exception:
        active_dur = 1.0

    transcript = stt_res.get("transcript", "").strip()
    words = transcript.split()
    wps = len(words) / active_dur if active_dur > 0 else 2.5
    avg_conf = stt_res.get("confidence", 80.0)

    # Check for lexical stuttering indicators (e.g. 'I I', 'the the', 'b-b-but')
    words_clean = [w.lower().strip(".,?!-") for w in words]
    has_word_repetition = any(words_clean[i] == words_clean[i+1] for i in range(len(words_clean)-1)) if len(words_clean) > 1 else False
    has_hyphen_repetition = any("-" in w for w in words)

    # A speaker with fluent conversational cadence (WPS >= 1.8), clean transcription, and 0 stutter repetitions
    is_fluent = (wps >= 1.8) and (not has_word_repetition) and (not has_hyphen_repetition) and (avg_conf >= 65.0)

    if is_fluent and p_stm > p_typ:
        # Re-balance away from false-positive microphone channel artifact toward true typical speech
        p_typ_adj = max(0.68, p_typ + p_stm * 0.75)
        p_stm_adj = p_stm * 0.25
        p_dys_adj = p_dys
        tot = p_typ_adj + p_stm_adj + p_dys_adj
        p_typ, p_stm, p_dys = p_typ_adj / tot, p_stm_adj / tot, p_dys_adj / tot

    calibrated_probs = {
        "dysarthria": float(p_dys),
        "stammer": float(p_stm),
        "typical": float(p_typ)
    }

    pred_label = max(calibrated_probs, key=calibrated_probs.get)
    confidence = calibrated_probs[pred_label] * 100.0

    # 6. Diagnostic Severity Estimation for the 3 Fields
    pred_lower = pred_label.lower()
    is_disorder = (pred_lower in ["dysarthria", "stammer"])

    jitter = feat_dict.get("jitter", 0.0)
    shimmer = feat_dict.get("shimmer", 0.0)
    zcr_std = feat_dict.get("zcr_std", 0.0)
    pitch_std = feat_dict.get("pitch_std", 0.0)

    if pred_lower == "dysarthria":
        prob_val = calibrated_probs.get("dysarthria", 0.7)
        severity_pct = float(np.clip(prob_val * 60 + (jitter + shimmer) * 120 + zcr_std * 80, 35.0, 95.0))
        if severity_pct < 55.0:
            severity_category = "mild"
            severity_color = "amber"
        elif severity_pct < 75.0:
            severity_category = "moderate"
            severity_color = "orange"
        else:
            severity_category = "severe"
            severity_color = "red"
    elif pred_lower == "stammer":
        prob_val = calibrated_probs.get("stammer", 0.7)
        severity_pct = float(np.clip(prob_val * 60 + jitter * 140 + (pitch_std / 12.0), 30.0, 95.0))
        if severity_pct < 55.0:
            severity_category = "mild"
            severity_color = "amber"
        elif severity_pct < 75.0:
            severity_category = "moderate"
            severity_color = "orange"
        else:
            severity_category = "severe"
            severity_color = "red"
    else:
        # Typical Speech
        severity_pct = 0.0
        severity_category = "typical"
        severity_color = "green"
        
    return {
        "disorder_type": pred_label,
        "is_disorder": is_disorder,
        "confidence": round(confidence, 1),
        "class_probabilities": {k: round(v * 100.0 if v <= 1.0 else v, 1) for k, v in calibrated_probs.items()},
        "severity_percentage": round(severity_pct, 1),
        "severity_category": severity_category,
        "severity_color": severity_color,
        "transcript": stt_res["transcript"],
        "word_confidences": stt_res["word_confidences"],
        "stt_confidence": stt_res["confidence"],
        "latency_seconds": stt_res["latency_seconds"],
        "features": feat_dict,
        "model_used": model_name or "Best Model (Auto)",
        "success": True
    }
