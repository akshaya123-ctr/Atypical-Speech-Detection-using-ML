import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from practice.coach import evaluate_speech_attempt, get_random_exercise

def test_practice_coach_scoring():
    target = "Hello Sunshine"
    attempt_exact = "Hello Sunshine"
    res_exact = evaluate_speech_attempt(target, attempt_exact)
    assert res_exact["match_score_pct"] == 100.0
    assert "Outstanding" in res_exact["feedback_msg"]
    
    attempt_partial = "Hello"
    res_partial = evaluate_speech_attempt(target, attempt_partial)
    assert res_partial["match_score_pct"] < 100.0
    
    ex = get_random_exercise("Easy")
    assert isinstance(ex, str)
    assert len(ex) > 0
