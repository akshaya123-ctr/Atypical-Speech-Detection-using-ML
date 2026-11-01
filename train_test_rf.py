"""
=============================================================================
  RANDOM FOREST (RF) - SPEECH DISORDER CLASSIFICATION
  Target Fields (3 Classes): Typical, Dysarthria, Stammer
=============================================================================

What is Random Forest?
----------------------
Random Forest is an ensemble learning method constructed from numerous
decision trees. Each tree is trained on a bootstrap sample of the dataset,
and at each split, a random subset of acoustic features is considered.
The ensemble combines predictions via majority voting, reducing variance
and preventing overfitting on complex acoustic vectors.

Key Parameters Used:
- n_estimators: 100 (100 independent decision trees).
- max_depth: None (trees expand until all leaves are pure or minimal samples).
- class_weight: 'balanced' (handles any slight class imbalances).
- random_state: 42 (ensures deterministic reproducibility).

Additional Educational Feature:
- Feature Importance Analysis: Ranks top predictive acoustic features
  (e.g., Jitter, Shimmer, Pitch variations, MFCCs).
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    confusion_matrix, classification_report
)

# Project paths
FEATURES_CSV = "features.csv"
MODEL_DIR = "models/stage_1"
RESULTS_DIR = "results/stage_1"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def train_and_test_random_forest():
    print("=" * 70)
    print("      TRAINING & TESTING: RANDOM FOREST (RF)")
    print("      Fields: Typical | Dysarthria | Stammer (3 Classes)")
    print("=" * 70)

    # 1. Load Dataset
    if not os.path.exists(FEATURES_CSV):
        print(f"Error: {FEATURES_CSV} not found.")
        sys.exit(1)

    df = pd.read_csv(FEATURES_CSV)
    
    from features.extractor import FEATURE_NAMES
    feature_cols = [c for c in FEATURE_NAMES if c in df.columns]
    
    df_clean = df.dropna(subset=['disorder_type', 'speaker_id'] + feature_cols).copy()
    
    X = df_clean[feature_cols].values
    y_raw = df_clean['disorder_type'].values
    groups = df_clean['speaker_id'].values

    # 2. Encode Labels
    encoder = LabelEncoder()
    y = encoder.fit_transform(y_raw)
    classes = list(encoder.classes_)
    
    print(f"\nTotal Dataset Samples: {len(df_clean)}")
    print(f"Feature Dimensions:     {len(feature_cols)}")
    print(f"Unique Speakers:        {len(np.unique(groups))}")
    print("\nClass Distribution across 3 Fields:")
    for cls_name, count in df_clean['disorder_type'].value_counts().items():
        print(f"  - {cls_name.capitalize():12s}: {count:5d} samples ({count/len(df_clean)*100:5.1f}%)")

    # 3. Setup Random Forest Classifier
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )

    # 4. Speaker-Independent 5-Fold Cross Validation
    sgkf = StratifiedGroupKFold(n_splits=5)
    
    fold_accuracies = []
    fold_f1_scores = []
    fold_precisions = []
    fold_recalls = []
    
    all_y_true = []
    all_y_pred = []
    
    print("\n" + "-" * 70)
    print("   Running Speaker-Disjoint 5-Fold Cross Validation...")
    print("-" * 70)

    for fold, (train_idx, test_idx) in enumerate(sgkf.split(X, y, groups), 1):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Verify 0 speaker leakage
        train_spks = set(groups[train_idx])
        test_spks = set(groups[test_idx])
        overlap = train_spks.intersection(test_spks)
        assert len(overlap) == 0, f"Fold {fold}: Speaker leakage detected!"
        
        # Fit Random Forest
        rf_model.fit(X_train, y_train)
        
        # Predict on holdout test fold
        preds = rf_model.predict(X_test)
        
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds, average='macro', zero_division=0)
        prec = precision_score(y_test, preds, average='macro', zero_division=0)
        rec = recall_score(y_test, preds, average='macro', zero_division=0)
        
        fold_accuracies.append(acc)
        fold_f1_scores.append(f1)
        fold_precisions.append(prec)
        fold_recalls.append(rec)
        
        all_y_true.extend(y_test)
        all_y_pred.extend(preds)
        
        print(f"  Fold {fold} | Test Speakers: {len(test_spks):2d} | Accuracy: {acc*100:6.2f}% | F1: {f1:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f}")

    mean_acc = float(np.mean(fold_accuracies))
    std_acc = float(np.std(fold_accuracies))
    mean_f1 = float(np.mean(fold_f1_scores))
    mean_prec = float(np.mean(fold_precisions))
    mean_rec = float(np.mean(fold_recalls))

    print("\n" + "=" * 70)
    print("                 RANDOM FOREST 5-FOLD CV RESULTS")
    print("=" * 70)
    print(f"  Average Accuracy:  {mean_acc*100:6.2f}% (+/- {std_acc*100:5.2f}%)")
    print(f"  Average F1 Score:  {mean_f1:6.4f}")
    print(f"  Average Precision: {mean_prec:6.4f}")
    print(f"  Average Recall:    {mean_rec:6.4f}")
    print("=" * 70)

    # Classification Report
    print("\nDetailed Per-Field Classification Report:")
    print(classification_report(all_y_true, all_y_pred, target_names=classes, digits=4))

    # 5. Fit full model & Feature Importance Ranking
    full_rf = RandomForestClassifier(n_estimators=100, max_depth=None, class_weight='balanced', random_state=42, n_jobs=-1)
    full_rf.fit(X, y)
    
    importances = full_rf.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print("\n--- Top 10 Most Important Acoustic Features ---")
    for rank in range(10):
        idx = indices[rank]
        print(f"  {rank+1:2d}. {feature_cols[idx]:20s} (Importance: {importances[idx]*100:5.2f}%)")

    rf_path = os.path.join(MODEL_DIR, "Random_Forest.joblib")
    joblib.dump(full_rf, rf_path)
    print(f"\n[Saved] Random Forest Model Artifact: {rf_path}")

    # 6. Save Confusion Matrix Plot
    cm = confusion_matrix(all_y_true, all_y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.title("Random Forest Confusion Matrix (5-Fold CV)")
    plt.ylabel('True Field')
    plt.xlabel('Predicted Field')
    plt.tight_layout()
    cm_path = os.path.join(RESULTS_DIR, "Random_Forest_cm.png")
    plt.savefig(cm_path)
    plt.close()
    print(f"[Saved] Confusion Matrix Heatmap: {cm_path}")

    return {
        "algorithm": "Random Forest",
        "accuracy": mean_acc,
        "accuracy_std": std_acc,
        "f1": mean_f1,
        "precision": mean_prec,
        "recall": mean_rec,
        "fold_scores": fold_accuracies
    }

if __name__ == "__main__":
    train_and_test_random_forest()
