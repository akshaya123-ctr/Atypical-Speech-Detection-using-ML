import unittest
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.test_audio_pipeline import test_clean_audio_synthetic
from tests.test_feature_extractor import test_feature_extractor_synthetic
from tests.test_db_manager import test_database_crud
from tests.test_practice_coach import test_practice_coach_scoring
from tests.test_predictor import test_load_inference_artifacts
from tests.test_trained_models import test_svm_rf_mlp_artifacts

class TestSuite(unittest.TestCase):
    def test_1_audio_pipeline(self):
        test_clean_audio_synthetic()
        print("  [PASS] Audio Preprocessing Pipeline")
        
    def test_2_feature_extractor(self):
        test_feature_extractor_synthetic()
        print("  [PASS] Extended Feature Extractor (63 Acoustic Features)")
        
    def test_3_database(self):
        test_database_crud()
        print("  [PASS] SQLite Database Operations & CRUD")
        
    def test_4_practice_coach(self):
        test_practice_coach_scoring()
        print("  [PASS] Practice Coach Fuzzy Match Scoring")
        
    def test_5_predictor_artifacts(self):
        test_load_inference_artifacts()
        print("  [PASS] Trained Model Artifacts & Live Predictor Engine")

    def test_6_svm_rf_mlp_models(self):
        test_svm_rf_mlp_artifacts()
        print("  [PASS] SVM, Random Forest, and MLP Multi-Model Inference Tests")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("      RUNNING AUTOMATED TEST SUITE")
    print("="*50)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
        sys.exit(0)
    else:
        print("\n>>> TEST SUITE FAILURE <<<")
        sys.exit(1)
