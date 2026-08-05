import os
import sqlite3
import datetime
import subprocess
import hashlib
import json
import re
import uuid
import re
try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("Please install requirements: pip install Pillow pytesseract")
    exit(1)

from glm5_client import GLM5Client

# ---------------------------------------------------------
# Sunsum OCR Tracker (Node 0) - "The Omniscient Self"
# ---------------------------------------------------------
# This script takes a silent screenshot, runs OCR to extract text,
# and uses GLM-5.1 to categorize your performance into the Akan Ontology.
# ---------------------------------------------------------

# iCloud Drive path with local fallback
ICLOUD_SUNSUM = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/Sunsum")
LOCAL_SUNSUM = os.path.expanduser("~/.sunsum")

if os.path.isdir(os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs")):
    SUNSUM_DIR = ICLOUD_SUNSUM
    print("[*] Using iCloud Drive for Sunsum data.")
else:
    SUNSUM_DIR = LOCAL_SUNSUM
    print("[*] iCloud Drive not found. Using local ~/.sunsum directory.")

os.makedirs(SUNSUM_DIR, exist_ok=True)

DB_PATH = os.path.join(SUNSUM_DIR, "sunsum_core.db")
REPORT_PATH = os.path.join(SUNSUM_DIR, "capability_timeseries.md")
INTENT_PATH = os.path.join(SUNSUM_DIR, "active_intent.txt")
SCREENSHOT_PATH = "/tmp/sunsum_screen.png"

import urllib.request
import urllib.error
import base64
from datetime import datetime, timezone

def init_db():
    # Stubbed out: TerminusDB runs via Docker, no local SQLite file needed.
    # We return None so we don't break existing function signatures in app.py
    return None

def get_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def fails_opsec_check(text: str) -> bool:
    """Returns True if the text contains sensitive OPSEC violations."""
    # 1. Sensitive App Names or Contexts
    sensitive_keywords = [
        "System Settings", "1Password", "Keychain Access", "Bitwarden",
        "AWS Console", "Enter password", "Private Key", "Secret Access Key",
        "Master Password", "recovery phrase", "seed phrase"
    ]
    for kw in sensitive_keywords:
        if kw.lower() in text.lower():
            print(f"[!] OPSEC Violation: Detected keyword '{kw}'")
            return True
            
    # 2. Sensitive Patterns (API Keys, etc)
    sensitive_patterns = [
        r"sk-[a-zA-Z0-9]{32,}", # Typical secret keys (OpenAI, Stripe, etc)
        r"AKIA[0-9A-Z]{16}",    # AWS Access Key ID
        r"(?i)(password|passcode|secret)[\s:=]+[^\s]{8,}" # Basic heuristics for visible passwords
    ]
    for pattern in sensitive_patterns:
        if re.search(pattern, text):
            print(f"[!] OPSEC Violation: Detected sensitive regex pattern.")
            return True
            
    return False

def capture_and_ocr() -> str:
    print("[*] Taking silent screenshot...")
    # Take screenshot of primary display silently (-x)
    subprocess.run(["screencapture", "-x", SCREENSHOT_PATH])
    
    if not os.path.exists(SCREENSHOT_PATH):
        print("[!] Failed to capture screen.")
        return ""
        
    print("[*] Running OCR on screen capture...")
    try:
        text = pytesseract.image_to_string(Image.open(SCREENSHOT_PATH))
    except Exception as e:
        print(f"[!] OCR Error: {e}")
        text = ""
        
    # Clean up screenshot
    if os.path.exists(SCREENSHOT_PATH):
        os.remove(SCREENSHOT_PATH)
        
    # Clean up empty lines to save context
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned_text = " ".join(lines)
    
    # Run OPSEC filter before doing anything else
    if fails_opsec_check(cleaned_text):
        return "__OPSEC_VIOLATION__"
    
    # Cap at 6000 characters to prevent prompt bloat from massive screens
    return cleaned_text[:6000]

# ---------------------------------------------------------
# Persistent Intent Memory (Letta Concept)
# ---------------------------------------------------------

def load_active_intent() -> str:
    """Load the last-known stated intent from persistent storage."""
    if os.path.exists(INTENT_PATH):
        with open(INTENT_PATH, 'r') as f:
            intent = f.read().strip()
            if intent:
                return intent
    return ""

def save_active_intent(intents: list):
    """Save newly discovered intents to persistent storage."""
    if intents:
        combined = "\n".join([i for i in intents if i and i != "Extract any to-do list items or goals visible on the screen. Leave empty if none found."])
        if combined.strip():
            with open(INTENT_PATH, 'w') as f:
                f.write(combined)
            print(f"[*] Persistent intent saved: {combined[:80]}...")

def load_recent_transitions(n=5) -> str:
    """Load the last N transitions from TerminusDB (stubbed for MVP)."""
    return ""

def analyze_capability(text: str) -> dict:
    if len(text) < 50:
        return {"capability_built": "None", "ontology_tag": "Ignore", "action_type": "NOISE", "current_action": "Idle", "stated_intents": []}

    client = GLM5Client()
    
    # Load persistent memory
    remembered_intent = load_active_intent()
    recent_context = load_recent_transitions(5)
    
    memory_block = ""
    if remembered_intent:
        memory_block += f"\n[PERSISTENT MEMORY - Last Known Stated Intents]:\n{remembered_intent}\n"
    if recent_context:
        memory_block += f"\n[PERSISTENT MEMORY - Last 5 Capability Transitions]:\n{recent_context}\n"
    
    prompt = f"""
You are the Sunsum (Ambient Spirit) capability engine.
I am providing you with the raw, messy OCR text extracted from my current computer screen.
Your job is to capture the current DATA TRANSITION. You must look for my Stated Intent (from any visible To-Do lists or notes) and compare it against my unstructured action.
{memory_block}
IMPORTANT: If no To-Do list is visible on the screen but you have PERSISTENT MEMORY of prior stated intents, use those remembered intents to judge whether the current action is PLANNED or UNSTRUCTURED.

Use the Akan ontology to classify the transition state:
1. 'Kyinna' (Action/Ripples): Executing routine tasks, reading, browsing.
2. 'Nnyini' (Growth): Actively learning, struggling through code. Capability is forming.
3. 'Ahodin' (Verified Capability): Producing a verified outcome.
4. 'Ignore': Irrelevant noise.

Screen Text (Raw OCR):
'''
{text}
'''

Respond ONLY with a valid JSON object matching this schema:
{{
    "stated_intents": ["Extract any to-do list items or goals visible on the screen. Leave empty if none found."],
    "current_action": "A 1-sentence description of what the user is actually doing right now.",
    "action_type": "Must be exactly one of: 'PLANNED' (matches an intent), 'UNSTRUCTURED' (building capability but not on the list), or 'NOISE'",
    "capability_built": "The specific technical capability forming or being exercised",
    "ontology_tag": "Kyinna, Nnyini, Ahodin, or Ignore"
}}
"""
    
    print("[*] Asking GLM-5.1 to analyze screen context...")
    try:
        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2 # low temp for deterministic JSON
        )
        
        content = response["content"].strip()
        # Clean markdown code blocks if GLM-5 returns them
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        return json.loads(content.strip())
    except Exception as e:
        print(f"[!] AI Analysis failed: {e}")
        return {"capability": "Error", "ontology_tag": "Ignore", "action": str(e)}

