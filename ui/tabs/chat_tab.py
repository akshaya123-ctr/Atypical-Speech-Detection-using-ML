import streamlit as st
import tempfile
from chatbot.ai_assistant import query_ai_assistant, SUGGESTED_PROMPTS
from utils.whisper_stt import transcribe_speech

def render_chat_tab():
    st.markdown("""
    <div class='fluent-card'>
        <h2>💬 Ask AI Speech Assistant</h2>
        <p style='color: #64748B; font-size: 16px;'>
            Ask questions about your speech checks, dysarthria practice tips, or how to use the app. Type or speak your question!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.warning("⚠️ **Medical Disclaimer**: The AI Assistant provides educational guidance and accessibility tools. It does not provide medical diagnosis. Please consult a qualified Speech-Language Pathologist for clinical medical advice.")
    
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {"role": "assistant", "content": "Hello! I am your AI Speech Assistant. How can I help you today?"}
        ]
        
    # Suggested Prompt Chips
    st.markdown("#### Suggested Questions:")
    chip_cols = st.columns(len(SUGGESTED_PROMPTS))
    selected_prompt = None
    for idx, prompt in enumerate(SUGGESTED_PROMPTS):
        with chip_cols[idx]:
            if st.button(prompt, key=f"chip_{idx}"):
                selected_prompt = prompt
                
    # Voice Input Mode Option for Chat
    st.markdown("#### Voice Query Input")
    voice_audio = st.audio_input("Speak question to AI", key="chat_voice")
    if voice_audio:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(voice_audio.read())
            voice_path = f.name
            
        with st.spinner("Transcribing spoken question..."):
            stt = transcribe_speech(voice_path)
            if stt["transcript"]:
                selected_prompt = stt["transcript"]
                
    # Render Chat Trajectory
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Process User Text Input or Clicked Prompt
    user_input = st.chat_input("Type your question here...")
    prompt_to_process = user_input or selected_prompt
    
    if prompt_to_process:
        # Display user message
        st.session_state["chat_messages"].append({"role": "user", "content": prompt_to_process})
        with st.chat_message("user"):
            st.markdown(prompt_to_process)
            
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("AI thinking..."):
                response_text = query_ai_assistant(prompt_to_process, st.session_state["chat_messages"])
                st.markdown(response_text)
                st.session_state["chat_messages"].append({"role": "assistant", "content": response_text})
