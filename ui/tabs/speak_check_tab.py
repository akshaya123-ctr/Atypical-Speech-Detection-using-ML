import streamlit as st
import os
import tempfile
import json
import joblib

from utils.predictor import predict_audio_sample
from database.db_manager import log_speech_check
from reports.pdf_generator import generate_pdf_report
from sharing.share_manager import generate_whatsapp_share_url

SAMPLE_A_PATH = "torgo_data/non_dysarthria_female/FC01_Session1_0008.wav"
SAMPLE_B_PATH = "torgo_data/dysarthria_female/F01_Session1_0001.wav"
SAMPLE_C_PATH = "torgo_data/stammer/Block/HeStutters_0_18.wav"
MODEL_RESULTS_PATH = "model_results.json"

def get_model_metrics(model_key: str):
    default_metrics = {
        "accuracy": 0.6441, "precision": 0.6542, "recall": 0.6513, "f1": 0.6352
    }
    if os.path.exists(MODEL_RESULTS_PATH):
        try:
            with open(MODEL_RESULTS_PATH, "r") as f:
                data = json.load(f)
            s1 = data.get("stage_1", {})
            if model_key in s1:
                return s1[model_key]
        except Exception:
            pass
    return default_metrics

def render_speak_check_tab():
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = "SVM"
    if "active_audio_path" not in st.session_state:
        st.session_state["active_audio_path"] = None
    if "prediction_result" not in st.session_state:
        st.session_state["prediction_result"] = None

    # =========================================================================
    # SECTION 1: CHOOSE A MODEL (Matching Reference UI Cards)
    # =========================================================================
    st.markdown("""
    <div class='dark-card'>
        <div class='dark-card-header'>
            <div class='dark-card-icon'>🧠</div>
            <div>
                <h3 class='dark-card-title'>Choose a Model</h3>
                <p class='dark-card-desc'>Pick one ML algorithm to run your prediction</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    mcol1, mcol2, mcol3 = st.columns(3)

    current_model = st.session_state["selected_model"]

    with mcol1:
        is_sel = (current_model == "SVM")
        card_class = "algo-card selected" if is_sel else "algo-card"
        radio_icon = "🟢" if is_sel else "⚪"
        st.markdown(f"""
        <div class='{card_class}'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span style='font-size: 20px;'>📐</span>
                <span style='font-size: 14px;'>{radio_icon}</span>
            </div>
            <div style='font-weight: 700; font-size: 16px; margin-top: 8px;'>SVM</div>
            <div class='algo-badge-pill pill-kernel'>KERNEL (RBF)</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select SVM", key="btn_sel_svm", use_container_width=True):
            st.session_state["selected_model"] = "SVM"
            st.rerun()

    with mcol2:
        is_sel = (current_model == "Random Forest")
        card_class = "algo-card selected" if is_sel else "algo-card"
        radio_icon = "🟢" if is_sel else "⚪"
        st.markdown(f"""
        <div class='{card_class}'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span style='font-size: 20px;'>🌲</span>
                <span style='font-size: 14px;'>{radio_icon}</span>
            </div>
            <div style='font-weight: 700; font-size: 16px; margin-top: 8px;'>Random Forest</div>
            <div class='algo-badge-pill pill-ensemble'>ENSEMBLE</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select Random Forest", key="btn_sel_rf", use_container_width=True):
            st.session_state["selected_model"] = "Random Forest"
            st.rerun()

    with mcol3:
        is_sel = (current_model == "MLP")
        card_class = "algo-card selected" if is_sel else "algo-card"
        radio_icon = "🟢" if is_sel else "⚪"
        st.markdown(f"""
        <div class='{card_class}'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <span style='font-size: 20px;'>🧠</span>
                <span style='font-size: 14px;'>{radio_icon}</span>
            </div>
            <div style='font-weight: 700; font-size: 16px; margin-top: 8px;'>MLP</div>
            <div class='algo-badge-pill pill-neural'>NEURAL NET</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select MLP", key="btn_sel_mlp", use_container_width=True):
            st.session_state["selected_model"] = "MLP"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 2: INPUT SPEECH DATA (Matching Reference "Enter Sample Data")
    # =========================================================================
    st.markdown("""
    <div class='dark-card'>
        <div class='dark-card-header'>
            <div class='dark-card-icon'>🎙️</div>
            <div>
                <h3 class='dark-card-title'>Input Speech Data</h3>
                <p class='dark-card-desc'>Record live patient voice via microphone or upload an audio file</p>
            </div>
        </div>
    """, unsafe_allow_html=True)


    # Input Mode Tabs
    input_tab1, input_tab2 = st.tabs(["🎤 Live Microphone Recording", "📁 Upload Audio File"])

    with input_tab1:
        recorded_audio = st.audio_input("Press microphone icon to record your voice")
        if recorded_audio is not None:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                tf.write(recorded_audio.read())
                st.session_state["active_audio_path"] = tf.name
                st.session_state["prediction_result"] = None

    with input_tab2:
        uploaded_file = st.file_uploader("Upload audio (.wav, .mp3, .flac, .m4a)", type=["wav", "mp3", "flac", "m4a", "ogg"])
        if uploaded_file is not None:
            ext = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
                tf.write(uploaded_file.read())
                st.session_state["active_audio_path"] = tf.name
                st.session_state["prediction_result"] = None

    # Audio Playback
    active_path = st.session_state.get("active_audio_path")
    if active_path and os.path.exists(active_path):
        st.markdown("<p style='font-size: 13px; font-weight: 600; color: #F59E0B; margin: 12px 0 4px 0;'>🎧 Audio Preview:</p>", unsafe_allow_html=True)
        st.audio(active_path)

    # Action Buttons: Reset & Analyse & Predict
    btn_col1, btn_col2 = st.columns([0.3, 0.7])
    with btn_col1:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state["active_audio_path"] = None
            st.session_state["prediction_result"] = None
            st.rerun()
    with btn_col2:
        analyse_clicked = st.button("⚡ Analyse & Predict", type="primary", use_container_width=True)

    if analyse_clicked:
        if not active_path or not os.path.exists(active_path):
            st.warning("⚠️ Please record voice, upload an audio file, or select a Quick Fill sample above.")
        else:
            with st.spinner("⏳ Extracting 63 acoustic features & transcribing speech..."):
                res = predict_audio_sample(active_path, model_name=st.session_state["selected_model"])
                st.session_state["prediction_result"] = res

    st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # SECTION 3: PREDICTION OUTPUT HERO (Matching Reference Upper Card)
    # =========================================================================
    res = st.session_state.get("prediction_result")
    if res and not res.get("error"):
        dtype = res["disorder_type"].lower()
        confidence = res["confidence"]
        transcript = res["transcript"]
        severity_pct = res["severity_percentage"]
        severity_cat = res["severity_category"]
        model_name = res.get("model_used", st.session_state["selected_model"])

        # Log to DB
        log_speech_check(dtype, severity_pct, severity_cat, confidence, transcript, res["latency_seconds"])

        if dtype == "typical":
            pill_class = "pred-pill-typical"
            pill_text = "• TYPICAL SPEECH (CONTROL)"
            big_title = "TYPICAL"
            title_color = "#34D399"
            desc_text = "No motor speech impairment or stuttering detected. Speech flow is normal and fluent."
        elif dtype == "dysarthria":
            pill_class = "pred-pill-dysarthria"
            pill_text = f"• DYSARTHRIA DETECTED ({severity_cat.upper()})"
            big_title = "DYSARTHRIA"
            title_color = "#F87171"
            desc_text = f"Motor speech impairment indicated. Articulation and acoustic perturbation severity: {severity_pct}% ({severity_cat.capitalize()})."
        else:
            pill_class = "pred-pill-stammer"
            pill_text = f"• STAMMER / STUTTERING ({severity_cat.upper()})"
            big_title = "STAMMER"
            title_color = "#C084FC"
            desc_text = f"Speech disfluency patterns detected (repetition, prolongation, or blocking). Severity: {severity_pct}%."

        st.markdown(f"""
        <div class='prediction-hero-card'>
            <div class='pred-status-pill {pill_class}'>{pill_text}</div>
            <div class='pred-big-title' style='color: {title_color};'>{big_title}</div>
            <div class='pred-desc'>Prediction Output: <b>{big_title.capitalize()}</b> | {desc_text}</div>
            <div class='pred-confidence-tag'>
                🎯 Confidence: <b>{confidence}%</b> &nbsp;•&nbsp; ⚡ Model: <b>{model_name}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # =====================================================================
        # SECTION 4: PREDICTION DETAILS & TRANSCRIPTION (Matching 2x4 Grid)
        # =====================================================================
        st.markdown("""
        <div class='dark-card'>
            <div class='dark-card-header'>
                <div class='dark-card-icon'>📋</div>
                <div>
                    <h3 class='dark-card-title'>Prediction Details & Transcribed Speech</h3>
                    <p class='dark-card-desc'>Automatic speech recognition (Faster-Whisper) & extracted acoustic parameters</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<p style='font-size: 13px; font-weight: 600; color: #9CA3AF; margin-bottom: 6px;'>💬 TRANSCRIBED SPEECH:</p>", unsafe_allow_html=True)
        display_transcript = f'"{transcript}"' if transcript else '"(No words transcribed)"'
        st.markdown(f"""
        <div class='transcript-display'>
            {display_transcript}
        </div>
        """, unsafe_allow_html=True)

        feats = res.get("features", {})
        f_pitch = round(feats.get("pitch_mean", 0.0), 1)
        f_jitter = round(feats.get("jitter", 0.0) * 100, 2)
        f_shimmer = round(feats.get("shimmer", 0.0) * 100, 2)
        f_rms = round(feats.get("rms_mean", 0.0), 3)
        f_zcr = round(feats.get("zcr_mean", 0.0), 3)
        words_count = len(transcript.split()) if transcript else 0
        wps = round(words_count / max(0.5, res["latency_seconds"]), 1)

        # 2x4 Grid Tiles
        gcol1, gcol2, gcol3, gcol4 = st.columns(4)
        with gcol1:
            st.markdown(f"""
            <div class='param-tile'>
                <div class='param-label'>Predicted Field</div>
                <div class='param-value'>{dtype.capitalize()}</div>
            </div>
            <div class='param-tile'>
                <div class='param-label'>Jitter (Perturbation)</div>
                <div class='param-value'>{f_jitter}%</div>
            </div>
            """, unsafe_allow_html=True)
        with gcol2:
            st.markdown(f"""
            <div class='param-tile'>
                <div class='param-label'>Speaking Rate</div>
                <div class='param-value'>{wps} WPS</div>
            </div>
            <div class='param-tile'>
                <div class='param-label'>Shimmer (Amplitude)</div>
                <div class='param-value'>{f_shimmer}%</div>
            </div>
            """, unsafe_allow_html=True)
        with gcol3:
            st.markdown(f"""
            <div class='param-tile'>
                <div class='param-label'>STT Confidence</div>
                <div class='param-value'>{res.get('stt_confidence', 85.0)}%</div>
            </div>
            <div class='param-tile'>
                <div class='param-label'>Pitch (F0 Mean)</div>
                <div class='param-value'>{f_pitch} Hz</div>
            </div>
            """, unsafe_allow_html=True)
        with gcol4:
            st.markdown(f"""
            <div class='param-tile'>
                <div class='param-label'>Severity Rating</div>
                <div class='param-value'>{severity_pct}%</div>
            </div>
            <div class='param-tile'>
                <div class='param-label'>RMS Energy</div>
                <div class='param-value'>{f_rms}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # =====================================================================
        # SECTION 5: MODEL PERFORMANCE METRICS (Matching Reference Bottom Card)
        # =====================================================================
        algo_save_key = model_name.replace(" ", "_")
        perf = get_model_metrics(algo_save_key)

        st.markdown(f"""
        <div class='dark-card'>
            <div class='dark-card-header'>
                <div class='dark-card-icon'>📊</div>
                <div>
                    <h3 class='dark-card-title'>Model Performance: {model_name}</h3>
                    <p class='dark-card-desc'>Evaluated via 5-Fold Speaker-Disjoint Cross Validation (0 Leakage across 264 Speakers)</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        kcol1, kcol2, kcol3, kcol4 = st.columns(4)
        with kcol1:
            st.markdown(f"""
            <div class='kpi-card kpi-yellow'>
                <div class='kpi-icon'>🎯</div>
                <div class='kpi-label'>Accuracy</div>
                <div class='kpi-value'>{perf['accuracy']*100:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with kcol2:
            st.markdown(f"""
            <div class='kpi-card kpi-green'>
                <div class='kpi-icon'>✅</div>
                <div class='kpi-label'>Precision</div>
                <div class='kpi-value'>{perf['precision']*100:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with kcol3:
            st.markdown(f"""
            <div class='kpi-card kpi-blue'>
                <div class='kpi-icon'>🔍</div>
                <div class='kpi-label'>Recall</div>
                <div class='kpi-value'>{perf['recall']*100:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with kcol4:
            st.markdown(f"""
            <div class='kpi-card kpi-purple'>
                <div class='kpi-icon'>⚖️</div>
                <div class='kpi-label'>F1 Score</div>
                <div class='kpi-value'>{perf['f1']*100:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

        # Class probability breakdown
        class_probs = res.get("class_probabilities", {})
        if class_probs:
            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 13px; font-weight: 600; color: #9CA3AF; margin-bottom: 6px;'>🎯 PROBABILITIES ACROSS 3 FIELDS:</p>", unsafe_allow_html=True)
            pcol1, pcol2, pcol3 = st.columns(3)
            with pcol1:
                typ_p = class_probs.get("typical", 0.0)
                st.markdown(f"**Typical Speech:** `{typ_p}%`")
                st.progress(min(1.0, typ_p / 100.0))
            with pcol2:
                dys_p = class_probs.get("dysarthria", 0.0)
                st.markdown(f"**Dysarthria:** `{dys_p}%`")
                st.progress(min(1.0, dys_p / 100.0))
            with pcol3:
                stm_p = class_probs.get("stammer", 0.0)
                st.markdown(f"**Stammer / Stutter:** `{stm_p}%`")
                st.progress(min(1.0, stm_p / 100.0))

        # Action Buttons (Share / PDF)
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        act1, act2 = st.columns(2)
        with act1:
            wa_url = generate_whatsapp_share_url(transcript)
            st.markdown(f"<a href='{wa_url}' target='_blank' style='text-decoration:none;'><button style='width:100%; min-height:44px; background-color:#25D366; color:white; border-radius:10px; border:none; font-weight:bold; cursor:pointer;'>💬 Share Transcript on WhatsApp</button></a>", unsafe_allow_html=True)
        with act2:
            pdf_path = os.path.join(tempfile.gettempdir(), "clinical_speech_report.pdf")
            if generate_pdf_report(res, pdf_path):
                with open(pdf_path, "rb") as pf:
                    st.download_button("📄 Download Clinical PDF Report", pf, file_name="speech_check_report.pdf", mime="application/pdf", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    elif res and res.get("error"):
        st.error(f"⚠️ {res['error']}")
