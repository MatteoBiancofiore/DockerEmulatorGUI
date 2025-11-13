# app.py
import tkinter as tk
import docker, sys
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import sv_ttk

# Importa our modules
import core.config_manager as config_manager
from core import docker_ops, system_ops
from utils.lock_manager import OperationLock
from gui import assets
from gui.main_window import MainWindow
from gui.node_window import NodeWindow
from gui.startup_window import choose_project_popup


class DTGApp:
    
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
        self.main_window = None # A single container

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

        # 3b. Execute Docker-Compose
        system_ops.exec_compose(self.compose_file)
        
        config_manager.save_recent_project(self.compose_file)
        self.project_name = self.compose_file.parent.name.lower()
        self.client = docker.from_env()

    def open_container_window(self, container_name):
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

    def _choose_project_popup(self):
        popup = tk.Toplevel(self.root)
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
            filepath = filedialog.askopenfilename(title="Select a .yml file",
                        filetypes=[("YAML files", "*.yml *.yaml")]) or None
            if filepath:
                selected_path["path"] = filepath
                popup.destroy()
        
        def exit_popup():
            popup.destroy()
            
        ttk.Button(popup, text="Open selected project", image=self.open_icon,
                   compound=tk.LEFT, command=select_existing).pack(pady=5)
        ttk.Button(popup, text="Browse new file", image=self.folder_icon,
                   compound=tk.LEFT, command=browse_new).pack(pady=5)
        ttk.Button(popup, text="Exit", image=self.exit_icon,
                   compound=tk.LEFT, command=exit_popup, width=4).pack(pady=5)

        popup.grab_set()
        self.root.wait_window(popup)
        return selected_path["path"]

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