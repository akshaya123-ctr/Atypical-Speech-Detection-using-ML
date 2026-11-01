# System Architecture & Technical Specifications

## 1. High-Level Data Flow

```
[User Audio / Webcam Input]
           │
           ▼
 [preprocessing/audio_pipeline.py]
  (16kHz Resampling, Non-Stationary Denoising, Silence Trim, RMS Norm)
           │
     ┌─────┴────────────────────────┐
     ▼                              ▼
[utils/whisper_stt.py]    [features/extractor.py]
 (Faster-Whisper STT)      (63 Acoustic Features)
     │                              │
     └──────────────┬───────────────┘
                    ▼
          [utils/predictor.py]
     (StandardScaler + Best Classifier)
                    │
   ┌────────────────┼────────────────┐
   ▼                ▼                ▼
[Disorder Label] [Severity %] [Transcript & Word Confs]
   │                │                │
   └────────────────┼────────────────┘
                    ▼
          [database/db_manager.py]
              (SQLite Storage)
                    │
   ┌────────────────┼────────────────┐
   ▼                ▼                ▼
[ui/tabs/]   [reports/pdf]    [sharing/whatsapp]
```

## 2. Audio Signal Preprocessing Standard
To eliminate training and live inference mismatch, every audio sample passes through `preprocessing/audio_pipeline.py`:
1. **Resampling**: Standardized to 16,000 Hz, 16-bit mono.
2. **Silence Trimming**: `librosa.effects.trim` with `top_db=25`.
3. **Spectral Denoising**: `noisereduce.reduce_noise` with non-stationary background estimation.
4. **Loudness Normalization**: Peak / RMS scaling using `librosa.util.normalize`.

## 3. Feature Matrix (63 Dimensions)
- **MFCCs**: 13 coefficients + 13 Delta + 13 Delta-Delta (39 features).
- **Pitch ($F_0$)**: YIN pitch tracker mean & standard deviation.
- **Energy (RMS)**: Root Mean Square energy mean & standard deviation.
- **Spectral Features**: Centroid, Bandwidth, Roll-off (mean & std).
- **Acoustic Perturbations**: Relative Jitter (frequency variation) & Relative Shimmer (amplitude variation).
- **Zero Crossing Rate**: Mean & standard deviation.
- **Chroma STFT**: 12 pitch class energy bins.

## 4. Machine Learning & Cross-Validation Strategy
- **Target Fields (3 Classes)**:
  1. `typical`: Control / normal speech without disorder
  2. `dysarthria`: Motor speech impairment characterized by slurred articulation
  3. `stammer`: Fluency disorder characterized by blocks, prolongations, and sound repetitions
- **Speaker Independence**: Evaluated using `StratifiedGroupKFold(n_splits=5)` grouped strictly by `speaker_id` across 264 unique speakers with zero data leakage (`train_speakers ∩ test_speakers = ∅`).
- **Only 3 Algorithms Evaluated (Separate Implementations for Easy Learning)**:
  1. **Support Vector Machine (SVM)** with RBF Kernel (`train_test_svm.py`)
  2. **Random Forest Classifier (RF)** with Feature Importance Analysis (`train_test_rf.py`)
  3. **Multi-Layer Perceptron (MLP)** Feedforward Neural Network (`train_test_mlp.py`)
- **Model Persistence**: Saved to `models/stage_1/best_model.joblib`, `SVM.joblib`, `Random_Forest.joblib`, `MLP.joblib`, `scaler.joblib`, `label_encoder.joblib`, and `feature_config.json`.

## 5. SQLite Database Schema (`database/speech_app.db`)
- `speech_checks`: `id`, `timestamp`, `disorder_type`, `severity_pct`, `severity_category`, `confidence`, `transcript`, `latency_seconds`.
- `practice_sessions`: `id`, `timestamp`, `exercise_type`, `target_phrase`, `spoken_transcript`, `match_score_pct`, `feedback_msg`, `video_path`.
- `saved_contacts`: `id`, `name`, `phone_number`, `notes`.
