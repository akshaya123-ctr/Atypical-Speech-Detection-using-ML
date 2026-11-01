import streamlit as st
import os
import tempfile

from practice.coach import get_random_exercise, evaluate_speech_attempt, EXERCISES
from practice.video_captioner import add_captions_to_video
from utils.whisper_stt import transcribe_speech
from database.db_manager import log_practice_session

def render_practice_tab():
    st.markdown("""
    <div class='fluent-card'>
        <h2>🏋️ Practice & Training Studio</h2>
        <p style='color: #64748B; font-size: 16px;'>
            Practice speech exercises at your own comfortable pace with gentle, encouraging feedback. No timers, no pressure!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_voice, tab_video = st.tabs(["🎤 Voice Practice", "📹 Webcam Video Exercises"])
    
    # --- VOICE PRACTICE ---
    with tab_voice:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### Select Exercise Difficulty")
            difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"], key="voice_diff")
            
            if "current_target_phrase" not in st.session_state or st.button("🔄 Get Next Phrase", key="btn_next"):
                st.session_state["current_target_phrase"] = get_random_exercise(difficulty)
                
            target_phrase = st.session_state.get("current_target_phrase", "Hello")
            
            st.markdown("<br/>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style='background-color: #EFF6FF; border: 2.5px solid #3B82F6; border-radius: 16px; padding: 24px; text-align: center;'>
                <span style='color: #1E40AF; font-size: 16px; font-weight: bold;'>TARGET PHRASE TO SPEAK:</span><br/>
                <span style='color: #1E293B; font-size: 28px; font-weight: 800; font-family: sans-serif;'>"{target_phrase}"</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br/>", unsafe_allow_html=True)
            
            st.markdown("#### Record Your Attempt")
            audio_attempt = st.audio_input("Record speech attempt", key="voice_rec")
            
        with col2:
            st.markdown("### Feedback & Scoring")
            if audio_attempt:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio_attempt.read())
                    temp_audio_path = f.name
                    
                with st.spinner("Evaluating speech attempt..."):
                    stt = transcribe_speech(temp_audio_path)
                    spoken_text = stt["transcript"]
                    eval_res = evaluate_speech_attempt(target_phrase, spoken_text)
                    
                # Log to DB
                log_practice_session("voice", target_phrase, spoken_text, eval_res["match_score_pct"], eval_res["feedback_msg"])
                
                # Feedback Display
                score_pct = eval_res["match_score_pct"]
                st.markdown(f"### Score: <span style='color: #2563EB;'>{score_pct}% Match</span>", unsafe_allow_html=True)
                st.info(f"{eval_res['badge']} | {eval_res['feedback_msg']}")
                
                st.markdown("#### Spoken Transcript:")
                st.write(f"*{spoken_text}*")
                
                st.markdown("#### Word-by-Word Analysis:")
                diff_cols = st.columns(len(eval_res["word_diff"]) if eval_res["word_diff"] else 1)
                for item in eval_res["word_diff"]:
                    w = item["word"]
                    status = item["status"]
                    if status == "correct":
                        st.markdown(f"<span style='color:green; font-weight:bold;'>✓ {w}</span> ", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color:orange; font-style:italic;'>~ {w}</span> ", unsafe_allow_html=True)
            else:
                st.info("👈 Press the microphone button on the left to record your attempt!")

    # --- WEBCAM VIDEO EXERCISES ---
    with tab_video:
        st.markdown("### 📹 Pronunciation Practice with Video Captions")
        st.write("Record a video clip of yourself speaking to practice mouth and lip movements. The app will automatically overlay your transcribed captions!")
        
        vcol1, vcol2 = st.columns([1, 1])
        with vcol1:
            uploaded_video = st.file_uploader("Upload webcam recording (.mp4, .mov, .avi)", type=["mp4", "mov", "avi"])
            video_target = st.text_input("Spoken Phrase / Note for Captions", "Practice makes progress every day.")
            
        with vcol2:
            if uploaded_video:
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                    f.write(uploaded_video.read())
                    in_vpath = f.name
                    
                out_vpath = in_vpath.replace(".mp4", "_captioned.mp4")
                
                with st.spinner("Transcribing spoken audio & rendering captions with OpenCV..."):
                    stt = transcribe_speech(in_vpath)
                    caption_text = stt["transcript"] if stt["transcript"] else video_target
                    res_vpath = add_captions_to_video(in_vpath, caption_text, out_vpath)
                    
                st.success("✅ Captioned Video Ready!")
                st.video(res_vpath)
                with open(res_vpath, "rb") as vf:
                    st.download_button("💾 Download Captioned Video", vf, file_name="practice_speech_captioned.mp4", mime="video/mp4")
            else:
                st.info("Upload a video recording to generate overlaid captions for self-review.")