def log_event(conn, result: dict):
    tag = result.get("ontology_tag", "Ignore")
    if tag == "Ignore" or result.get("action_type") == "NOISE":
        print("[*] Transition classified as noise. Not logging.")
        return

    intents = result.get("stated_intents", [])
    save_active_intent(intents)

    action = result.get("current_action", "")
    capability = result.get("capability_built", "")
    action_type = result.get("action_type", "UNSTRUCTURED")
    energy_cost = 1320.0
    now = datetime.now(timezone.utc).isoformat()
    
    # TerminusDB HTTP config
    base_url = "http://localhost:6363"
    db_id = "darwin"
    auth = base64.b64encode(b"admin:root").decode("ascii")
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    
    documents = []
    
    # 1. Action State Node
    state_id = f"PhaseState/{uuid.uuid4().hex}"
    action_state = {
        "@type": "PhaseState",
        "@id": state_id,
        "timestamp": now,
        "accumulated_energy": energy_cost,
        "current_action": action
    }
    
    # 2. Intent Anchor (if PLANNED)
    if intents and action_type == "PLANNED":
        intent_hash = get_hash(intents[0])
        anchor_id = f"CapabilityAnchor/{intent_hash}"
        anchor = {
            "@type": "CapabilityAnchor",
            "@id": anchor_id,
            "intent_hash": intent_hash,
            "content": intents[0],
            "phase": "Okra"
        }
        action_state["anchor"] = anchor_id
        
        # Propagation Edge (Okra -> Action)
        edge = {
            "@type": "PropagationEdge",
            "@id": f"PropagationEdge/{uuid.uuid4().hex}",
            "source": anchor_id,
            "target": anchor_id, # Simplified for MVP, targeting the same anchor's state chain
            "energy_transferred": energy_cost,
            "timestamp": now
        }
        documents.extend([anchor, edge])
        
    documents.append(action_state)
    
    # Push to TerminusDB
    try:
        url = f"{base_url}/api/document/admin/{db_id}?author=darwin_agent&message=Logged%20{tag}%20Phase"
        req = urllib.request.Request(url, method="POST", headers=headers, data=json.dumps(documents).encode("utf-8"))
        urllib.request.urlopen(req)
        print(f"[*] 4D Phase Change Synced to TerminusDB: {capability} [{tag}]")
    except Exception as e:
        print(f"[!] TerminusDB sync failed: {e}")

