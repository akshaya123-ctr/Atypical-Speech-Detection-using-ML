import os
import random
import re
from typing import Dict, Any, List

SYSTEM_PROMPT = """
You are a warm, compassionate, and highly intelligent AI Speech Assistant built into the Atypical Speech Detection & Communication Platform.
Your mission is to support individuals with speech conditions (such as Dysarthria, Stammering / Stuttering, Apraxia, and voice disorders), their families, and clinicians.

Guidelines:
1. Be encouraging, empathetic, patient, and motivating.
2. Provide actionable vocal exercises, speech pacing strategies, and psychological coping tips.
3. Keep clinical information accurate, grounded in Speech-Language Pathology (SLP) best practices.
4. If the user feels anxious, embarrassed, or unmotivated, provide genuine psychological support and remind them that their voice and thoughts have profound value.
5. Remind users that your advice is supportive and educational, and they should also consult their SLP.
"""

SUGGESTED_PROMPTS = [
    "What daily exercises help improve dysarthria speech clarity?",
    "How can I manage stuttering blocks during stressful conversations?",
    "Can you motivate me? I feel self-conscious about my speech today.",
    "Explain how my speech severity score is calculated.",
    "What is the difference between Dysarthria and Stammering?"
]

def query_ai_assistant(user_message: str, history: List[Dict[str, str]] = None) -> str:
    """
    Intelligent Conversational AI Engine:
    1. Checks for OPENAI_API_KEY or GEMINI_API_KEY.
    2. If offline, runs a multi-intent dynamic speech pathology reasoning engine.
    """
    if history is None:
        history = []

    clean_msg = user_message.strip()
    msg_lower = clean_msg.lower()

    # 1. Check for OpenAI API Key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": clean_msg})

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=600
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI call failed, utilizing offline intelligence engine: {e}")

    # 2. Check for Google Gemini API Key
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        try:
            import urllib.request
            import json
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\nUser: {clean_msg}"}]}
                ]
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"Gemini call failed, utilizing offline intelligence engine: {e}")

    # =========================================================================
    # ADVANCED OFFLINE INTELLIGENCE & REASONING SYSTEM (ChatGPT/Gemini Style)
    # =========================================================================

    # A. GREETINGS & SMALL TALK
    if re.search(r'\b(hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening|greetings|howdy)\b', msg_lower):
        greetings = [
            "Hello! I am your **AI Speech Assistant & Coach**. How are you feeling today? I am here to help you practice pronunciation, provide communication tips, or answer questions about your speech journey.",
            "Hey there! It's wonderful to connect with you. Whether you'd like to practice vocal drills, learn about speech mechanics, or just chat about how your voice is feeling, I'm right here with you.",
            "Warm greetings! I am your AI speech companion. Feel free to speak or type anything—I'm ready to support you with vocal clarity, stuttering techniques, or daily motivation."
        ]
        return random.choice(greetings)

    # B. MOTIVATION, EMOTIONAL SUPPORT & ENCOURAGEMENT
    if re.search(r'\b(motivate|motivation|inspire|depressed|sad|frustrated|anxious|nervous|embarrassed|give\s+up|tired|hard|struggling|scared)\b', msg_lower):
        motivational_responses = [
            "### 🌟 You Are Stronger Than Any Stutter or Muscle Fatigue\n\n"
            "Take a slow, gentle breath right now. Drop your shoulders and release the tension in your jaw.\n\n"
            "**Here is what you need to remember today:**\n"
            "- **Your voice is worthy:** A pause, block, or slurred syllable does not diminish the intelligence, humor, and heart behind your words.\n"
            "- **Progress is cumulative:** Every time you practice a phrase, record an attempt, or speak up despite fear, your brain builds new neuromuscular pathways.\n"
            "- **History is full of giants who spoke atypically:** King George VI, Joe Biden, James Earl Jones, and Winston Churchill all faced severe speech impediments and went on to move the world.\n\n"
            "**Mini-exercise right now:** Inhale slowly through your nose for 4 seconds, then exhale with a relaxed, voiced sigh: *\"Aaahhh\"*. You are doing great. What is one small goal you'd like to conquer today?",

            "### 💪 Keep Going — Every Step Counts!\n\n"
            "Living with a speech condition can feel exhausting when people rush or interrupt. But remember:\n\n"
            "1. **Communication > Perfection:** The goal of speech is to connect with people, not to sound like a machine. What you have to say matters immensely.\n"
            "2. **Pacing gives you control:** When you feel tension building, pause. Silence is your ally, not your enemy.\n"
            "3. **You are making progress:** Just by opening this app and checking in, you are taking ownership of your health.\n\n"
            "I believe in your voice. Let's do a quick daily drill together in the **🏋️ Daily Practice** tab when you're ready!",

            "### 💙 A Gentle Reminder on Tough Days\n\n"
            "It's completely normal to have days where speaking feels heavier than usual. Vocal muscles get tired, anxiety flares up, and fluency fluctuates with stress.\n\n"
            "- Don't judge your entire recovery by a single hard morning.\n"
            "- Be compassionate with your vocal cords and articulation muscles.\n"
            "- Drink some warm water, practice gentle humming, and give yourself credit for showing up."
        ]
        return random.choice(motivational_responses)

    # C. STAMMERING / STUTTERING COPING & CLINICAL STRATEGIES
    if re.search(r'\b(stammer|stutter|block|blocks|fluency|repetition|prolongation|stuttering)\b', msg_lower):
        return (
            "### 🗣️ Evidence-Based Stammering & Fluency Strategies\n\n"
            "Stammering (stuttering) is a neurodevelopmental variation in speech motor timing. Here are clinical techniques taught by certified Speech-Language Pathologists:\n\n"
            "1. **Easy / Gentle Onset (Fluency Shaping):**\n"
            "   - Start vowel sounds (A, E, I, O, U) with a soft, breathy whisper before bringing your vocal cords together. Avoid hard glottal attacks.\n\n"
            "2. **Light Articulatory Contact:**\n"
            "   - When pronouncing plosives (/p/, /b/, /t/, /d/, /k/, /g/), touch your lips or tongue lightly without squeezing hard.\n\n"
            "3. **Pull-Out Technique (Stuttering Modification):**\n"
            "   - When caught in a tight block or syllable repetition, don't force through it. Deliberately slow down the sound, slide forward gently, and ease into the next syllable.\n\n"
            "4. **Diaphragmatic Belly Breathing:**\n"
            "   - Speak only on the exhale. Never push speech out when your lungs feel empty.\n\n"
            "💡 *Tip: Try our **Daily Practice Studio** with 'Medium (Phrases)' to practice smooth transitions!*"
        )

    # D. DYSARTHRIA DIAGNOSTICS & ARTICULATION DRILLS
    if re.search(r'\b(dysarthria|slur|slurred|clarity|articulation|stroke|als|parkinson|muscle|weakness)\b', msg_lower):
        return (
            "### 🩺 Understanding Dysarthria & Rehabilitation\n\n"
            "**Dysarthria** occurs when the neurological signals controlling the lips, tongue, soft palate, or vocal cords are impaired (often following stroke, head injury, ALS, or Parkinson's).\n\n"
            "**Key Articulation Drills for Clarity:**\n\n"
            "1. **Over-Articulation ('Biting the Words'):**\n"
            "   - Exaggerate your mouth and lip movements. Open your mouth wider than feels natural on open vowels like *'AH'* and *'OH'*.\n"
            "2. **Rate Control & Finger Tapping:**\n"
            "   - Slow down your rate of speech by 25%. Tap your finger on a table for each syllable: *\"To-day-is-Mon-day\"*.\n"
            "3. **End-Consonant Precision:**\n"
            "   - Dysarthric speech often drops word endings. Deliberately emphasize final consonants: *\"Ca-**T**\"*, *\"Foo-**D**\"*, *\"Cu-**P**\"*.\n"
            "4. **Respiratory Support:**\n"
            "   - Take a breath every 4–5 words rather than waiting until you run out of air.\n\n"
            "Would you like recommendations for tongue or lip strengthening exercises?"
        )

    # E. EXERCISES & PRACTICE
    if re.search(r'\b(exercise|practice|drill|drills|lip|tongue|jaw|mouth|vocal\s+cords)\b', msg_lower):
        return (
            "### 🏋️ 5-Minute Daily Oral-Motor & Speech Routine\n\n"
            "Perform these 3 times a day in front of a mirror:\n\n"
            "1. **Lip Pucker & Smile Stretch (10 reps):**\n"
            "   - Pucker your lips like a tight whistle for 3 seconds, then stretch into a broad exaggerated smile. Strengthens the *orbicularis oris*.\n"
            "2. **Tongue Tip Elevation ('T-D-N-L' Drill - 15 reps):**\n"
            "   - Touch your tongue tip firmly behind your top front teeth (alveolar ridge) and say: *\"Ta-Ta-Ta\"*, *\"Da-Da-Da\"*, *\"La-La-La\"*.\n"
            "3. **Pitch Glides (Resonance - 5 reps):**\n"
            "   - Glide your pitch from low to high on *\"Whoop!\"* to exercise vocal cord elongation.\n"
            "4. **Fuzzy Target Phrase Matching:**\n"
            "   - Switch to the **Daily Practice Studio** tab in this platform to test your real-time score on target sentences!"
        )

    # F. ACOUSTIC METRICS & SEVERITY SCORE
    if re.search(r'\b(score|severity|percentage|jitter|shimmer|hnr|mfcc|pitch|metric|metrics|svm|mlp)\b', msg_lower):
        return (
            "### 📊 How the Diagnostic AI Analyzes Your Voice\n\n"
            "Our system extracts **26 clinical acoustic features** from your audio:\n\n"
            "- **Jitter (Pitch Stability):** Measures cycle-to-cycle frequency variations. Higher jitter indicates vocal tremor or muscular instability.\n"
            "- **Shimmer (Loudness Stability):** Measures amplitude perturbation. Higher shimmer reflects breathiness or glottal closure issues.\n"
            "- **HNR (Harmonics-to-Noise Ratio):** Measures the purity of your voice compared to background acoustic turbulence.\n"
            "- **MFCCs (Mel-Frequency Cepstral Coefficients):** 13 frequency band coefficients capturing vocal tract shape and phoneme articulation.\n\n"
            "**Classification Severity Ranges:**\n"
            "- **0% – 30% (Typical)**: High stability, clear spectral peaks.\n"
            "- **30% – 60% (Mild)**: Minor perturbation, easily understood in conversation.\n"
            "- **60% – 80% (Moderate)**: Significant acoustic variation, benefits from pacing techniques.\n"
            "- **80%+ (Severe)**: High acoustic noise; tele-consultation with an SLP is recommended."
        )

    # G. WHATSAPP & SHARING
    if re.search(r'\b(whatsapp|share|contact|contacts|family|message|text)\b', msg_lower):
        return (
            "### 💬 Effortless Assistive Communication\n\n"
            "You can use the **Chat with Friends & Family** tab for real-time assistive talking:\n\n"
            "1. **Speak or Type:** Click the microphone or type directly into the transcript box.\n"
            "2. **AI Correction:** Faster-Whisper transcribes your voice into clean text, eliminating disfluent repetitions.\n"
            "3. **One-Click WhatsApp:** Click **'Share via WhatsApp'** to instantly send the text to any contact.\n"
            "4. **Custom Contacts:** You can now add and manage your own personal WhatsApp contacts (doctor, family, friends) with custom phone numbers!"
        )

    # H. GENERAL ASSISTANT / WHO ARE YOU / HELP
    if re.search(r'\b(who\s+are\s+you|what\s+can\s+you\s+do|help|features|about)\b', msg_lower):
        return (
            "### 🤖 Welcome to Your Speech Accessibility Suite\n\n"
            "I am your dedicated **AI Speech Assistant**, tailored specifically for atypical speech support.\n\n"
            "**Here is everything we can do together:**\n"
            "1. **Diagnose Speech:** Classify voice samples into *Typical*, *Dysarthria*, or *Stammer* using SVM, Random Forest, or MLP models.\n"
            "2. **Voice-to-Text Chat:** Transcribe spoken audio to text for instant WhatsApp and SMS messaging.\n"
            "3. **Voice AI Recognition:** You can talk to me directly using the 🎙️ mic button—I recognize stammering and reconstruct what you meant!\n"
            "4. **Daily Practice Studio:** Read target sentences and get instant pronunciation accuracy scores.\n"
            "5. **Therapist Directory:** Book tele-consultations with certified Speech-Language Pathologists.\n\n"
            "What would you like to explore first?"
        )

    # I. DEFAULT INTELLIGENT CONVERSATIONAL RESPONSE (Always responsive & context-aware!)
    # Avoids ever repeating the exact same generic string!
    context_intros = [
        f"Thank you for sharing that with me regarding **\"{clean_msg}\"**.",
        f"I hear you clearly on **\"{clean_msg}\"**.",
        f"That is an important thought regarding **\"{clean_msg}\"**."
    ]
    intro = random.choice(context_intros)

    return (
        f"{intro}\n\n"
        "As your speech companion, I am dedicated to helping you communicate with clarity and confidence.\n\n"
        "**Helpful Next Steps:**\n"
        "- If you are feeling tension or difficulty articulating, try taking a diaphragmatic breath and speaking at an easy, measured pace.\n"
        "- You can ask me for **specific vocal drills**, **tips for phone anxiety**, or **how our machine learning models evaluate voice samples**.\n"
        "- You can also tap the 🎙️ **Microphone icon** below to speak your thoughts aloud to practice your vocal delivery!"
    )
