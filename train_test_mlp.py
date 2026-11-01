"""
=============================================================================
  MULTI-LAYER PERCEPTRON (MLP) - SPEECH DISORDER CLASSIFICATION
  Target Fields (3 Classes): Typical, Dysarthria, Stammer
=============================================================================

What is Multi-Layer Perceptron (MLP)?
-------------------------------------
MLP is a feedforward Artificial Neural Network (ANN) model capable of learning
complex non-linear mappings between high-dimensional acoustic representations
and clinical speech disorder categories.

Architecture Used:
- Input Layer: 63 nodes (corresponding to the 63 acoustic features).
- Hidden Layer 1: 128 neurons with Rectified Linear Unit (ReLU) activation.
- Hidden Layer 2: 64 neurons with ReLU activation.
- Output Layer: 3 nodes with Softmax activation (Typical, Dysarthria, Stammer).
- Optimization: Adam optimizer with learning rate 0.001 and L2 penalty (alpha=0.001).
- Training Stability: Early stopping with patience=15 epochs.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.neural_network import MLPClassifier
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

def train_and_test_mlp():
    print("=" * 70)
    print("      TRAINING & TESTING: MULTI-LAYER PERCEPTRON (MLP)")
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

    # 3. Setup MLP Neural Network Classifier
    mlp_model = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        solver='adam',
        alpha=0.001,
        learning_rate_init=0.001,
        max_iter=500,
        early_stopping=True,
        n_iter_no_change=15,
        random_state=42
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
        
        # Standardize features (Neural networks require zero mean & unit variance)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Fit MLP
        mlp_model.fit(X_train_scaled, y_train)
        
        # Predict on holdout test fold
        preds = mlp_model.predict(X_test_scaled)
        
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
    print("                     MLP 5-FOLD CV RESULTS")
    print("=" * 70)
    print(f"  Average Accuracy:  {mean_acc*100:6.2f}% (+/- {std_acc*100:5.2f}%)")
    print(f"  Average F1 Score:  {mean_f1:6.4f}")
    print(f"  Average Precision: {mean_prec:6.4f}")
    print(f"  Average Recall:    {mean_rec:6.4f}")
    print("=" * 70)

    # Classification Report
    print("\nDetailed Per-Field Classification Report:")
    print(classification_report(all_y_true, all_y_pred, target_names=classes, digits=4))

    # 5. Fit full model & Save Model Artifacts
    full_scaler = StandardScaler()
    X_full_scaled = full_scaler.fit_transform(X)
    
    final_mlp = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        solver='adam',
        alpha=0.001,
        learning_rate_init=0.001,
        max_iter=500,
        early_stopping=True,
        n_iter_no_change=15,
        random_state=42
    )
    final_mlp.fit(X_full_scaled, y)
    
    mlp_path = os.path.join(MODEL_DIR, "MLP.joblib")
    joblib.dump(final_mlp, mlp_path)
    print(f"\n[Saved] MLP Model Artifact: {mlp_path}")

    # 6. Save Confusion Matrix Plot
    cm = confusion_matrix(all_y_true, all_y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.title("MLP Confusion Matrix (5-Fold CV)")
    plt.ylabel('True Field')
    plt.xlabel('Predicted Field')
    plt.tight_layout()
    cm_path = os.path.join(RESULTS_DIR, "MLP_cm.png")
    plt.savefig(cm_path)
    plt.close()
    print(f"[Saved] Confusion Matrix Heatmap: {cm_path}")

    return {
        "algorithm": "MLP",
        "accuracy": mean_acc,
        "accuracy_std": std_acc,
        "f1": mean_f1,
        "precision": mean_prec,
        "recall": mean_rec,
        "fold_scores": fold_accuracies
    }

if __name__ == "__main__":
    train_and_test_mlp()
