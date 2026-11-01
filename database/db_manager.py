import hashlib
import hmac
import secrets
import sqlite3
import os
import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join("database", "speech_app.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Speech Detection Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS speech_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        disorder_type TEXT,
        severity_pct REAL,
        severity_category TEXT,
        confidence REAL,
        transcript TEXT,
        latency_seconds REAL
    )
    """)
    
    # 2. Practice & Coaching Sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS practice_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        exercise_type TEXT,
        target_phrase TEXT,
        spoken_transcript TEXT,
        match_score_pct REAL,
        feedback_msg TEXT,
        video_path TEXT
    )
    """)
    
    # 3. Saved Contacts for WhatsApp Sharing
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        notes TEXT
    )
    """)
    
    # 4. Registered Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        condition TEXT,
        age INTEGER,
        phone TEXT,
        primary_goal TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 5. Therapist Consultations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consultations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        therapist_name TEXT,
        session_type TEXT,
        preferred_date TEXT,
        preferred_time TEXT,
        notes TEXT,
        status TEXT DEFAULT 'Confirmed',
        clinical_notes TEXT DEFAULT '',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 6. Prescribed Clinical Drills
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prescribed_drills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        therapist_name TEXT NOT NULL,
        target_phrase TEXT NOT NULL,
        difficulty TEXT DEFAULT 'Easy',
        instructions TEXT,
        status TEXT DEFAULT 'Assigned',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Check if clinical_notes column exists in consultations
    try:
        cursor.execute("PRAGMA table_info(consultations)")
        c_cols = [c["name"] for c in cursor.fetchall()]
        if "clinical_notes" not in c_cols:
            cursor.execute("ALTER TABLE consultations ADD COLUMN clinical_notes TEXT DEFAULT ''")
    except Exception:
        pass

    # Seed Default Users (Patient & SLP Clinicians)
    
    # Seed demo data only when explicitly enabled
    if os.getenv("ENABLE_DEMO_DATA", "false").lower() == "true":

        # Demo Users
        demo_users = [
            ('Alex Taylor', 'patient@speech.ai', 'password123', 'Dysarthria (Mild-Moderate)', 34, '+1 (555) 234-5678', 'Daily articulation clarity and phone conversations'),
            ('Maya Lin', 'maya@speech.ai', 'password123', 'Stammer / Stuttering (Fluency)', 26, '+1 (555) 432-8765', 'Reduce blocking on plosive consonants during meetings'),
            ('Dr. Sarah Jenkins, CCC-SLP', 'slp@speech.ai', 'password123', 'Speech-Language Pathologist (SLP)', 42, '+1 (555) 890-1234', 'Senior Clinical Neurological SLP - Dysarthria Specialist'),
            ('Dr. Sarah Jenkins, CCC-SLP', 'sarah.jenkins@speech.ai', 'password123', 'Speech-Language Pathologist (SLP)', 42, '+1 (555) 890-1234', 'Senior Clinical Neurological SLP - Dysarthria Specialist'),
            ('Dr. Rajesh Kumar, MS, SLP', 'rajesh.slp@speech.ai', 'password123', 'Speech-Language Pathologist (SLP)', 39, '+1 (555) 678-9012', 'Clinical Fluency Consultant - Stammering Rehabilitation')
        ]

        for u in demo_users:
            cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (u[1],))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                INSERT INTO users (name, email, password, condition, age, phone, primary_goal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    u[0], u[1], hash_password(u[2]),
                    u[3], u[4], u[5], u[6]
                ))

        # Demo Consultations
        cursor.execute("SELECT COUNT(*) FROM consultations")
        if cursor.fetchone()[0] == 0:
            demo_consultations = [
                (1, 'Alex Taylor', 'Dr. Sarah Jenkins, CCC-SLP', '1-on-1 Video Tele-Therapy (45 mins)', 'Tomorrow', '4:30 PM', 'Patient reports vocal fatigue and slurring during afternoon phone calls.', 'Confirmed', 'Review palatal elevation and respiratory breath support.'),
                (2, 'Maya Lin', 'Dr. Rajesh Kumar, MS, SLP', 'Clinical Diagnostic Intake Assessment', 'Thursday', '11:00 AM', 'Persistent stuttering blocks during work presentations; plosive consonants /p/ and /b/.', 'Confirmed', 'Introduce easy gentle vocal onset drills and diaphragmatic pacing.')
            ]

            for c in demo_consultations:
                cursor.execute("""
                INSERT INTO consultations
                (user_id, user_name, therapist_name, session_type, preferred_date, preferred_time, notes, status, clinical_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, c)

        # Demo Speech Checks
        cursor.execute("SELECT COUNT(*) FROM speech_checks")
        if cursor.fetchone()[0] == 0:
            demo_checks = [
                ('Dysarthria', 54.2, 'Moderate', 88.5, 'The patient demonstrated slurred articulation and reduced speech cadence.', 0.38),
                ('Stammer', 41.0, 'Mild-Moderate', 91.2, 'p-p-please schedule my practice session for tomorrow morning.', 0.42),
                ('Typical', 8.5, 'Typical', 96.0, 'Today is a wonderful day and I feel very confident speaking.', 0.35)
            ]

            for chk in demo_checks:
                cursor.execute("""
                INSERT INTO speech_checks
                (disorder_type, severity_pct, severity_category, confidence, transcript, latency_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
                """, chk)

        # Demo Practice Sessions
        cursor.execute("SELECT COUNT(*) FROM practice_sessions")
        if cursor.fetchone()[0] == 0:
            demo_practice = [
                ('Easy', 'Today is a wonderful day', 'Today is a wonderful day', 95.0, 'Excellent pacing and clean articulation!'),
                ('Medium', 'She sells seashells on the seashore', 'She sells sea shells seashore', 86.4, 'Great cadence; slight phoneme omission on second syllable.'),
                ('Hard', 'Proper preparation prevents poor performance', 'Proper preparation prevents poor performance', 92.1, 'Outstanding rhythm and fluency control.')
            ]

            for pr in demo_practice:
                cursor.execute("""
                INSERT INTO practice_sessions
                (exercise_type, target_phrase, spoken_transcript, match_score_pct, feedback_msg)
                VALUES (?, ?, ?, ?, ?)
                """, pr)

    conn.commit()
    conn.close()

