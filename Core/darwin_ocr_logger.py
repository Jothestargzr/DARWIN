#!/usr/bin/env python3
"""
=============================================================================
DARWIN OCR Logger: Screen Capture → Akan Ontology Classification → TerminusDB
=============================================================================
Captures screen content, extracts text via OCR, classifies into Akan ontology
(Kyinna/Nnyini/Ahodin/Okra/Sunsum), and syncs to TerminusDB 4D graph.

OPSEC Features:
  - Filters AWS keys, 1Password, SSH keys, API tokens
  - Redacts PII (emails, phone numbers, credit cards)
  - Never logs sensitive credential patterns
=============================================================================
"""

import os
import sys
import json
import sqlite3
import hashlib
import uuid
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import subprocess
import base64
import urllib.request
import urllib.error

# Try to import PIL for screen capture
try:
    from PIL import ImageGrab, Image
except ImportError:
    ImageGrab = None
    Image = None

# Try pytesseract for OCR
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

# GLM-5 client for Akan classification
try:
    from glm5_client import GLM5Client
except ImportError:
    GLM5Client = None

DARWIN_DIR = os.path.expanduser("~/.darwin")
DB_PATH = os.path.join(DARWIN_DIR, "capability_log.db")

# OPSEC Filters: patterns to redact
OPSEC_PATTERNS = {
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "aws_secret": r"aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}",
    "ssh_key": r"-----BEGIN.*PRIVATE KEY-----",
    "api_token": r"(api_key|api_token|authorization|bearer)\s*[=:]\s*[A-Za-z0-9_\-\.]{20,}",
    "password": r"(password|passwd)\s*[=:]\s*[A-Za-z0-9_\-\.!@#$%^&*]{6,}",
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "credit_card": r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
    "phone": r"\b\d{3}[\s\-]?\d{3}[\s\-]?\d{4}\b",
    "1password": r"1Password|opvault|agentkeychain",
}

def ensure_darwin_dir():
    """Ensure ~/.darwin directory exists."""
    os.makedirs(DARWIN_DIR, exist_ok=True)

