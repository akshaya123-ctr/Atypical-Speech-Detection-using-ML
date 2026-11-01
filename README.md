# 🗣️ Atypical Speech Detection & Communication Assistant

> A complete AI-powered accessibility platform for individuals with speech disorders (such as Dysarthria and Stammer). The system transcribes atypical speech accurately, detects disorder presence, estimates severity percentages, guides vocal and webcam video practice with instant fuzzy feedback, tracks progress over time, enables WhatsApp communication, and provides accessible AI guidance.

---

## 🌟 Key Features

### 1. 🎤 Core Detection & Preprocessing Engine (Module 1)
- **Speech-to-Text (Faster-Whisper)**: Accurate transcription optimized for both typical and atypical speech patterns, returning word-level confidence metrics and latency.
- **Unified Preprocessing Pipeline**: Resampling (16kHz mono), non-stationary noise reduction (`noisereduce`), silence trimming (`librosa.effects.trim`), and RMS loudness normalization.
- **Extended Acoustic Feature Extraction (63 Features)**:
  - 13 MFCCs + 13 Delta MFCCs + 13 Delta-Delta MFCCs (39 features)
  - Fundamental Frequency / Pitch ($F_0$ mean & std)
  - RMS Energy (mean & std)
  - Relative Jitter & Shimmer (acoustic perturbation indicators)
  - Zero Crossing Rate (mean & std)
  - Spectral Centroid, Bandwidth, and Roll-off
  - 12 Chroma STFT features
- **Speaker-Independent 5-Fold Cross-Validation**: `StratifiedGroupKFold` split ensuring **0 speaker leakage** between training and testing sets.
- **Multi-Algorithm Model Selection**: Automatic training, benchmarking, and comparison of **SVM, Random Forest, and MLP (Multi-Layer Perceptron)**. Best performing classifier auto-selected for live inference with multi-model interactive testing.
- **Severity Estimation**: Calculates severity percentage ($0\% - 100\%$) and category (**Green: Typical**, **Amber: Mild**, **Orange: Moderate**, **Red: Severe**).

### 2. 🏋️ Practice & Training Studio (Module 2)
- **Live Voice Exercises**: Single words, short phrases, and full sentences with no timers or pressure.
- **Fuzzy Match Feedback Engine**: Uses `difflib.SequenceMatcher` for instant, non-judgmental scoring and visual diff highlighting.
- **Webcam Video Exercises with Overlaid Captions**: Record video during speech exercises. Spoken words are transcribed and rendered onto the MP4 video using **OpenCV** for self-review.
- **Progress Tracking & Analytics**: Interactive **Plotly** severity reduction charts and practice history logs powered by **SQLite**.

### 3. 💬 AI Chat Assistant (Module 3)
- **OpenAI API Integration**: Conversational assistant answering questions about dysarthria, exercises, and app usage via text or voice.
- **Intelligent Offline Fallback**: Rule-based knowledge engine when no API key is set.
- **Suggested Prompts & Clear Medical Disclaimer**.

### 4. 📤 Communication & WhatsApp Sharing (Module 4)
- **WhatsApp Direct Sharing**: Generates `wa.me/?text=...` deep-links for instant sharing without requiring business API credentials.
- **Saved Contacts Directory**: Manage caregiver and family phone numbers for one-click direct WhatsApp sharing.
- **Downloadable PDF Clinical Summaries**: ReportLab-generated reports detailing transcripts, severity metrics, and practice recommendations.

### 5. 🎨 Modern Accessible UI/UX (Module 5)
- **Apple Health / Microsoft Fluent Aesthetic**: Warm rounded cards (20px), soft elevation shadows, high-contrast typography, and intuitive touch targets.

---

## 🛠️ Technology Stack

- **Frontend**: Streamlit, Custom CSS (Fluent design system), Plotly, Pillow
- **Machine Learning**: Python, Scikit-learn, Imbalanced-learn (SMOTE), Joblib
- **Speech Recognition**: Faster-Whisper
- **Audio Processing**: Librosa, Noisereduce, SoundFile, PyDub
- **Computer Vision**: OpenCV (`cv2`)
- **Database & Storage**: SQLite3, JSON, CSV
- **Reports**: ReportLab PDF Engine
- **AI Chat**: OpenAI API / Claude API

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure Python 3.9+ is installed on your system.

### 2. Installation
```bash
git clone https://github.com/your-username/atypical-speech-detection.git
cd atypical-speech-detection

# Install required dependencies
pip install -r requirements.txt
```

### 3. Run Standalone Algorithm Training & Testing (Separate Files for Learning)
You can train and test each algorithm independently to inspect how each works:
```bash
# 1. Support Vector Machine (SVM)
python train_test_svm.py

# 2. Random Forest (RF with Top Acoustic Features)
python train_test_rf.py

# 3. Multi-Layer Perceptron (MLP Neural Network)
python train_test_mlp.py
```

### 4. Run Full Comparative Pipeline & Benchmark
```bash
python training/train_pipeline.py
python test_models.py
```
*Evaluates SVM, Random Forest, and MLP across the 3 fields (`typical`, `dysarthria`, `stammer`) with 0 speaker leakage, and auto-selects the best model.*

### 5. Launch Application
```bash
streamlit run app.py
```

### 6. Run Automated Tests
```bash
python tests/run_all_tests.py
```

---

## 📊 Module 1 Validation Gate Summary (3 Fields)

```text
==================================================
================ MODULE 1 VALIDATION ================
Best Accuracy:      64.41% (Best Model: SVM)
Cross Validation:   5-Fold Speaker CV (StratifiedGroupKFold)
Speaker Leakage:    0 (PASSED - Verified Zero Overlap)
Target Fields:      ['dysarthria', 'stammer', 'typical']
Validation Gate:    PASS
====================================================
==================================================
```

---

## 📁 Directory Architecture

```
d:\atypical speech detection\
├── app.py                         # Streamlit application entry point
├── requirements.txt               # Dependencies list
├── features.csv                   # Extracted feature dataset (TORGO)
├── model_results.json             # Model CV metrics & selection output
│
├── preprocessing/                 # Audio preprocessing (noise reduction, trimming)
├── features/                      # 63 Extended acoustic feature extraction engine
├── training/                      # Speaker-independent CV & validation gate
├── utils/                         # Faster-whisper STT & live predictor
├── database/                      # SQLite persistence engine
├── practice/                      # Fuzzy matching coach & OpenCV video captioner
├── sharing/                       # WhatsApp wa.me links & contact manager
├── chatbot/                       # OpenAI API assistant & offline fallback
├── reports/                       # ReportLab PDF clinical report generator
├── ui/                            # Custom CSS & Streamlit tab views
├── models/                        # Saved ML models, scalers, encoders
├── tests/                         # Unit & integration test suite
└── docs/                          # Architecture, User Manual, Deployment guide
```
