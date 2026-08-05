import os
import sqlite3
import datetime
import subprocess
import hashlib
from typing import List, Dict

# ---------------------------------------------------------
# Sunsum Capability Logger - 18 Hour MVP
# "The Keeper of the Current"
# ---------------------------------------------------------
# This script is designed for extreme storage efficiency.
# It tracks your 'capability growth' (Kyinna) and verified 
# outcomes (Ahodin) via system telemetry, rather than heavy video OCR.
# ---------------------------------------------------------

DB_PATH = os.path.expanduser("~/.sunsum/sunsum_core.db")
ZSH_HISTORY_PATH = os.path.expanduser("~/.zsh_history")
REPORT_PATH = os.path.expanduser("~/capability_log.md")

# Target processes that indicate capability building / flow
CAPABILITY_APPS = ["Code", "Xcode", "Terminal", "iTerm2", "Cursor", "Python"]

def init_db():
    """Initialize the SQLite database with the Akan Ontology schema."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kyinna_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT,
            detail TEXT,
            hash TEXT UNIQUE,
            ontology_tag TEXT
        )
    ''')
    conn.commit()
    return conn

def get_hash(text: str) -> str:
    """Generate a hash to prevent logging duplicate events."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def log_zsh_history(conn):
    """
    Extract recent terminal commands. 
    This represents 'Kyinna' (action/ripples) and 'Nnyini' (growth).
    """
    if not os.path.exists(ZSH_HISTORY_PATH):
        return
        
    try:
        # Read the last 50 lines of zsh history (ignoring decode errors for binary junk)
        with open(ZSH_HISTORY_PATH, 'rb') as f:
            lines = f.readlines()[-50:]
            
        cursor = conn.cursor()
        added_count = 0
        
        for line_bytes in lines:
            try:
                line = line_bytes.decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                    
                # ZSH history format: : 1629837498:0;command
                if ';' in line:
                    command = line.split(';', 1)[1].strip()
                else:
                    command = line
                    
                if len(command) < 3: # Ignore tiny commands like 'ls' or 'cd'
                    continue
                    
                cmd_hash = get_hash(command)
                
                try:
                    cursor.execute('''
                        INSERT INTO kyinna_events (event_type, detail, hash, ontology_tag)
                        VALUES (?, ?, ?, ?)
                    ''', ('TERMINAL_COMMAND', command, cmd_hash, 'Kyinna'))
                    added_count += 1
                except sqlite3.IntegrityError:
                    pass # Duplicate command hash, ignore
                    
            except Exception:
                continue
                
        conn.commit()
        if added_count > 0:
            print(f"[*] Logged {added_count} new terminal commands (Kyinna).")
            
    except Exception as e:
        print(f"[!] Error reading zsh history: {e}")

def log_active_processes(conn):
    """
    Check if capability-building apps are running.
    This tracks the state of 'Flow' / Focus.
    """
    try:
        result = subprocess.run(['ps', '-axc', '-o', 'command'], capture_output=True, text=True)
        running_apps = result.stdout.split('\n')
        
        active_capability_apps = []
        for app in running_apps:
            for cap_app in CAPABILITY_APPS:
                if cap_app.lower() in app.lower():
                    active_capability_apps.append(cap_app)
                    
        active_capability_apps = list(set(active_capability_apps)) # Deduplicate
        
        if not active_capability_apps:
            return
            
        apps_str = ", ".join(active_capability_apps)
        
        # Only log once per hour to save space
        current_time = datetime.datetime.now()
        time_hash = f"{current_time.year}-{current_time.month}-{current_time.day}-{current_time.hour}"
        event_hash = get_hash(f"APPS_{apps_str}_{time_hash}")
        
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO kyinna_events (event_type, detail, hash, ontology_tag)
                VALUES (?, ?, ?, ?)
            ''', ('ACTIVE_FOCUS', f"Working in: {apps_str}", event_hash, 'Kyinna'))
            conn.commit()
            print(f"[*] Logged active focus apps: {apps_str}")
        except sqlite3.IntegrityError:
            pass # Already logged this hour
            
    except Exception as e:
        print(f"[!] Error checking processes: {e}")

def generate_dealbook_markdown(conn):
    """
    Translates the SQLite telemetry into the readable Capability Dealbook format.
    """
    cursor = conn.cursor()
    
    # Get today's events
    cursor.execute('''
        SELECT event_type, detail, ontology_tag, timestamp 
        FROM kyinna_events 
        WHERE date(timestamp) = date('now')
        ORDER BY timestamp DESC
    ''')
    
    events = cursor.fetchall()
    
    with open(REPORT_PATH, 'w') as f:
        f.write("# 🌿 Sunsum Capability Log (Dealbook)\n\n")
        f.write(f"*Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        f.write("## The Keeper of the Flow\n")
        f.write("> *Wild Flow → [The Figure] → Ordered Flow*\n\n")
        
        f.write("### 🌊 Kyinna (Daily Actions & Ripples)\n")
        if not events:
            f.write("*No capability signals detected today yet.*\n")
        else:
            for event in events:
                e_type, detail, tag, timestamp = event
                time_str = timestamp.split(' ')[1] # just the HH:MM:SS
                f.write(f"- **[{time_str}]** `{e_type}`: {detail}\n")
                
    print(f"[*] Generated readable capability log at: {REPORT_PATH}")

if __name__ == "__main__":
    print("=== Sunsum Capability Logger (MVP) ===")
    db_conn = init_db()
    
    log_zsh_history(db_conn)
    log_active_processes(db_conn)
    
    generate_dealbook_markdown(db_conn)
    db_conn.close()
    print("=== Complete ===")