def init_db() -> sqlite3.Connection:
    """Initialize SQLite database for capability logging."""
    ensure_darwin_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS capability_events (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        screen_text TEXT NOT NULL,
        action_type TEXT NOT NULL,
        capability_built TEXT,
        ontology_tag TEXT NOT NULL,
        energy_cost REAL DEFAULT 1320.0,
        terminus_synced BOOLEAN DEFAULT 0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transition_history (
        id TEXT PRIMARY KEY,
        from_state TEXT,
        to_state TEXT,
        transition_type TEXT,
        timestamp TEXT NOT NULL,
        energy_delta REAL
    )
    """)
    
    conn.commit()
    return conn

def check_opsec_violation(text: str) -> bool:
    """
    Check if text contains sensitive patterns.
    Returns True if violation detected, False otherwise.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    for pattern_name, pattern in OPSEC_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            print(f"[!] OPSEC VIOLATION DETECTED: {pattern_name}")
            return True
    
    return False

def redact_sensitive_data(text: str) -> str:
    """
    Redact sensitive patterns from text.
    Returns sanitized text safe for logging.
    """
    sanitized = text
    for pattern_name, pattern in OPSEC_PATTERNS.items():
        sanitized = re.sub(pattern, f"[REDACTED_{pattern_name.upper()}]", sanitized, flags=re.IGNORECASE)
    return sanitized

def capture_and_ocr() -> Optional[str]:
    """
    Capture screen and extract text via OCR.
    Returns extracted text or None on failure.
    """
    if not ImageGrab:
        print("[!] PIL not available. Install: pip install pillow")
        return None
    
    try:
        # macOS: use screencapture to /tmp
        screenshot_path = "/tmp/darwin_screenshot.png"
        result = subprocess.run(
            ["screencapture", "-x", screenshot_path],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print(f"[!] screencapture failed: {result.stderr.decode()}")
            return None
        
        if not os.path.exists(screenshot_path):
            print("[!] Screenshot file not created")
            return None
        
        # OCR via pytesseract or fallback to cloud
        if PYTESSERACT_AVAILABLE:
            image = Image.open(screenshot_path)
            text = pytesseract.image_to_string(image)
            os.remove(screenshot_path)
            return text if text.strip() else None
        else:
            print("[*] pytesseract not available, returning raw capture path")
            return f"Screenshot captured at: {screenshot_path}"
    
    except Exception as e:
        print(f"[!] OCR capture failed: {e}")
        return None

def classify_capability(screen_text: str) -> Dict[str, Any]:
    """
    Use GLM-5.2 to classify screen activity into Akan ontology.
    
    Returns:
    {
        "action_type": "Kyinna" | "Nnyini" | "Ahodin" | "Okra" | "Sunsum",
        "capability_built": str (e.g. "HTTP routing layer"),
        "confidence": float (0.0-1.0),
        "summary": str
    }
    """
    
    prompt = f"""
Analyze this screen activity and classify into the Akan Metaphysical Ontology:

**AKAN ONTOLOGY DEFINITIONS:**
- **Kyinna (Physical Action)**: Terminal commands, file operations, CDP browser events, keystrokes, API calls
- **Nnyini (Growth & Cognitive Friction)**: Learning activities, debugging, reading docs, skill acquisition
- **Ahodin (Verified Mastery)**: Completed builds, merged PRs, deployed services, tested features
- **Okra (Intent Anchor)**: Planning, goal-setting, issue creation, architecture design
- **Sunsum (Executive Spirit)**: Active transitions, state changes, structural entropy measurement

**SCREEN ACTIVITY:**
{screen_text[:2000]}

**RESPOND IN JSON:**
{{
  "action_type": "Kyinna|Nnyini|Ahodin|Okra|Sunsum",
  "capability_built": "brief description (max 50 chars)",
  "confidence": 0.0-1.0,
  "summary": "one sentence analysis"
}}
"""
    
    try:
        if GLM5Client:
            client = GLM5Client()
            response = client.classify(prompt)
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        
        # Fallback: heuristic classification
        return classify_heuristic(screen_text)
    
    except Exception as e:
        print(f"[!] Classification failed: {e}")
        return classify_heuristic(screen_text)

def classify_heuristic(text: str) -> Dict[str, Any]:
    """Fallback heuristic classification without GLM-5."""
    text_lower = text.lower()
    
    # Simple heuristic rules
    if any(x in text_lower for x in ["error", "failed", "exception", "traceback"]):
        action = "Nnyini"  # Debugging/learning
    elif any(x in text_lower for x in ["merged", "deployed", "released", "shipped"]):
        action = "Ahodin"  # Verified mastery
    elif any(x in text_lower for x in ["$ ", ">>> ", "# ", "commit", "push"]):
        action = "Kyinna"  # Physical action
    elif any(x in text_lower for x in ["todo", "plan", "goal", "issue", "design"]):
        action = "Okra"  # Intent
    else:
        action = "Sunsum"  # Executive spirit (default)
    
    return {
        "action_type": action,
        "capability_built": "Heuristic classification",
        "confidence": 0.5,
        "summary": f"Classified as {action} based on keywords"
    }

def log_event(conn: sqlite3.Connection, analysis: Dict[str, Any]) -> str:
    """
    Log a capability event to SQLite.
    Returns event ID.
    """
    cursor = conn.cursor()
    event_id = f"CapabilityEvent/{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
    INSERT INTO capability_events 
    (id, timestamp, screen_text, action_type, capability_built, ontology_tag)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        now,
        analysis.get("summary", ""),
        analysis.get("action_type", "Sunsum"),
        analysis.get("capability_built", "Unknown"),
        analysis.get("action_type", "Sunsum")
    ))
    
    conn.commit()
    print(f"[+] Logged event: {event_id}")
    return event_id

def sync_to_terminus(event_id: str, analysis: Dict[str, Any]) -> bool:
    """
    Sync capability event to TerminusDB 4D graph.
    Returns True on success.
    """
    try:
        base_url = "http://localhost:6363"
        db_id = "darwin"
        auth = base64.b64encode(b"admin:root").decode("ascii")
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json"
        }
        
        now = datetime.now(timezone.utc).isoformat()
        state_id = f"PhaseState/{uuid.uuid4().hex}"
        
        action_state = {
            "@type": "PhaseState",
            "@id": state_id,
            "timestamp": now,
            "accumulated_energy": 1320.0,
            "current_action": analysis.get("capability_built", "Unknown"),
            "ontology_tag": analysis.get("action_type", "Sunsum"),
            "capability_id": event_id
        }
        
        documents = [action_state]
        url = f"{base_url}/api/document/admin/{db_id}?author=darwin_ocr&message=Capability%20{analysis.get('action_type')}"
        
        req = urllib.request.Request(
            url,
            method="POST",
            headers=headers,
            data=json.dumps(documents).encode("utf-8")
        )
        
        response = urllib.request.urlopen(req)
        if response.status == 200:
            print(f"[+] Synced to TerminusDB: {state_id}")
            return True
        
    except Exception as e:
        print(f"[!] TerminusDB sync failed: {e}")
    
    return False

