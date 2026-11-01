"""
Atypical Speech & Stammer Disfluency Normalizer
Identifies repetitions, prolongations, blocks, and reconstructs intended queries
for patients with stammering or dysarthric speech patterns.
"""
import re
from typing import Dict, Any, Tuple

def reconstruct_stammered_text(raw_text: str) -> Tuple[str, bool, str, float]:
    """
    Analyzes raw speech transcription for disfluencies (syllable repetitions,
    sound prolongations, word repetitions, hesitation pauses) and reconstructs
    the clean intended sentence for effortless AI communication.
    
    Returns:
        (clean_text, is_disfluent, disfluency_type, confidence_pct)
    """
    if not raw_text or not raw_text.strip():
        return ("", False, "None", 0.0)

    original = raw_text.strip()
    text = original
    disfluency_detected = False
    disfluency_types = []
    
    # 1. Hyphenated syllable repetitions (e.g. "c-c-can", "w-w-what", "m-motivate", "p-p-please")
    hyphen_pattern = re.compile(r'\b([a-zA-Z]{1,3})-(?:[a-zA-Z]{1,3}-)*([a-zA-Z]+)\b', re.IGNORECASE)
    def clean_hyphen(match):
        nonlocal disfluency_detected
        disfluency_detected = True
        disfluency_types.append("Syllable Repetition")
        return match.group(2)
    
    text = hyphen_pattern.sub(clean_hyphen, text)
    
    # 2. Sound prolongations (e.g. "sssspeak" -> "speak", "wwwwwater" -> "water", "mmmmotivate" -> "motivate")
    prolong_pattern = re.compile(r'\b([bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ])\1{2,}([a-zA-Z]+)\b')
    def clean_prolong(match):
        nonlocal disfluency_detected
        disfluency_detected = True
        disfluency_types.append("Sound Prolongation")
        return match.group(1) + match.group(2)
        
    text = prolong_pattern.sub(clean_prolong, text)
    
    # 3. Whole-word stutter repetitions (e.g. "can can can you" -> "can you", "I I I want" -> "I want", "help... help" -> "help")
    word_rep_pattern = re.compile(r'\b(\w+)(?:\s+(?:[.\-,…\s]*)\s*\1\b)+', re.IGNORECASE)
    def clean_word_rep(match):
        nonlocal disfluency_detected
        disfluency_detected = True
        disfluency_types.append("Word Repetition")
        return match.group(1)
        
    text = word_rep_pattern.sub(clean_word_rep, text)
    
    # 4. Clean hesitation fillers like "um...", "uh...", "er..." when embedded inside phrases
    filler_pattern = re.compile(r'\b(?:um+|uh+|er+|ah+)[.\-,…]*\s*', re.IGNORECASE)
    cleaned_fillers = filler_pattern.sub('', text).strip()
    if cleaned_fillers and len(cleaned_fillers) > 2 and cleaned_fillers != text:
        disfluency_detected = True
        disfluency_types.append("Hesitation Blocks")
        text = cleaned_fillers

    # Clean up whitespace and punctuation
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Capitalize first letter
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
        
    primary_type = ", ".join(list(dict.fromkeys(disfluency_types))) if disfluency_types else "Typical Articulation"
    conf = 88.5 if disfluency_detected else 95.0
    
    return (text, disfluency_detected, primary_type, conf)
