import streamlit as st
import os

def load_css():
    css_path = os.path.join("ui", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_header(current_step: int = 2):
    step1_class = "active" if current_step >= 1 else ""
    step1_num = "active" if current_step > 1 else ("current" if current_step == 1 else "")
    
    step2_class = "active" if current_step >= 2 else ""
    step2_num = "active" if current_step > 2 else ("current" if current_step == 2 else "")
    
    step3_class = "active" if current_step >= 3 else ""
    step3_num = "current" if current_step == 3 else ""
    
    st.markdown(f"""
    <div class='diag-header'>
        <div class='diag-pill-tag'>🎙️ Speech Diagnostics</div>
        <h1 class='diag-title'>Atypical Speech <span class='diag-title-highlight'>Detection System</span></h1>
        <p class='diag-subtitle'>
            Select a machine learning model, record or upload patient speech, and get instant predictions across <b>Typical</b>, <b>Dysarthria</b>, and <b>Stammer</b> with detailed clinical metrics.
        </p>
        
        <div class='diag-stepper'>
            <div class='step-item {step1_class}'>
                <span class='step-num {step1_num}'>1</span> Select Model
            </div>
            <div class='step-divider'></div>
            <div class='step-item {step2_class}'>
                <span class='step-num {step2_num}'>2</span> Input Speech
            </div>
            <div class='step-divider'></div>
            <div class='step-item {step3_class}'>
                <span class='step-num {step3_num}'>3</span> View Results
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