def generate_dealbook(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT type, content, created_at 
        FROM nodes 
        WHERE date(created_at) = date('now') AND type != 'Okra'
        ORDER BY created_at DESC
    ''')
    events = cursor.fetchall()
    
    with open(REPORT_PATH, 'w') as f:
        f.write("# ⏳ Sunsum Capability Time Series\n\n")
        f.write(f"*Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("## The Flow of Reality (Recursive Graph View)\n")
        f.write("> *Mapping transitions from Intent (Okra) to Action (Kyinna) to Mastery (Ahodin).* \n\n")
        
        if not events:
            f.write("*No capability nodes sprouted today yet.*\n")
        else:
            for event in events:
                node_type, content, timestamp = event
                time_str = timestamp.split(' ')[1]
                f.write(f"- **[{time_str}] [{node_type}]** {content}\n")
                
    print(f"[*] Updated Time Series Log at: {REPORT_PATH}")

def generate_meta_review(session_start_time):
    """Generates a 333-minute raw data export for manual meta-review."""
    db_conn = init_db()
    cursor = db_conn.cursor()
    cursor.execute('''
        SELECT created_at, content, type 
        FROM nodes 
        WHERE created_at >= ? AND type != 'Okra'
        ORDER BY created_at ASC
    ''', (session_start_time,))
    events = cursor.fetchall()
    db_conn.close()

    if not events:
        print("[!] No events found for meta-review.")
        return None

    review_path = os.path.join(SUNSUM_DIR, "meta_review_333.md")
    with open(review_path, "w") as f:
        f.write(f"# 🧿 Raw Data Export: 333-Minute Meta-Review\n\n")
        f.write(f"*Session Start: {session_start_time}*\n")
        f.write("> *Manual Review Mode: Compare this raw data against your calendar and To-Do list to assess Sovereign Capability.* \n\n")
        
        for e in events:
            time_str = e[0].split(' ')[1] if ' ' in e[0] else e[0]
            f.write(f"- **[{time_str}] [{e[2]}]** {e[1]}\n")
            
    print(f"[*] Raw Meta-Review generated at: {review_path}")
    return review_path

if __name__ == "__main__":
    print("=== Sunsum OCR Tracker ===")
    screen_text = capture_and_ocr()
    if screen_text:
        analysis = analyze_capability(screen_text)
        print(f"AI Result: {analysis}")
        
        db_conn = init_db()
        log_event(db_conn, analysis)
        generate_dealbook(db_conn)
        db_conn.close()
    else:
        print("[!] No text extracted from screen.")
    print("=== Complete ===")
