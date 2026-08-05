import os
import subprocess
import datetime
import json
from glm5_client import GLM5Client
from sunsum_ocr_logger import init_db, get_hash, log_event, generate_dealbook

# The directory to scan for Git commits. For MVP, we use the current GLM-5 project.
# You can add more paths here later (e.g. "~/Projects")
TARGET_REPOS = [
    os.path.expanduser("~/Downloads/GLM-5-main")
]

def scan_git_commits(repo_path: str):
    """Scan a git repository for commits in the last 24 hours."""
    print(f"[*] Scanning Git repository at: {repo_path}")
    if not os.path.exists(os.path.join(repo_path, ".git")):
        print(f"[!] Not a valid Git repository: {repo_path}")
        return []

    try:
        # Get commit hashes and messages from the last 24 hours
        result = subprocess.run(
            ["git", "log", "--since=24.hours", "--pretty=format:%H||%s||%b"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        if not result.stdout.strip():
            print(f"[*] No new commits found in {repo_path} in the last 24 hours.")
            return []
            
        commits = result.stdout.strip().split('\n')
        commit_data = []
        for commit in commits:
            parts = commit.split('||')
            if len(parts) >= 2:
                commit_hash = parts[0]
                message = parts[1]
                body = parts[2] if len(parts) > 2 else ""
                
                # Get the stat (files changed)
                stat_result = subprocess.run(
                    ["git", "show", "--stat", "--oneline", commit_hash],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                stat = stat_result.stdout.strip()
                
                commit_data.append({
                    "hash": commit_hash,
                    "message": message,
                    "body": body,
                    "stat": stat,
                    "repo": os.path.basename(repo_path)
                })
        return commit_data
    except Exception as e:
        print(f"[!] Error scanning Git: {e}")
        return []

def analyze_git_capability(commit_data: dict) -> dict:
    """Use GLM-5.1 to analyze the git commit and categorize the capability."""
    client = GLM5Client()
    
    prompt = f"""
You are the Sunsum (Ambient Spirit) capability engine.
I am providing you with a Git Commit from the user. 
A Git Commit represents 'Ahodin' (Verified Capability / Mastery), because it is a tangible outcome.

Commit Message: {commit_data['message']}
Commit Body: {commit_data['body']}
Files Changed: 
{commit_data['stat']}

Determine what capability the user just demonstrated.

Respond ONLY with a valid JSON object matching this schema:
{{
    "action": "A short 1-sentence description of what the user built/fixed.",
    "capability": "The specific technical capability demonstrated (e.g., 'Python API Integration', 'Database Schema Design', 'React Frontend Development')",
    "ontology_tag": "Ahodin"
}}
"""
    print(f"[*] Asking GLM-5.1 to analyze commit: {commit_data['hash'][:7]}...")
    try:
        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response["content"].strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        return json.loads(content.strip())
    except Exception as e:
        print(f"[!] AI Analysis failed: {e}")
        return {"capability": "Git Commit", "ontology_tag": "Ahodin", "action": commit_data['message']}

def sync_all_repos():
    db_conn = init_db()
    total_logged = 0
    
    for repo in TARGET_REPOS:
        commits = scan_git_commits(repo)
        for commit in commits:
            # Check if we already logged this exact commit
            cursor = db_conn.cursor()
            cursor.execute("SELECT id FROM kyinna_events WHERE hash = ?", (commit['hash'],))
            if cursor.fetchone():
                continue # Already logged
                
            analysis = analyze_git_capability(commit)
            
            # Format the detail
            action = analysis.get("action", commit['message'])
            capability = analysis.get("capability", "Software Development")
            detail = f"[Repo: {commit['repo']}] {action} (Capability Focus: {capability})"
            
            try:
                cursor.execute('''
                    INSERT INTO kyinna_events (event_type, detail, hash, ontology_tag)
                    VALUES (?, ?, ?, ?)
                ''', ('GIT_COMMIT', detail, commit['hash'], 'Ahodin'))
                db_conn.commit()
                print(f"[*] Successfully logged Git Ahodin: {capability}")
                total_logged += 1
            except sqlite3.IntegrityError:
                pass

    if total_logged > 0:
        generate_dealbook(db_conn)
        
    db_conn.close()
    return total_logged

if __name__ == "__main__":
    print("=== Sunsum Git Tracker ===")
    count = sync_all_repos()
    print(f"=== Complete. Synced {count} new verified capabilities. ===")
