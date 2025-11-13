# gui/startup_window.py
import subprocess, platform, shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Import necessary modules
from core import config_manager

def choose_project_popup(parent, icons):
 
    popup = tk.Toplevel(parent)
    popup.title("Select Docker Compose project")
    popup.geometry("600x500")
    popup.wm_minsize(600, 500)

    ttk.Label(popup, text="Recent projects:", font=("Arial", 16)).pack(pady=10)
    
    projects = config_manager.load_recent_projects()
    listbox = tk.Listbox(popup, font=("Arial", 13), selectmode=tk.SINGLE)
    listbox.pack(fill=tk.BOTH, padx=20, pady=10)
    
    for p in projects:
        listbox.insert(tk.END, p)

    selected_path = {"path": None}
    
    def select_existing():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select a project...", parent=popup)
            return
        selected_path["path"] = projects[sel[0]]
        popup.destroy()

    def browse_new():

        filepath = None
        flag = False

        # --- Linux ---
        if platform.system().startswith("Linux"):
            flag = True
            if shutil.which("zenity"):
                result = subprocess.run(
                    ["zenity", "--file-selection", "--title=Select a .yml file"],
                    capture_output=True, text=True
                )
                filepath = result.stdout.strip() or None
            elif shutil.which("kdialog"):
                result = subprocess.run(
                    ["kdialog", "--getopenfilename"],
                    capture_output=True, text=True
                )
                filepath = result.stdout.strip() or None

        # --- macOS ---
        elif platform.system() == "Darwin":
            flag = True
            if shutil.which("osascript"):
                # AppleScript to open file select on macOS
                script = (
                    'set theFile to POSIX path of (choose file with prompt "Select a .yml file")\n'
                    'do shell script "echo " & quoted form of theFile'
                )
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True, text=True
                )
                filepath = result.stdout.strip() or None

        # --- Windows (o fallback) ---
        if not filepath and flag is False:
            filepath = filedialog.askopenfilename(
                        title="Select a .yml file",
                        filetypes=[("YAML files", "*.yml *.yaml")]
                    ) or None

        if filepath:
            if filepath.endswith((".yml", ".yaml")):
                selected_path["path"] = filepath
                popup.destroy()
            else:
                messagebox.showerror("Error", "Select a docker compose project\n(file .yml or .yaml)", parent=popup)   
    
    def exit_popup():
        selected_path["path"] = None
        popup.destroy()
        
    # Usa il dizionario 'icons' che abbiamo passato
    ttk.Button(popup, text="Open selected project", image=icons['open'],
               compound=tk.LEFT, command=select_existing).pack(pady=5)
    ttk.Button(popup, text="Browse new file", image=icons['folder'],
               compound=tk.LEFT, command=browse_new).pack(pady=5)
    ttk.Button(popup, text="Exit", image=icons['exit'],
               compound=tk.LEFT, command=exit_popup, width=4).pack(pady=5)

    popup.grab_set()
    parent.wait_window(popup) # Wait for popup to close
    
    return selected_path["path"]