# --- Speech Checks CRUD ---
def log_speech_check(disorder_type: str, severity_pct: float, severity_category: str,
                     confidence: float, transcript: str, latency_seconds: float) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO speech_checks (disorder_type, severity_pct, severity_category, confidence, transcript, latency_seconds)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (disorder_type, severity_pct, severity_category, confidence, transcript, latency_seconds))
    conn.commit()
    check_id = cursor.lastrowid
    conn.close()
    return check_id

def get_recent_speech_checks(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM speech_checks ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

# --- Practice Sessions CRUD ---
def log_practice_session(exercise_type: str, target_phrase: str, spoken_transcript: str,
                         match_score_pct: float, feedback_msg: str, video_path: Optional[str] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO practice_sessions (exercise_type, target_phrase, spoken_transcript, match_score_pct, feedback_msg, video_path)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (exercise_type, target_phrase, spoken_transcript, match_score_pct, feedback_msg, video_path))
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id

def get_practice_history(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM practice_sessions ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

# --- Contacts CRUD ---
def get_contacts(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if user_id column exists
        cursor.execute("PRAGMA table_info(saved_contacts)")
        cols = [c["name"] for c in cursor.fetchall()]
        if "user_id" not in cols:
            cursor.execute("ALTER TABLE saved_contacts ADD COLUMN user_id INTEGER DEFAULT NULL")
            conn.commit()

        if user_id:
            cursor.execute("SELECT * FROM saved_contacts WHERE user_id = ? OR user_id IS NULL ORDER BY id ASC", (user_id,))
        else:
            cursor.execute("SELECT * FROM saved_contacts ORDER BY id ASC")
    except Exception:
        cursor.execute("SELECT * FROM saved_contacts ORDER BY id ASC")
        
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def add_contact(name: str, phone_number: str, notes: str = "", user_id: Optional[int] = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(saved_contacts)")
        cols = [c["name"] for c in cursor.fetchall()]
        if "user_id" not in cols:
            cursor.execute("ALTER TABLE saved_contacts ADD COLUMN user_id INTEGER DEFAULT NULL")
            conn.commit()
            
        cursor.execute("""
        INSERT INTO saved_contacts (name, phone_number, notes, user_id)
        VALUES (?, ?, ?, ?)
        """, (name.strip(), phone_number.strip(), notes.strip(), user_id))
    except Exception:
        cursor.execute("""
        INSERT INTO saved_contacts (name, phone_number, notes)
        VALUES (?, ?, ?)
        """, (name.strip(), phone_number.strip(), notes.strip()))
        
    conn.commit()
    cid = cursor.lastrowid
    conn.close()
    return cid

def delete_contact(contact_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_contacts WHERE id = ?", (contact_id,))
    conn.commit()
    conn.close()

# --- Users & Authentication CRUD ---
# --- Password Security ---
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        310000
    ).hex()
    return f"pbkdf2_sha256${salt}${password_hash}"


def verify_password(password: str, stored_password: str) -> bool:
    # New secure password format
    if stored_password.startswith("pbkdf2_sha256$"):
        try:
            _, salt, saved_hash = stored_password.split("$")
            check_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                310000
            ).hex()
            return hmac.compare_digest(check_hash, saved_hash)
        except (ValueError, TypeError):
            return False

    # Legacy plain-text password support during migration
    return hmac.compare_digest(password, stored_password)


# --- Users & Authentication CRUD ---
def register_user(name: str, email: str, password: str, condition: str = "Dysarthria",
                  age: int = 30, phone: str = "", primary_goal: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        secure_password = hash_password(password)

        cursor.execute("""
        INSERT INTO users (name, email, password, condition, age, phone, primary_goal)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name.strip(),
            email.strip().lower(),
            secure_password,
            condition,
            age,
            phone,
            primary_goal
        ))

        conn.commit()
        uid = cursor.lastrowid

        cursor.execute("""
        SELECT id, name, email, condition, age, phone, primary_goal, created_at
        FROM users WHERE id = ?
        """, (uid,))

        user = dict(cursor.fetchone())
        return {"success": True, "user": user}

    except sqlite3.IntegrityError:
        return {
            "success": False,
            "error": "An account with this email address already exists. Please log in."
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT id, name, email, password, condition, age, phone,
               primary_goal, created_at
        FROM users
        WHERE email = ?
        """, (email.strip().lower(),))

        row = cursor.fetchone()

        if not row:
            return {
                "success": False,
                "error": "Invalid email or password. Please verify your credentials or register."
            }

        stored_password = row["password"]

        if not verify_password(password, stored_password):
            return {
                "success": False,
                "error": "Invalid email or password. Please verify your credentials or register."
            }

        # Upgrade an old plain-text password after successful login
        if not stored_password.startswith("pbkdf2_sha256$"):
            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hash_password(password), row["id"])
            )
            conn.commit()

        user = {
            key: row[key]
            for key in (
                "id", "name", "email", "condition", "age",
                "phone", "primary_goal", "created_at"
            )
        }

        return {"success": True, "user": user}

    except Exception as e:
        return {"success": False, "error": str(e)}

    finally:
        conn.close()

def get_all_users() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, email, condition, age, phone, primary_goal, created_at
    FROM users
    ORDER BY id ASC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

# --- Consultations CRUD ---
def book_consultation(user_id: Optional[int], user_name: str, therapist_name: str,
                      session_type: str, preferred_date: str, preferred_time: str,
                      notes: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO consultations (user_id, user_name, therapist_name, session_type, preferred_date, preferred_time, notes, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'Confirmed')
    """, (user_id, user_name, therapist_name, session_type, preferred_date, preferred_time, notes))
    conn.commit()
    cid = cursor.lastrowid
    cursor.execute("SELECT * FROM consultations WHERE id = ?", (cid,))
    cons = dict(cursor.fetchone())
    conn.close()
    return {"success": True, "consultation": cons}

def get_user_consultations(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM consultations WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    else:
        cursor.execute("SELECT * FROM consultations ORDER BY created_at DESC LIMIT 50")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def update_consultation_status(consultation_id: int, status: str, clinical_notes: str = "") -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    if clinical_notes:
        cursor.execute("""
        UPDATE consultations
        SET status = ?, clinical_notes = ?
        WHERE id = ?
        """, (status, clinical_notes.strip(), consultation_id))
    else:
        cursor.execute("""
        UPDATE consultations
        SET status = ?
        WHERE id = ?
        """, (status, consultation_id))
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

def prescribe_drill(patient_name: str, therapist_name: str, target_phrase: str,
                    difficulty: str = "Easy", instructions: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO prescribed_drills (patient_name, therapist_name, target_phrase, difficulty, instructions)
    VALUES (?, ?, ?, ?, ?)
    """, (patient_name.strip(), therapist_name.strip(), target_phrase.strip(), difficulty, instructions.strip()))
    conn.commit()
    did = cursor.lastrowid
    conn.close()
    return did

def get_prescribed_drills(patient_name: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if patient_name:
        cursor.execute("SELECT * FROM prescribed_drills WHERE patient_name LIKE ? ORDER BY created_at DESC", (f"%{patient_name}%",))
    else:
        cursor.execute("SELECT * FROM prescribed_drills ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_slp_dashboard_data(therapist_name: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Registered Patients (exclude SLP clinicians)
    cursor.execute("""
    SELECT id, name, email, condition, age, phone, primary_goal, created_at
    FROM users
    WHERE condition NOT LIKE '%Pathologist%' AND condition NOT LIKE '%SLP%'
    ORDER BY id DESC
    """)
    patients = [dict(row) for row in cursor.fetchall()]

    # 2. Consultations / Bookings
    if therapist_name:
        cursor.execute("""
        SELECT * FROM consultations
        WHERE therapist_name LIKE ?
        ORDER BY id DESC
        """, (f"%{therapist_name}%",))
    else:
        cursor.execute("SELECT * FROM consultations ORDER BY id DESC LIMIT 50")
    consultations = [dict(row) for row in cursor.fetchall()]

    # 3. Speech Checks Logged
    cursor.execute("SELECT * FROM speech_checks ORDER BY timestamp DESC LIMIT 50")
    speech_checks = [dict(row) for row in cursor.fetchall()]

    # 4. Vocal Practice Sessions Logged
    cursor.execute("SELECT * FROM practice_sessions ORDER BY timestamp DESC LIMIT 50")
    practice_sessions = [dict(row) for row in cursor.fetchall()]

    # 5. Prescribed Drills
    cursor.execute("SELECT * FROM prescribed_drills ORDER BY created_at DESC LIMIT 50")
    prescribed = [dict(row) for row in cursor.fetchall()]

    # 6. Aggregated Stats
    total_patients = len(patients)
    total_consultations = len(consultations)
    total_checks = len(speech_checks)
    avg_practice_score = 0.0
    if practice_sessions:
        scores = [p["match_score_pct"] for p in practice_sessions if p.get("match_score_pct") is not None]
        avg_practice_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    conn.close()
    return {
        "stats": {
            "total_patients": total_patients,
            "total_consultations": total_consultations,
            "total_checks": total_checks,
            "avg_practice_score": avg_practice_score
        },
        "patients": patients,
        "consultations": consultations,
        "speech_checks": speech_checks,
        "practice_sessions": practice_sessions,
        "prescribed_drills": prescribed
    }

# Initialize DB on module import
init_db()
