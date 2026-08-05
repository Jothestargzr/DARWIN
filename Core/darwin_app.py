import rumps
import threading
import subprocess
import os
import json

# Import the logic we built in the OCR logger
from sunsum_ocr_logger import capture_and_ocr, analyze_capability, init_db, log_event, generate_dealbook, generate_meta_review, SUNSUM_DIR
from sunsum_git_logger import sync_all_repos
import datetime

class SunsumApp(rumps.App):
    def __init__(self):
        super(SunsumApp, self).__init__("Sunsum")
        self.menu = [
            "Capture Now",
            "Sync Git Outcomes (Ahodin)",
            "Generate 333m Meta-Review Now",
            "Toggle Ambient Mode (Off)",
            "Open Dashboard",
            "Launch Browser",
            None # Separator
        ]
        self.ambient_timer = rumps.Timer(self.auto_capture, 1320) # 22 minutes in seconds
        self.review_timer = rumps.Timer(self.prompt_review, 6660) # 111 minutes
        self.meta_review_timer = rumps.Timer(self.prompt_meta_review, 19980) # 333 minutes
        self.is_ambient_on = False
        self.session_start_time = None
        self.last_cybersec_baseline = None

    def _run_capture_pipeline(self):
        """Runs the OCR capture and logging in a background thread to prevent UI freezing."""
        print("=== Manual Capture Triggered ===")
        screen_text = capture_and_ocr()
        
        if screen_text == "__OPSEC_VIOLATION__":
            print("[!] Capture aborted due to OPSEC violation.")
            rumps.notification(
                title="Sunsum Logger (OPSEC)",
                subtitle="Capture Blocked",
                message="Sensitive keywords or patterns detected. OCR payload destroyed."
            )
            return

        if screen_text:
            analysis = analyze_capability(screen_text)
            print(f"AI Result: {analysis}")
            
            db_conn = init_db()
            log_event(db_conn, analysis)
            generate_dealbook(db_conn)
            db_conn.close()
            rumps.notification(
                title="Sunsum Logger",
                subtitle="Transition Logged",
                message=f"[{analysis.get('action_type', 'UNSTRUCTURED')}] -> {analysis.get('capability_built', 'None')}"
            )
        else:
            print("[!] No text extracted from screen.")
            rumps.notification(
                title="Sunsum Logger",
                subtitle="Capture Failed",
                message="No text found on screen."
            )

    @rumps.clicked("Capture Now")
    def capture_now(self, _):
        # Run in thread so the menu bar doesn't lock up during OCR/API call
        threading.Thread(target=self._run_capture_pipeline).start()

    def _run_git_sync(self):
        print("=== Git Sync Triggered ===")
        count = sync_all_repos()
        rumps.notification(
            title="Sunsum Logger",
            subtitle="Git Sync Complete",
            message=f"Synced {count} new verified outcomes (Ahodin)."
        )

    @rumps.clicked("Sync Git Outcomes (Ahodin)")
    def sync_git(self, _):
        threading.Thread(target=self._run_git_sync).start()

    def auto_capture(self, _):
        print("=== Ambient Auto Capture Triggered ===")
        threading.Thread(target=self._run_capture_pipeline).start()
        
    def prompt_review(self, _):
        print("=== 111-Minute Review Triggered ===")
        rumps.notification(
            title="Sunsum Logger (Review Time)",
            subtitle="Take a Review.",
            message="Time to look at your capability time series.",
            sound="Glass"
        )
        
    def prompt_meta_review(self, _):
        print("=== 333-Minute META Review Triggered ===")
        rumps.notification("Sunsum Logger", "Generating Meta-Review...", "Quma is synthesizing your session.")
        
        # Run in thread so UI doesn't freeze while GLM-5 generates review
        def run_meta():
            start_str = self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')
            review_path = generate_meta_review(start_str)
            if review_path and os.path.exists(review_path):
                subprocess.run(["open", review_path])
                rumps.notification("Sunsum Meta-Review", "Complete", "Your 333-minute synthesis is ready.", sound="Glass")
            
            # --- Silent CyberSec Delta Scan ---
            self._run_cybersec_delta()
        threading.Thread(target=run_meta).start()
    
    def _run_cybersec_delta(self):
        """Runs a silent cybersec scan and alerts only on changes from baseline."""
        try:
            from cybersec_scan import run_scan
            print("=== 333m CyberSec Delta Scan ===")
            current_scan = run_scan()
            baseline_path = os.path.join(SUNSUM_DIR, "cybersec_baseline.json")
            
            if os.path.exists(baseline_path):
                with open(baseline_path, 'r') as f:
                    previous_scan = json.load(f)
                
                # Compare key security indicators
                changes = []
                for key in current_scan:
                    if current_scan[key] != previous_scan.get(key):
                        changes.append(key)
                
                if changes:
                    rumps.notification(
                        "Sunsum CyberSec", "⚠️ Changes Detected",
                        f"Delta in: {', '.join(changes[:3])}", sound="Basso"
                    )
                    print(f"[!] CyberSec delta detected in: {changes}")
                else:
                    print("[*] CyberSec scan: No changes from baseline.")
            
            # Save current scan as the new baseline
            with open(baseline_path, 'w') as f:
                json.dump(current_scan, f, indent=2)
            print("[*] CyberSec baseline updated.")
        except Exception as e:
            print(f"[!] CyberSec delta scan failed: {e}")

    @rumps.clicked("Generate 333m Meta-Review Now")
    def trigger_meta_review_now(self, _):
        if not self.session_start_time:
            # If ambient mode wasn't started, just use 333 minutes ago
            start_time = datetime.datetime.now() - datetime.timedelta(minutes=333)
        else:
            start_time = self.session_start_time
            
        def run_meta():
            start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            review_path = generate_meta_review(start_str)
            if review_path and os.path.exists(review_path):
                subprocess.run(["open", review_path])
            else:
                rumps.notification("Sunsum Logger", "No Data", "No transitions found in the last 333 minutes.")
        threading.Thread(target=run_meta).start()

    @rumps.clicked("Toggle Ambient Mode (Off)")
    def toggle_ambient(self, sender):
        self.is_ambient_on = not self.is_ambient_on
        if self.is_ambient_on:
            self.title = "[REC] Sunsum"
            self.session_start_time = datetime.datetime.now()
            sender.title = "Toggle Ambient Mode (On)"
            self.ambient_timer.start()
            self.review_timer.start()
            self.meta_review_timer.start()
            rumps.notification("Sunsum Logger", "Ambient Mode ON", "Capture: 22m | Review: 111m | Meta: 333m")
        else:
            self.title = "Sunsum"
            sender.title = "Toggle Ambient Mode (Off)"
            self.ambient_timer.stop()
            self.review_timer.stop()
            self.meta_review_timer.stop()
            rumps.notification("Sunsum Logger", "Ambient Mode OFF", "Ambient tracking paused.")

    @rumps.clicked("Open Dashboard")
    def view_timeseries(self, _):
        # Open the local Flask web dashboard
        subprocess.run(["open", "http://127.0.0.1:5000"])

    @rumps.clicked("Launch Browser")
    def launch_browser(self, _):
        # Launch BrowserOS (or fallback to default browser)
        browseros_path = os.path.expanduser("~/Applications/BrowserOS.app")
        if os.path.exists(browseros_path):
            subprocess.run(["open", browseros_path])
        else:
            rumps.notification("Sunsum Logger", "BrowserOS Not Found",
                            "Install BrowserOS to ~/Applications/ or use 'Open Dashboard' for now.")

def start_flask_dashboard():
    from sunsum_dashboard import app
    # Run silently, disable Werkzeug logging to not clutter terminal
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Start the local UI dashboard in the background
    threading.Thread(target=start_flask_dashboard, daemon=True).start()
    SunsumApp().run()
