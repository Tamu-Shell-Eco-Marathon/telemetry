import tkinter as tk
from tkinter import messagebox
import subprocess
import os
from pathlib import Path
from datetime import datetime
import shutil

# --- PATH SETUP (Relative to this script) ---
# This ensures it works on ANY computer
SCRIPT_DIR = Path(__file__).parent.absolute()
STAGING_DIR = SCRIPT_DIR / "staging_logs"
REPO_LOGS_DIR = SCRIPT_DIR / "logs"

# Ensure directories exist
STAGING_DIR.mkdir(exist_ok=True)
REPO_LOGS_DIR.mkdir(exist_ok=True)

class SyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DIS Log Synchronizer")
        self.root.geometry("400x300")

        # --- UI ELEMENTS ---
        tk.Label(root, text="Shell Eco-marathon Telemetry Sync", font=("Arial", 12, "bold")).pack(pady=10)

        # 1. View Logs Button
        self.btn_view = tk.Button(root, text="1. View Files on Pico", command=self.view_pico_files)
        self.btn_view.pack(pady=5, fill='x', padx=50)

        # 2. Download Button
        self.btn_download = tk.Button(root, text="2. Download Logs to Staging (Timestamped)", command=self.download_logs)
        self.btn_download.pack(pady=5, fill='x', padx=50)

        # 3. Push to GitHub
        self.btn_push = tk.Button(root, text="3. Push Staging to GitHub", command=self.push_to_github)
        self.btn_push.pack(pady=5, fill='x', padx=50)

        # 4. Clear Pico (Red Button)
        self.btn_clear = tk.Button(root, text="⚠️ Clear Logs on Pico", fg="red", command=self.clear_pico)
        self.btn_clear.pack(pady=20, fill='x', padx=50)

    def view_pico_files(self):
        # TODO: Run 'mpremote fs ls :logs/' and show in a popup
        print("Viewing files...")

    def download_logs(self):
        # TODO: Run 'mpremote fs cp', then loop through downloaded files 
        # and rename them using datetime.now().strftime("%Y%m%d_%H%M%S")
        print("Downloading and timestamping...")

    def push_to_github(self):
        # TODO: Move files from STAGING_DIR to REPO_LOGS_DIR
        # Run subprocess git add, git commit, git push
        print("Pushing to cloud...")

    def clear_pico(self):
        # Ask for confirmation before deleting!
        if messagebox.askyesno("Warning", "Are you sure you want to permanently delete all logs on the Pico?"):
            # TODO: Run 'mpremote fs rm'
            print("Clearing Pico...")

if __name__ == "__main__":
    root = tk.Tk()
    app = SyncApp(root)
    root.mainloop()