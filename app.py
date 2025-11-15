r"""
\file app.py

\brief The central orchestrator of whole application 

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

import tkinter as tk
import docker, sys
from tkinter import messagebox
from pathlib import Path
import sv_ttk

# Import our modules
import core.config_manager as config_manager
from core import docker_ops, system_ops
from utils.lock_manager import OperationLock
from gui import assets
from gui.main_window import MainWindow
from gui.node_window import NodeWindow
from gui.startup_window import choose_project_popup


class DTGApp:
    r"""
    \brief Main Controller that handle DTG lifecycle.

    The DTGApp class is responsible for initializing the environment, 
    connecting to Docker daemon and coordinating between MainWindow
    and individual nodes windows.

    Its purpose is to store the app's state which includes:
    - Docker client.
    - Active docker-compose file.
    - List of open windows.
    - Lock for asynchronous operations.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.withdraw()

        # Application STATE
        self.open_windows = {}
        self.open_terminals = {}
        self.lock_manager = OperationLock()
        self.project_name = None
        self.compose_file = None
        self.client = None

        # Icons
        self.running_icon = assets.load_image(assets.IMAGE_DIR / "running.png")
        self.exited_icon = assets.load_image(assets.IMAGE_DIR / "exited.png")
        self.other_icon = assets.load_image(assets.IMAGE_DIR / "other.png")
        self.refresh_icon = assets.load_image(assets.IMAGE_DIR / "refresh.png")
        self.start_icon = assets.load_image(assets.IMAGE_DIR / "start.png")
        self.stop_icon = assets.load_image(assets.IMAGE_DIR / "stop.png")
        self.folder_icon = assets.load_image(assets.IMAGE_DIR / "folder.png")
        self.open_icon = assets.load_image(assets.IMAGE_DIR / "open.png")
        self.exit_icon = assets.load_image(assets.IMAGE_DIR / "exit.png")
        
        # Main Widget UI
        self.main_window = None

        # STARTING LOGIC
        try:
            self._run_startup()
        except Exception as e:
            messagebox.showerror("Error while starting", str(e))
            self.root.destroy()
            sys.exit(1)

        # If all good, start UI
        if self.compose_file:
            sv_ttk.set_theme("dark")
            self.root.title("DTN & Emulator Control GUI")

            # Create a new istance of MainWindow and pass self
            self.main_window = MainWindow(self.root, controller=self)

            self.root.protocol("WM_DELETE_WINDOW", self.on_main_window_close)
            self.root.deiconify()

            # Update window
            self.main_window.refresh_containers()

    # Invoked by app.py
    def run(self):
        self.root.mainloop()

    def _run_startup(self):
        # Load icons needed for popup
        icons = {
            'open': self.open_icon,
            'folder': self.folder_icon,
            'exit': self.exit_icon
        }

        self.compose_file = choose_project_popup(self.root, icons)
        
        if not self.compose_file:
            return
            
        self.compose_file = Path(self.compose_file)

        # Execute Docker-Compose via system_ops
        system_ops.exec_compose(self.compose_file)
        
        # Save recent project via config_manager
        config_manager.save_recent_project(self.compose_file)
        self.project_name = self.compose_file.parent.name.lower()
        self.client = docker.from_env()

    def open_container_window(self, container_name):
        r"""
        \brief Open a new window for the given container.

        This method checks if the container is running, if a window
        for the container is already open, and if the container is locked.
        If all checks pass, it creates a new NodeWindow for the container
        and tracks it in the open_windows dictionary.

        \param container_name The name of the container to open the window for.

        \return None
        """
        try:
            container = docker_ops.get_container(self.client, container_name)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.root)
            return

        if container.status != "running":
            messagebox.showinfo("Notice", f"{container.name} is not running!")
            return
        
        # Check if is already opened
        if container_name in self.open_windows:
            self.open_windows[container_name].lift()
            self.open_windows[container_name].focus_force()
            return

        # Check if its locked
        if self.lock_manager.is_locked(container.id):
            messagebox.showwarning("Busy", "You can't do that right now!", parent=self.root)
            return

        # Create new window
        new_window = NodeWindow(self.root, self, container_name)

        # Add window to tracker
        self.open_windows[container_name] = new_window

    def show_exiting_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Exiting...")
        popup.geometry("250x80")
        popup.resizable(False, False)
        popup.grab_set()
        tk.Label(popup, text="Stopping containers...\nPlease wait", padx=20, pady=20).pack()
        return popup

    def on_main_window_close(self):
        if self.lock_manager.has_active_locks():
            if self.root.winfo_exists():
                messagebox.showwarning("Operation running", "Wait for the operations to finish...", parent=self.root)
        else:
            if messagebox.askokcancel("Quit", "Are you sure you want to exit?", parent=self.root):
                popup = self.show_exiting_popup()
                def finish_close():
                    if popup.winfo_exists():
                        popup.destroy()
                    self.root.destroy()
                
                self.main_window.stop_all_containers(on_done=finish_close)