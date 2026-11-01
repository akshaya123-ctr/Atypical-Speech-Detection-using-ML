import streamlit as st
from sharing.share_manager import generate_whatsapp_share_url, prepare_contact_share_links
from database.db_manager import get_contacts, add_contact, delete_contact, get_recent_speech_checks

def render_share_tab():
    st.markdown("""
    <div class='fluent-card'>
        <h2>📤 Communication & WhatsApp Sharing</h2>
        <p style='color: #64748B; font-size: 16px;'>
            Instantly share your transcribed speech with caregivers, family, or friends using pre-filled WhatsApp links.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 1. Select Speech Transcript to Share")
        checks = get_recent_speech_checks(limit=10)
        
        if checks:
            check_options = [f"{c['timestamp']} - \"{c['transcript'][:40]}...\"" for c in checks]
            selected_idx = st.selectbox("Choose Recent Check", range(len(check_options)), format_func=lambda i: check_options[i])
            share_text = checks[selected_idx]["transcript"]
        else:
            share_text = st.text_area("Enter custom message / transcript to share", "Hello! Here is my transcribed speech sample.")
            
        st.markdown("#### Text to Share:")
        st.code(share_text, language=None)
        
        st.markdown("#### Quick Actions:")
        scol1, scol2 = st.columns(2)
        with scol1:
            wa_gen_url = generate_whatsapp_share_url(share_text)
            st.markdown(f"<a href='{wa_gen_url}' target='_blank' style='text-decoration:none;'><button style='width:100%; min-height:50px; background-color:#25D366; color:white; border-radius:12px; border:none; font-weight:bold;'>📱 General WhatsApp Share</button></a>", unsafe_allow_html=True)
        with scol2:
            st.write("*(Click button above to open WhatsApp contact picker)*")

    with col2:
        st.markdown("### 2. Saved Contacts List")
        contacts_with_links = prepare_contact_share_links(share_text)
        
        if contacts_with_links:
            for c in contacts_with_links:
                with st.expander(f"👤 {c['name']} ({c['phone_number']})", expanded=True):
                    st.write(f"**Notes:** {c['notes']}")
                    ccol1, ccol2 = st.columns([3, 1])
                    with ccol1:
                        st.markdown(f"<a href='{c['whatsapp_url']}' target='_blank' style='text-decoration:none;'><button style='width:100%; min-height:42px; background-color:#25D366; color:white; border-radius:10px; border:none; font-weight:bold; font-size:14px;'>💬 Send WhatsApp to {c['name']}</button></a>", unsafe_allow_html=True)
                    with ccol2:
                        if st.button("🗑️ Delete", key=f"del_c_{c['id']}"):
                            delete_contact(c['id'])
                            st.rerun()
        else:
            st.info("No saved contacts found. Add a contact below!")
            
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("### ➕ Add New Contact")
        with st.form("add_contact_form"):
            cname = st.text_input("Contact Name", placeholder="e.g. Mom, Dr. Smith, Caregiver")
            ccol_code, ccol_num = st.columns([1, 2])
            with ccol_code:
                country_code_choice = st.selectbox("Country Code", ["+91 (India)", "+1 (US/CA)", "+44 (UK)", "+61 (Australia)", "+971 (UAE)", "+65 (Singapore)", "+49 (Germany)", "+33 (France)", "Other"])
            with ccol_num:
                cphone = st.text_input("Mobile Number", placeholder="e.g. 9876543210")
            cnotes = st.text_input("Notes (Optional)", placeholder="e.g. Primary speech therapist")
            submitted = st.form_submit_button("Save Contact")
            
            if submitted:
                if cname and cphone:
                    clean_phone = cphone.strip().replace(" ", "").replace("-", "")
                    if not clean_phone.startswith("+"):
                        if clean_phone.startswith("0"):
                            clean_phone = clean_phone[1:]
                        code_val = country_code_choice.split()[0] if country_code_choice != "Other" else ""
                        clean_phone = f"{code_val}{clean_phone}"
                    add_contact(cname, clean_phone, cnotes)
                    st.success(f"Saved contact {cname} ({clean_phone})!")
                    st.rerun()
                else:
                    st.error("Please provide both name and phone number.")
