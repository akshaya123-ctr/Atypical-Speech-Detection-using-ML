import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.db_manager import (
    log_speech_check, get_recent_speech_checks,
    log_practice_session, get_practice_history,
    add_contact, get_contacts, delete_contact
)

def test_database_crud():
    cid = log_speech_check("dysarthria", 65.5, "moderate", 88.0, "Testing speech check", 1.2)
    assert cid > 0
    checks = get_recent_speech_checks(limit=10)
    assert len(checks) > 0
    
    pid = log_practice_session("voice", "Hello world", "Hello world", 100.0, "Great job!")
    assert pid > 0
    history = get_practice_history(limit=10)
    assert len(history) > 0
    
    contact_id = add_contact("Test Contact", "+9999999999", "Test notes")
    assert contact_id > 0
    contacts = get_contacts()
    names = [c["name"] for c in contacts]
    assert "Test Contact" in names
    
    delete_contact(contact_id)