def generate_dealbook(conn: sqlite3.Connection, output_path: Optional[str] = None) -> str:
    """
    Generate capability dealbook (markdown report).
    Returns file path.
    """
    if not output_path:
        output_path = os.path.join(DARWIN_DIR, "capability_dealbook.md")
    
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, timestamp, action_type, capability_built 
    FROM capability_events 
    ORDER BY timestamp DESC 
    LIMIT 100
    """)
    
    rows = cursor.fetchall()
    
    # Build markdown report
    report = "# 🌿 DARWIN Capability Dealbook\n\n"
    report += f"**Generated**: {datetime.now().isoformat()}\n\n"
    report += "## Session Capabilities\n\n"
    
    # Group by action type
    by_type = {}
    for event_id, timestamp, action_type, capability in rows:
        if action_type not in by_type:
            by_type[action_type] = []
        by_type[action_type].append((event_id, timestamp, capability))
    
    ontology_desc = {
        "Kyinna": "🔨 **Physical Actions** - Terminal commands, API calls, file operations",
        "Nnyini": "📚 **Growth & Learning** - Debugging, reading docs, skill acquisition",
        "Ahodin": "✅ **Verified Mastery** - Completed builds, merged PRs, deployed services",
        "Okra": "🎯 **Intent Anchors** - Planning, goal-setting, architecture design",
        "Sunsum": "⚡ **Executive Spirit** - State transitions, active measures"
    }
    
    for action_type in ["Kyinna", "Nnyini", "Ahodin", "Okra", "Sunsum"]:
        if action_type in by_type:
            report += f"\n### {ontology_desc.get(action_type, action_type)}\n\n"
            for event_id, timestamp, capability in by_type[action_type]:
                report += f"- **{timestamp}**: {capability}\n"
    
    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"[+] Dealbook generated: {output_path}")
    return output_path

def generate_meta_review(start_time_iso: str, duration_minutes: int = 333) -> Optional[str]:
    """
    Generate 333-minute meta-review (GLM-5 synthesis).
    Returns markdown file path.
    """
    conn = init_db()
    cursor = conn.cursor()
    
    # Query events from the time window
    cursor.execute("""
    SELECT capability_built, action_type, COUNT(*) as count
    FROM capability_events
    WHERE timestamp >= ?
    GROUP BY action_type
    ORDER BY count DESC
    """, (start_time_iso,))
    
    stats = cursor.fetchall()
    
    review = f"# 🧿 333-Minute Meta-Review\n\n"
    review += f"**Period**: {start_time_iso} (333 minutes)\n\n"
    review += "## Capability Summary\n\n"
    
    for capability, action_type, count in stats:
        review += f"- **{action_type}**: {count} events - {capability}\n"
    
    review += "\n## Key Transitions\n\n"
    review += "- Moved through multiple capability states\n"
    review += "- Active learning and implementation phases\n"
    review += "- Verified outputs: some builds/deployments completed\n"
    
    # Write to file
    review_path = os.path.join(DARWIN_DIR, f"meta_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    with open(review_path, 'w') as f:
        f.write(review)
    
    conn.close()
    print(f"[+] Meta-review generated: {review_path}")
    return review_path

# ============================================================================
# PUBLIC API
# ============================================================================

def main():
    """Example usage."""
    ensure_darwin_dir()
    print("🌿 DARWIN OCR Logger initialized")
    
    # Test: capture and classify
    screen_text = capture_and_ocr()
    if screen_text:
        # Check OPSEC
        if check_opsec_violation(screen_text):
            print("[!] OPSEC violation - capture aborted")
            return "__OPSEC_VIOLATION__"
        
        # Redact and analyze
        safe_text = redact_sensitive_data(screen_text)
        analysis = classify_capability(safe_text)
        
        # Log to database
        conn = init_db()
        log_event(conn, analysis)
        
        # Sync to TerminusDB
        sync_to_terminus(str(uuid.uuid4()), analysis)
        
        # Generate dealbook
        generate_dealbook(conn)
        
        conn.close()
        print(f"[+] Capability logged: {analysis}")
    else:
        print("[!] No screen text captured")

if __name__ == "__main__":
    main()
