import difflib
import random
from typing import Dict, Any, List

EXERCISES = {
    "Easy": [
        "Hello", "Sunshine", "Water", "Family", "Together",
        "Happy", "Pencil", "Coffee", "Listen", "Welcome"
    ],
    "Medium": [
        "Good morning to you",
        "How are you doing today?",
        "Please pass the water",
        "I would like some tea",
        "Today is a wonderful day",
        "Can you hear me clearly?"
    ],
    "Hard": [
        "The quick brown fox jumps over the lazy dog",
        "Communication empowers everyone to share their voice",
        "Practice and consistency lead to clearer speech every single day",
        "Technology can bridge the gap between people and understanding"
    ]
}

def get_random_exercise(difficulty: str = "Easy") -> str:
    phrases = EXERCISES.get(difficulty, EXERCISES["Easy"])
    return random.choice(phrases)

def evaluate_speech_attempt(target_phrase: str, spoken_transcript: str) -> Dict[str, Any]:
    """
    Evaluates spoken attempt against target phrase using fuzzy matching.
    Provides gentle, non-judgmental scoring and helpful visual diff.
    """
    target_clean = target_phrase.strip().lower()
    spoken_clean = spoken_transcript.strip().lower()
    
    # Calculate overall string similarity ratio
    matcher = difflib.SequenceMatcher(None, target_clean, spoken_clean)
    similarity = matcher.ratio()
    match_score_pct = round(similarity * 100.0, 1)
    
    # Word level diff analysis
    target_words = target_clean.split()
    spoken_words = spoken_clean.split()
    
    word_matcher = difflib.SequenceMatcher(None, target_words, spoken_words)
    diff_analysis = []
    correct_count = 0
    
    for tag, i1, i2, j1, j2 in word_matcher.get_opcodes():
        if tag == 'equal':
            for w in target_words[i1:i2]:
                diff_analysis.append({"word": w, "status": "correct", "display": w})
                correct_count += 1
        elif tag == 'replace':
            for w_t in target_words[i1:i2]:
                diff_analysis.append({"word": w_t, "status": "needs_practice", "display": w_t})
        elif tag == 'delete':
            for w_t in target_words[i1:i2]:
                diff_analysis.append({"word": w_t, "status": "skipped", "display": w_t})
        elif tag == 'insert':
            pass # Extra words spoken
            
    # Generate encouraging feedback message based on score
    if match_score_pct >= 85.0:
        feedback = "🌟 Outstanding effort! Your speech was exceptionally clear!"
        badge = "Gold Star 🏆"
    elif match_score_pct >= 65.0:
        feedback = "👍 Great job! You pronounced most words clearly. Keep practicing!"
        badge = "Silver Star 🥈"
    elif match_score_pct >= 45.0:
        feedback = "💪 Good attempt! Every practice session brings real progress. Try speaking a bit slower."
        badge = "Bronze Badge 🥉"
    else:
        feedback = "❤️ Gentle effort! Don't worry at all — practice is about consistency, not perfection. Take your time!"
        badge = "Practice Explorer 🔍"
        
    return {
        "target_phrase": target_phrase,
        "spoken_transcript": spoken_transcript,
        "match_score_pct": match_score_pct,
        "correct_word_count": correct_count,
        "total_word_count": len(target_words),
        "word_diff": diff_analysis,
        "feedback_msg": feedback,
        "badge": badge
    }
