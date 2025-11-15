r"""
\file gui/startup_window.py

\brief The startup window for DTG application. Used to choose or create a Docker Compose project.

\copyright Copyright (c) 2025, Alma Mater Studiorum, University of Bologna, All rights reserved.
	
\par License

    This file is part of DTG (DTN Testbed GUI).

    DTG is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    DTG is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with DTG.  If not, see <http://www.gnu.org/licenses/>.

\author Matteo Biancofiore <matteo.biancofiore2@studio.unibo.it>
\date 13/11/2025

\par Supervisor
   Carlo Caini <carlo.caini@unibo.it>


\par Revision History:
| Date       |  Author         |   Description
| ---------- | --------------- | -----------------------------------------------
| 13/11/2025 | M. Biancofiore  |  Initial implementation for DTG project.
"""

import subprocess, platform, shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Import necessary modules
from core import config_manager

def choose_project_popup(parent, icons):
    r"""
    \brief Popup window to choose or create a Docker Compose project.

    This fucntion creates a popup window that allows the user to either select an existing
    Docker Compose project from a list of recent projects or browse the filesystem to select a
    new Docker Compose YAML file.

    \param parent The parent tkinter window.
    \param icons A dictionary containing icons for buttons.

    \return The path to the selected Docker Compose project file, or None if the user exits.

    """
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

        # --- Windows (or fallback) ---
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
        
    # use icon dictionary to create buttons with images
    ttk.Button(popup, text="Open selected project", image=icons['open'],
               compound=tk.LEFT, command=select_existing).pack(pady=5)
    ttk.Button(popup, text="Browse new file", image=icons['folder'],
               compound=tk.LEFT, command=browse_new).pack(pady=5)
    ttk.Button(popup, text="Exit", image=icons['exit'],
               compound=tk.LEFT, command=exit_popup, width=4).pack(pady=5)

    popup.grab_set()
    parent.wait_window(popup) # Wait for popup to close
    
    return selected_path["path"]