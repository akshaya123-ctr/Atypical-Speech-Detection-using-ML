import streamlit as st
import streamlit.components.v1 as components
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Page configuration
st.set_page_config(
    page_title="Atypical Speech Detection System",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Seamless Dark Styling: Hide Streamlit navbars, footers, and padding
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
div[data-testid="stToolbar"] {display: none;}
div[data-testid="stDecoration"] {display: none;}
div[data-testid="stStatusWidget"] {display: none;}
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    max-width: 100% !important;
}
iframe {
    width: 100vw;
    height: 100vh;
    border: none;
    display: block;
}
body {
    background-color: #0A0B0E;
    overflow-x: hidden;
}
</style>
""", unsafe_allow_html=True)

# Direct integration with the high-fidelity diagnostic web app
FASTAPI_PORT = int(os.environ.get("PORT", 8080))
SERVER_URL = f"http://localhost:{FASTAPI_PORT}"

# Render full screen responsive UI
components.iframe(SERVER_URL, height=1800, scrolling=True)
