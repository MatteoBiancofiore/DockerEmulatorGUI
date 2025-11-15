r"""
\file gui/main_window.py

\brief Main window class for DTG GUI

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
from tkinter import ttk, messagebox
import platform
import threading

from core import docker_ops, system_ops

class MainWindow(ttk.Frame):
    r"""
    \brief Main Window of DTG GUI.

    This class represents the main window of the DTG GUI application.
    It shows the list of Docker containers and allows users to
    start, stop, restart containers, and open terminal windows.

    \param parent The parent tkinter widget.
    \param controller The main application controller (DTGApp instance).
    """
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        
        # UI State
        self.tree = None
        self.refresh_btn = None
        self.start_button = None
        self.stop_button = None
        self.context_menu = None
        
        self._build_main_ui()
        
        self.pack(fill="both", expand=True)

    def _build_main_ui(self):
        r"""
        \brief Utility function to build the main UI components.

        This fuction builds the Treeview for displaying Docker containers,
        the control buttons, and sets up the context menu for container actions.

        \return None
        """
        self.tree = ttk.Treeview(self, columns=("Status",), show="tree headings")
        self.tree.bind("<Double-1>", self.on_tree_select)

        if platform.system() == "Darwin":
            self.tree.bind("<Button-2>", self.show_context_menu)  
            self.tree.bind("<Control-Button-1>", self.show_context_menu)
        else:
            self.tree.bind("<Button-3>", self.show_context_menu)

        self.parent.bind("<FocusOut>", self.close_context_menu)
        self.parent.bind("<Button-1>", self.close_context_menu)
        self.parent.option_add("*TCombobox*Listbox.font", ("Arial", 12))
        
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 20), rowheight=50)
        style.configure("Treeview.Heading", font=("Arial", 18), padding=5)

        self.tree.heading("#0", text="Container")
        self.tree.heading("Status", text="Status")
        self.tree.column("Status", anchor="center")
        self.tree.pack(fill="both", expand=True)

        buttons_frame = tk.Frame(self)
        buttons_frame.pack(pady=10)

        self.refresh_btn = ttk.Button(buttons_frame, text="Refresh", 
            image=self.controller.refresh_icon,
            compound=tk.LEFT, command=self.refresh_containers)
        self.refresh_btn.pack()

        self.start_button = ttk.Button(buttons_frame, text="Start All", 
            image=self.controller.start_icon, compound=tk.LEFT, 
            command=self.start_all_containers)
        self.start_button.pack(side=tk.LEFT, padx=10, pady= 5)

        self.stop_button = ttk.Button(buttons_frame, text="Stop All", 
            image=self.controller.stop_icon, compound=tk.LEFT, 
            command=self.stop_all_containers)
        self.stop_button.pack(side=tk.LEFT, padx=10)

        self.context_menu = tk.Menu(self.parent, tearoff=0)

    # Business logic methods needed for main window
    
    def refresh_containers(self):
        r"""
        \brief Utility function to refresh the list of Docker containers shown in the GUI.

        This fuction queries Docker via docker_ops for the current status of containers related 
        to the active project and updates the Treeview accordingly. 
        It also handles closing any open windows or terminals for containers 
        that have been removed or stopped.

        \return None

        \throw DockerError if Docker is not reachable
        """
        try:
            docker_containers = docker_ops.get_project_containers(
                self.controller.client, self.controller.project_name
            )
            docker_container_names = {c.name for c in docker_containers}
        except Exception as e:
            messagebox.showerror("Docker Error", f"Docker is unavailable at the moment!\n{e}")
            return 

        tree_container_names = set(self.tree.get_children())
        deleted_names = tree_container_names - docker_container_names
        
        for name in deleted_names:
            self.tree.delete(name)
            if name in self.controller.open_windows:
                try: self.controller.open_windows[name].force_close()
                except (tk.TclError, KeyError): pass
            if name in self.controller.open_terminals:
                proc = self.controller.open_terminals.pop(name, None)
                if proc and proc.poll() is None:
                    try: proc.terminate() 
                    except Exception: pass    

        for c in docker_containers:
            if c.status != "running":
                if c.name in self.controller.open_windows:
                    try: self.controller.open_windows[c.name].force_close()
                    except (tk.TclError, KeyError): pass
                if c.name in self.controller.open_terminals:
                    processo = self.controller.open_terminals.pop(c.name, None)
                    if processo and processo.poll() is None:
                        try: processo.terminate()
                        except Exception: pass
        
            if not self.controller.lock_manager.is_locked(c.id):
                if c.status == "running":
                    icon = self.controller.running_icon
                elif c.status == "exited":
                    icon = self.controller.exited_icon
                else:
                    icon = self.controller.other_icon

                if self.tree.exists(c.name):
                    self.tree.item(c.name, values=(c.status,), image=icon)
                else:
                    self.tree.insert("", "end", iid=c.name,
                                     text=f"  {c.name}",
                                     values=(c.status,), image=icon)

    def start_container(self, row_id):
        r"""
        \brief Utility function to start a Docker container from the GUI.

        This function attempts to start the specified Docker container via docker_ops. 
        It checks if the container is already running or locked, 
        and updates the GUI accordingly.
        The starting operation is performed in a separate thread to keep the GUI responsive.

        \param row_id The identifier of the container to start (container name).

        \throw DockerError if Docker is not reachable
        """
        try:
            container = docker_ops.get_container(self.controller.client, row_id)
        except Exception as e:
            messagebox.showerror("Docker Error", str(e))
            return

        if self.controller.lock_manager.is_locked(container.id):
            messagebox.showwarning("Busy", "You can't do that right now!")
            return

        if container.status == "running":
            messagebox.showinfo("Notice", f"{container.name} is already running!") 
            return
        
        self.controller.lock_manager.lock(container.id, "start")
        self.tree.item(container.name, values=("starting...",))

        def do_start_worker():
            try:
                docker_ops.start_container_by_id(self.controller.client, container.id)
                self.parent.after(0, finalize_ui_success)
            except Exception as e:
                self.parent.after(0, finalize_ui_error, e)
        
        def finalize_ui_success():
            self.controller.lock_manager.unlock(container.id)
            self.refresh_containers()
        def finalize_ui_error(e):
            messagebox.showerror("Errore", f"Impossibile avviare {container.name}:\n{e}")
            self.controller.lock_manager.unlock(container.id)
            self.refresh_containers()

        threading.Thread(target=do_start_worker, daemon=True).start()

    def stop_container(self, row_id):
        r"""
        \brief Utility function to stop a Docker container from the GUI.

        This fuction attempts to stop the specified Docker container via docker_ops. 
        It checks if the container is already stopped or locked, 
        and updates the GUI accordingly.
        The stopping operation is performed in a separate thread to keep the GUI responsive.

        \param row_id The identifier of the container to start (container name).
        
        \return None

        \throw DockerError if Docker is not reachable
        """
        try:
            container = docker_ops.get_container(self.controller.client, row_id)
        except Exception as e:
            messagebox.showerror("Docker error", str(e))
            return

        if self.controller.lock_manager.is_locked(container.id):
            messagebox.showwarning("Busy", "You can't do that right now!")
            return
        if container.status == "exited":
            messagebox.showinfo("Notice", f"{container.name} is not running!")
            return
        
        self.controller.lock_manager.lock(container.id, "stop")
        self.set_buttons_state("disabled") 
        self.tree.item(container.name, values=("exiting...",), image=self.controller.exited_icon)

        def close_window_if_open():
            if container.name in self.controller.open_windows:
                try: self.controller.open_windows[container.name].force_close()
                except (tk.TclError, KeyError): pass 
        self.parent.after(0, close_window_if_open) 

        def do_stop_worker():
            try:
                docker_ops.stop_container_by_id(self.controller.client, container.id)
                self.parent.after(0, finalize_ui_success)
            except Exception as e:
                self.parent.after(0, finalize_ui_error, e)

        def finalize_ui_success():
            self.controller.lock_manager.unlock(container.id)
            self.refresh_containers() 
            self.reset_operation_flag()
        def finalize_ui_error(e):
            messagebox.showerror("Error", f"Can't stop {container.name}:\n{e}")
            self.controller.lock_manager.unlock(container.id)
            self.refresh_containers()
            self.reset_operation_flag()
            
        threading.Thread(target=do_stop_worker, daemon=True).start()

    def restart_container(self, row_id):
        r"""
        \brief Utility function to restart a Docker container from the GUI.

        This fuction attempts to restart the specified Docker container via docker_ops. 
        It checks if the container is locked, and updates the GUI accordingly.
        The restarting operation is performed in a separate thread to keep the GUI responsive.
        
        \param row_id The identifier of the container to start (container name).

        \return None

        \throw DockerError if Docker is not reachable
        """
        try:
            container = docker_ops.get_container(self.controller.client, row_id)
        except Exception as e:
            messagebox.showerror("Docker Error", str(e))
            return

        if self.controller.lock_manager.is_locked(container.id):
            messagebox.showwarning("Busy", "You can't do that right now!")
            return
        if not self.controller.lock_manager.lock(container.id, "restart"):
            return
            
        self.set_buttons_state("disabled") 
        self.tree.item(container.name, values=("restarting...",), image=self.controller.exited_icon)
        
        def do_restart_worker():
            try:
                docker_ops.restart_container_by_id(self.controller.client, container.id)
                self.parent.after(0, finalize_ui_success)
            except Exception as e:
                self.parent.after(0, finalize_ui_error, e)

        def finalize_ui_success():
            self.controller.lock_manager.unlock(container.id)
            self.refresh_containers()
            self.reset_operation_flag()
        def finalize_ui_error(e):
            messagebox.showerror("Error", f"Can't restart {container.name}:\n{e}")
            self.controller.lock_manager.unlock(container.id)
            self.refresh_containers()
            self.reset_operation_flag()
            
        threading.Thread(target=do_restart_worker, daemon=True).start()

    def start_all_containers(self):
        try:
            containers = docker_ops.get_project_containers(
                self.controller.client, self.controller.project_name
            )
        except Exception as e:
            messagebox.showerror("Docker Error", f"Containers could not be listed\n{e}")
            return
        for container in containers:
            if container.status != "running":
                self.start_container(container.name)

    def stop_all_containers(self, on_done=None):
        self.set_buttons_state("disabled") 
        containers_to_stop = [] 
        
        for row_id in self.tree.get_children():
            current_status = self.tree.item(row_id, "values")[0]
            if "running" in current_status:
                try:
                    container = docker_ops.get_container(self.controller.client, row_id)
                    container_id = container.id
                    container_name = container.name
                    self.controller.lock_manager.lock(container_id, "stop")
                    containers_to_stop.append((container_name, container_id))
                    self.tree.item(row_id, values=("exiting...",), image=self.controller.exited_icon)
                    if row_id in self.controller.open_windows:
                        try: self.controller.open_windows[row_id].force_close()
                        except(tk.TclError, KeyError): pass
                except Exception as e:
                    print(f"Errore in stop_all: {e}")

        def parallel_stop_manager():
            threads = []
            def stop_worker(container_name, container_id):
                try:
                    docker_ops.stop_container_by_id(self.controller.client, container_name)
                except Exception as e:
                    print(f"Errore durante l'arresto di {container_name}: {e}")
                finally:
                    self.controller.lock_manager.unlock(container_id) 

            for name, c_id in containers_to_stop:
                thread = threading.Thread(target=stop_worker, args=(name, c_id), daemon=True)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            self.parent.after(0, self.reset_operation_flag)
            self.parent.after(0, self.refresh_containers)
            if on_done:
                self.parent.after(0, on_done)

        threading.Thread(target=parallel_stop_manager, daemon=True).start()

    def open_terminal(self, row_id):
        r"""
        \brief Utility function to open a terminal window for a Docker container from the GUI.

        This fuction uses system_ops to open a terminal window attached 
        to the specified Docker container. 
        It checks if the container is locked or already has an open terminal.

        \param row_id The identifier of the container to open a terminal for (container name).

        \return None

        \throw TerminalError if the terminal could not be opened
        """
        try:
            container = docker_ops.get_container(self.controller.client, row_id)
        except Exception as e:
            messagebox.showerror("Docker Error", str(e))
            return

        if self.controller.lock_manager.is_locked(container.id):
            messagebox.showwarning("Busy", "You can't do that right now!")
            return
        if container.status != "running":
            messagebox.showinfo("Notice", f"{container.name} is not running!") 
            return
        
        if container.name in self.controller.open_terminals:
            proc = self.controller.open_terminals[container.name]
            if proc.poll() is None:
                messagebox.showwarning("Already opened", f"A terminal for '{container.name}' is already opened.", parent=self.parent)
                return 
            else:
                del self.controller.open_terminals[container.name]

        try:
            proc = system_ops.open_terminal(container.name)
            self.controller.open_terminals[container.name] = proc
        except system_ops.TerminalError as e:
            messagebox.showerror("Error", str(e), parent=self.parent)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open terminal:\n{e}", parent=self.parent)
    
    def show_context_menu(self, event):
            row_id = self.tree.identify_row(event.y)
            self.tree.selection_set(row_id)
            if row_id:
                self.context_menu.delete(0, tk.END)
                self.context_menu.add_command(label="Channel Emulator", font=("Arial", 14), 
                    command=lambda: self.controller.open_container_window(row_id))
                self.context_menu.add_command(label="Start", font=("Arial", 14), 
                    command=lambda: self.start_container(row_id))
                self.context_menu.add_command(label="Stop", font=("Arial", 14), 
                    command=lambda: self.stop_container(row_id))
                self.context_menu.add_command(label="Restart", font=("Arial", 14), 
                    command=lambda: self.restart_container(row_id))
                self.context_menu.add_command(label="Terminal", font=("Arial", 14), 
                    command=lambda: self.open_terminal(row_id))
                self.context_menu.post(event.x_root, event.y_root)

    def close_context_menu(self, event=None):
        try:
            self.context_menu.unpost()
        except:
            pass

    def set_buttons_state(self, state):
        self.refresh_btn.config(state=state)
        self.start_button.config(state=state)
        self.stop_button.config(state=state)

    def reset_operation_flag(self):
        if not self.controller.lock_manager.has_active_locks():
            self.set_buttons_state("normal")

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            container_name = selected[0]
            # Open new window with controller
            self.controller.open_container_window(container_name)