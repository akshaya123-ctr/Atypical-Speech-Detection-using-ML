"""
Unified Training Pipeline: 3 Algorithms (SVM, Random Forest, MLP) on 3 Fields (Typical, Dysarthria, Stammer)
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from training.train_pipeline import train_and_validate_module1

if __name__ == "__main__":
    train_and_validate_module1()
