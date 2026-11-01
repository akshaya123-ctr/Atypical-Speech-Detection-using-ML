# 🚀 Deployment & Installation Guide

## 1. Local Environment Setup

### System Requirements
- OS: Windows, macOS, or Linux
- Python: 3.9, 3.10, 3.11, or 3.12
- Memory: 4GB RAM minimum (8GB recommended)

### Environment Setup
```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Upgrade pip & install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 2. Model Training & Verification

Before running the application for the first time, execute the Module 1 training pipeline to extract features and validate the ML model:

```bash
python training/train_pipeline.py
```

This script will:
1. Extract 63 acoustic features from the TORGO dataset.
2. Verify 0 speaker leakage across 5 folds (`StratifiedGroupKFold`).
3. Train Random Forest, SVM, Logistic Regression, KNN, and Gradient Boosting.
4. Print the **Module 1 Validation Gate PASS** summary.
5. Save model artifacts to `models/stage_1/`.

---

## 3. Running the Application locally

```bash
streamlit run app.py
```
The app will open automatically in your browser at `http://localhost:8501`.

---

## 4. Running Automated Tests

```bash
python tests/run_all_tests.py
```

---

## 5. Deployment on Streamlit Community Cloud

1. Push your repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/).
3. Connect your GitHub repository.
4. Set Main file path to `app.py`.
5. (Optional) Add your `OPENAI_API_KEY` in Streamlit Secrets:
   ```toml
   OPENAI_API_KEY = "your-actual-api-key"
   ```
6. Click **Deploy**!
