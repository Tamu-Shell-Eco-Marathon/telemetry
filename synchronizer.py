import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
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
        self.root.geometry("400x500")

        # --- UI ELEMENTS ---
        tk.Label(root, text="Shell Eco-marathon Telemetry Sync", font=("Arial", 12, "bold")).pack(pady=10)

        # 1. View Logs Button
        self.btn_view = tk.Button(root, text="View Files on DIS", command=self.view_dis_files)
        self.btn_view.pack(pady=5, fill='x', padx=50)

        # 2. Download Button
        self.btn_download = tk.Button(root, text="Download Logs to Staging (Timestamped)", command=self.download_logs)
        self.btn_download.pack(pady=5, fill='x', padx=50)

        # 3. Push to GitHub
        self.btn_push = tk.Button(root, text="Push Staging to GitHub", command=self.push_to_github)
        self.btn_push.pack(pady=5, fill='x', padx=50)

        # 4. Clear DIS (Red Button)
        self.btn_clear = tk.Button(root, text="⚠️ Clear Logs on DIS", fg="red", command=self.clear_dis)
        self.btn_clear.pack(pady=20, fill='x', padx=50)

        # 5. Log Output Area
        tk.Label(root, text="Activity:", font=("Arial", 10, "bold")).pack(pady=(5, 0), anchor="w", padx=10)
        self.log_text = scrolledtext.ScrolledText(root, height=10, state='disabled', font=("Consolas", 9))
        self.log_text.pack(pady=5, fill='both', expand=True, padx=10)

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()

    def view_dis_files(self):
        self.log("Listing files in :Logs/...")
        try:
            result = subprocess.run(["mpremote", "fs", "ls", ":Logs/"], capture_output=True, text=True)
            if result.returncode != 0:
                self.log(f"Error listing files: {result.stderr.strip()}")
                return

            output = result.stdout.strip()
            if not output:
                self.log("Directory :Logs/ is empty.")
                messagebox.showinfo("Info", "No logs found on DIS.")
                return

            # Parse filenames (mpremote ls output: "   size filename")
            files = []
            for line in output.splitlines():
                parts = line.split()
                # Skip the command echo line (e.g., "ls :Logs/")
                if parts and parts[0] == "ls":
                    continue
                if len(parts) >= 2:
                    filename = parts[-1]
                    if filename not in (".", ".."):
                        files.append(filename)
            
            if not files:
                self.log("No files found in output.")
                return

            self.open_file_manager(files)

        except FileNotFoundError:
            self.log("Error: 'mpremote' not found.")
        except Exception as e:
            self.log(f"An unexpected error occurred: {e}")

    def open_file_manager(self, files):
        top = tk.Toplevel(self.root)
        top.title("DIS File Manager")
        top.geometry("400x400")

        tk.Label(top, text="Select files from Logs/", font=("Arial", 10, "bold")).pack(pady=5)

        # Scrollable Listbox
        frame = tk.Frame(top)
        frame.pack(fill='both', expand=True, padx=10)
        
        scrollbar = tk.Scrollbar(frame, orient="vertical")
        listbox = tk.Listbox(frame, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        scrollbar.pack(side="right", fill="y")
        listbox.pack(side="left", fill="both", expand=True)

        for f in files:
            listbox.insert(tk.END, f)

        # Buttons
        btn_frame = tk.Frame(top)
        btn_frame.pack(fill='x', padx=10, pady=10)

        def get_selected():
            return [listbox.get(i) for i in listbox.curselection()]

        def on_preview():
            selected = get_selected()
            if not selected: return
            if len(selected) > 1:
                messagebox.showwarning("Selection Error", "Please select only one file to preview.")
                return
            self.preview_file(selected[0])

        def on_download(delete=False):
            selected = get_selected()
            if not selected: return
            if delete and not messagebox.askyesno("Confirm", f"Download and DELETE {len(selected)} files?"):
                return
            top.destroy()
            self.batch_process(selected, delete)

        def on_delete_selected():
            selected = get_selected()
            if not selected: return
            if messagebox.askyesno("Confirm", f"Permanently delete {len(selected)} selected files?"):
                top.destroy()
                self.batch_delete(selected)

        def on_delete_all():
            if messagebox.askyesno("Confirm", "Permanently delete ALL files in this list?"):
                top.destroy()
                self.batch_delete(files)

        btn_preview = tk.Button(btn_frame, text="Preview Selected", command=on_preview, state='disabled')
        btn_preview.pack(fill='x', pady=2)

        def on_selection_change(event):
            if len(listbox.curselection()) == 1:
                btn_preview.config(state='normal')
            else:
                btn_preview.config(state='disabled')

        listbox.bind('<<ListboxSelect>>', on_selection_change)

        tk.Button(btn_frame, text="Download Selected", command=lambda: on_download(False)).pack(fill='x', pady=2)
        tk.Button(btn_frame, text="Download & Delete Selected", command=lambda: on_download(True)).pack(fill='x', pady=2)
        tk.Button(btn_frame, text="Delete Selected", fg="red", command=on_delete_selected).pack(fill='x', pady=2)
        tk.Button(btn_frame, text="Delete ALL Logs", fg="red", command=on_delete_all).pack(fill='x', pady=(10, 2))

    def preview_file(self, filename):
        self.log(f"Previewing {filename}...")
        try:
            # Use 'cat' to read file content directly from DIS
            result = subprocess.run(["mpremote", "fs", "cat", f":Logs/{filename}"], capture_output=True, text=True)
            if result.returncode != 0:
                self.log(f"Error reading file: {result.stderr.strip()}")
                return

            content = result.stdout
            
            # Create preview window
            top = tk.Toplevel(self.root)
            top.title(f"Preview: {filename}")
            top.geometry("600x400")
            
            text_area = scrolledtext.ScrolledText(top, font=("Consolas", 10))
            text_area.pack(fill='both', expand=True)
            text_area.insert(tk.END, content)

        except Exception as e:
            self.log(f"Preview error: {e}")

    def batch_process(self, files, delete):
        self.log(f"Processing {len(files)} files...")
        for filename in files:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_name = f"{ts}_{filename}"
            local_path = STAGING_DIR / local_name
            remote_path = f":Logs/{filename}"

            self.log(f"Downloading {filename}...")
            try:
                subprocess.run(["mpremote", "fs", "cp", remote_path, str(local_path)], check=True)
                if delete:
                    self.log(f"Deleting {filename}...")
                    subprocess.run(["mpremote", "fs", "rm", remote_path], check=True)
            except subprocess.CalledProcessError as e:
                self.log(f"Error with {filename}: {e}")
        self.log("Operation complete.")

    def batch_delete(self, files):
        self.log(f"Deleting {len(files)} files...")
        for filename in files:
            try:
                subprocess.run(["mpremote", "fs", "rm", f":Logs/{filename}"], check=True)
                self.log(f"Deleted {filename}")
            except subprocess.CalledProcessError:
                self.log(f"Failed to delete {filename}")
        self.log("Deletion complete.")

    def download_logs(self):
        # TODO: Run 'mpremote fs cp', then loop through downloaded files 
        # and rename them using datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log("Downloading and timestamping...")

    def push_to_github(self):
        # TODO: Move files from STAGING_DIR to REPO_LOGS_DIR
        # Run subprocess git add, git commit, git push
        self.log("Pushing to cloud...")

    def clear_dis(self):
        # Ask for confirmation before deleting!
        if messagebox.askyesno("Warning", "Are you sure you want to permanently delete all logs on the DIS?"):
            # TODO: Run 'mpremote fs rm'
            self.log("Clearing DIS...")

if __name__ == "__main__":
    root = tk.Tk()
    app = SyncApp(root)
    root.mainloop()