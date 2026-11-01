import urllib.parse
from typing import List, Dict, Any, Optional
from database.db_manager import get_contacts

def generate_whatsapp_share_url(text: str, phone_number: Optional[str] = None) -> str:
    """
    Generates a wa.me share URL for WhatsApp.
    If phone_number is provided, opens directly to that contact.
    Otherwise opens WhatsApp contact selector with text pre-filled.
    """
    encoded_text = urllib.parse.quote(text.strip())
    if phone_number:
        clean_phone = "".join([c for c in phone_number if c.isdigit() or c == '+'])
        if clean_phone.startswith('+'):
            clean_phone = clean_phone[1:]
        return f"https://wa.me/{clean_phone}?text={encoded_text}"
    else:
        return f"https://wa.me/?text={encoded_text}"

def prepare_contact_share_links(transcript: str) -> List[Dict[str, Any]]:
    """
    Retrieves saved contacts and builds custom WhatsApp share links for each contact.
    """
    contacts = get_contacts()
    share_list = []
    
    for c in contacts:
        url = generate_whatsapp_share_url(transcript, c["phone_number"])
        share_list.append({
            "id": c["id"],
            "name": c["name"],
            "phone_number": c["phone_number"],
            "notes": c.get("notes", ""),
            "whatsapp_url": url
        })
        
    return share_list
