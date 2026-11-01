"""
Comprehensive Model Testing Suite: SVM | Random Forest | MLP on 3 Fields
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from training.test_models import run_comprehensive_test

if __name__ == "__main__":
    run_comprehensive_test()
