#!/usr/bin/env python3
"""
=============================================================================
DARWIN Sovereign Engine - Meta-OCR Menu Bar Controller (macOS Native)
=============================================================================
Provides native macOS top menu bar controls for ambient OCR tracking,
Akan Ontology classification, and 4D Spatiotemporal TerminusDB syncing.
=============================================================================
"""

import os
import sys
import time
import subprocess
import threading
import datetime
from AppKit import (
    NSApplication, NSStatusBar, NSMenu, NSMenuItem, 
    NSVariableStatusItemLength, NSObject, NSWorkspace
)
from PyObjCTools import AppHelper

# Import core OCR tracking pipeline
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import darwin_ocr_logger
except ImportError:
    darwin_ocr_logger = None

CONFIG = {
    "active": True,
    "mode": "Full Desktop", # Options: "Full Desktop", "BrowserOS Only"
    "interval_seconds": 60, # Options: 60, 300, 900
    "last_run": None,
    "event_count": 0
}

class DarwinMenuBarApp(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.update_title()

        # Build Menu
        self.menu = NSMenu.alloc().init()

        # 1. Status Toggle
        self.status_menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🟢 Status: Active (Click to Pause)", "toggleStatus:", ""
        )
        self.status_menu_item.setTarget_(self)
        self.menu.addItem_(self.status_menu_item)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # 2. Mode Submenu
        self.mode_menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🎯 Mode: Full Desktop", None, ""
        )
        mode_submenu = NSMenu.alloc().init()
        
        self.item_mode_full = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "✓ Full Desktop (Browser + All Apps)", "setModeFull:", ""
        )
        self.item_mode_full.setTarget_(self)
        mode_submenu.addItem_(self.item_mode_full)

        self.item_mode_browser = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "  BrowserOS Only", "setModeBrowser:", ""
        )
        self.item_mode_browser.setTarget_(self)
        mode_submenu.addItem_(self.item_mode_browser)

        self.mode_menu_item.setSubmenu_(mode_submenu)
        self.menu.addItem_(self.mode_menu_item)

        # 3. Interval Submenu
        self.interval_menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⏱️ Interval: 1 Minute", None, ""
        )
        interval_submenu = NSMenu.alloc().init()

        self.item_int_1m = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "✓ 1 Minute", "setInterval1m:", ""
        )
        self.item_int_1m.setTarget_(self)
        interval_submenu.addItem_(self.item_int_1m)

        self.item_int_5m = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "  5 Minutes", "setInterval5m:", ""
        )
        self.item_int_5m.setTarget_(self)
        interval_submenu.addItem_(self.item_int_5m)

        self.item_int_15m = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "  15 Minutes", "setInterval15m:", ""
        )
        self.item_int_15m.setTarget_(self)
        interval_submenu.addItem_(self.item_int_15m)

        self.interval_menu_item.setSubmenu_(interval_submenu)
        self.menu.addItem_(self.interval_menu_item)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # 4. Immediate Trigger Action
        self.run_now_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⚡ Capture & Classify Now", "triggerOCRNow:", ""
        )
        self.run_now_item.setTarget_(self)
        self.menu.addItem_(self.run_now_item)

        # 5. Open Dealbook Log
        self.dealbook_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "📖 Open Capability Dealbook", "openDealbook:", ""
        )
        self.dealbook_item.setTarget_(self)
        self.menu.addItem_(self.dealbook_item)

        # 6. Export 333-Min Meta-Review
        self.review_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "🧿 Export 333-Min Meta-Review", "exportMetaReview:", ""
        )
        self.review_item.setTarget_(self)
        self.menu.addItem_(self.review_item)

        self.menu.addItem_(NSMenuItem.separatorItem())

        # 7. Quit Button
        self.quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit DARWIN Meta-OCR", "terminate:", "q"
        )
        self.menu.addItem_(self.quit_item)

        self.status_item.setMenu_(self.menu)

        # Start Background Timer Loop
        self.running = True
        self.timer_thread = threading.Thread(target=self.loop_worker, daemon=True)
        self.timer_thread.start()
        print("🌿 DARWIN Meta-OCR Menu Bar Controller Running.")

    def update_title(self):
        if CONFIG["active"]:
            mins = CONFIG["interval_seconds"] // 60
            title = f"🌿 DARWIN [{mins}m]"
        else:
            title = "⏸️ DARWIN [Paused]"
        self.status_item.setTitle_(title)

    def get_frontmost_app(self) -> str:
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        return active_app.localizedName() if active_app else "Unknown"

    def toggleStatus_(self, sender):
        CONFIG["active"] = not CONFIG["active"]
        if CONFIG["active"]:
            self.status_menu_item.setTitle_("🟢 Status: Active (Click to Pause)")
        else:
            self.status_menu_item.setTitle_("🔴 Status: Paused (Click to Resume)")
        self.update_title()

    def setModeFull_(self, sender):
        CONFIG["mode"] = "Full Desktop"
        self.item_mode_full.setTitle_("✓ Full Desktop (Browser + All Apps)")
        self.item_mode_browser.setTitle_("  BrowserOS Only")
        self.mode_menu_item.setTitle_("🎯 Mode: Full Desktop")

    def setModeBrowser_(self, sender):
        CONFIG["mode"] = "BrowserOS Only"
        self.item_mode_full.setTitle_("  Full Desktop (Browser + All Apps)")
        self.item_mode_browser.setTitle_("✓ BrowserOS Only")
        self.mode_menu_item.setTitle_("🎯 Mode: BrowserOS Only")

    def setInterval1m_(self, sender):
        CONFIG["interval_seconds"] = 60
        self.item_int_1m.setTitle_("✓ 1 Minute")
        self.item_int_5m.setTitle_("  5 Minutes")
        self.item_int_15m.setTitle_("  15 Minutes")
        self.interval_menu_item.setTitle_("⏱️ Interval: 1 Minute")
        self.update_title()

    def setInterval5m_(self, sender):
        CONFIG["interval_seconds"] = 300
        self.item_int_1m.setTitle_("  1 Minute")
        self.item_int_5m.setTitle_("✓ 5 Minutes")
        self.item_int_15m.setTitle_("  15 Minutes")
        self.interval_menu_item.setTitle_("⏱️ Interval: 5 Minutes")
        self.update_title()

    def setInterval15m_(self, sender):
        CONFIG["interval_seconds"] = 900
        self.item_int_1m.setTitle_("  1 Minute")
        self.item_int_5m.setTitle_("  5 Minutes")
        self.item_int_15m.setTitle_("✓ 15 Minutes")
        self.interval_menu_item.setTitle_("⏱️ Interval: 15 Minutes")
        self.update_title()

    def triggerOCRNow_(self, sender):
        threading.Thread(target=self.execute_ocr_capture, daemon=True).start()

    def openDealbook_(self, sender):
        report_path = os.path.expanduser("~/capability_log.md")
        if not os.path.exists(report_path):
            report_path = os.path.expanduser("~/.sunsum/capability_timeseries.md")
        if os.path.exists(report_path):
            subprocess.run(["open", report_path])
        else:
            print(f"[!] Log file not found yet: {report_path}")

    def exportMetaReview_(self, sender):
        if darwin_ocr_logger:
            now_iso = datetime.datetime.now().isoformat()
            review_file = darwin_ocr_logger.generate_meta_review(now_iso)
            if review_file and os.path.exists(review_file):
                subprocess.run(["open", review_file])

    def execute_ocr_capture(self):
        if not CONFIG["active"]:
            return

        frontmost = self.get_frontmost_app()
        if CONFIG["mode"] == "BrowserOS Only" and "browser" not in frontmost.lower() and "chrome" not in frontmost.lower() and "darwin" not in frontmost.lower():
            print(f"[*] Skipping OCR capture: Frontmost app '{frontmost}' is not BrowserOS.")
            return

        print(f"[*] Executing Meta-OCR capture (Active App: {frontmost})...")
        if darwin_ocr_logger:
            try:
                screen_text = darwin_ocr_logger.capture_and_ocr()
                if screen_text and screen_text != "__OPSEC_VIOLATION__":
                    analysis = darwin_ocr_logger.analyze_capability(screen_text)
                    conn = darwin_ocr_logger.init_db()
                    darwin_ocr_logger.log_event(conn, analysis)
                    darwin_ocr_logger.generate_dealbook(conn)
                    CONFIG["event_count"] += 1
                    CONFIG["last_run"] = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"✅ OCR event #{CONFIG['event_count']} processed and synced to TerminusDB.")
            except Exception as e:
                print(f"[!] Error during Meta-OCR capture: {e}")

    def loop_worker(self):
        while self.running:
            time.sleep(1)
            if CONFIG["active"]:
                now = time.time()
                last_time = getattr(self, "_last_loop_time", 0)
                if now - last_time >= CONFIG["interval_seconds"]:
                    self._last_loop_time = now
                    self.execute_ocr_capture()

def main():
    app = NSApplication.sharedApplication()
    delegate = DarwinMenuBarApp.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()

if __name__ == "__main__":
    main()
