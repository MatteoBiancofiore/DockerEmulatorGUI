import tkinter as tk
import docker, threading , ipaddress, shlex, shutil, sys, platform, json, subprocess, os
from tkinter import ttk, messagebox, scrolledtext, filedialog
from PIL import Image, ImageTk
from pathlib import Path
import sv_ttk

# Determine the base directory depending on whether the script is frozen or not
if getattr(sys, 'frozen', False):
    # if frozen (e.g., PyInstaller) the base dir is the temp folder created by PyInstaller
    BASE_DIR = Path(sys._MEIPASS)
else:
    # if not frozen, use the script's directory
    BASE_DIR = Path(__file__).parent

def get_config_dir():
    if sys.platform == "win32":
        # Windows: C:\Users\<username>\AppData\Roaming\<AppName>
        config_path = Path.home() / "AppData" / "Roaming" / APP_NAME
    elif sys.platform == "darwin":
        # macOS: /Users/<username>/Library/Application Support/<AppName>
        config_path = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        # Linux (e altri): /home/<username>/.config/<AppName> (standard XDG)
        config_path = Path.home() / ".config" / APP_NAME
    
    # Create directory (if it does not exist)
    config_path.mkdir(parents=True, exist_ok=True)
    return config_path

# Images directory
APP_NAME = "DockerEmulatorGUI"
IMAGE_DIR = BASE_DIR / "images"
CONFIG_DIR = get_config_dir()
RECENT_PROJECTS_FILE = CONFIG_DIR / "recent_projects.json"

open_windows = {}  # keep track of open container windows

# class to lock operations on containers
class OperationLock:
    def __init__(self):
        self._locks = {}

    def lock(self, container_id, op):
        if self._locks.get(container_id, {}).get("running", False):
            return False # already locked
        
        self._locks[container_id] = {"running": True, "operation": op}
        return True

    def unlock(self, container_id):
        self._locks[container_id] = {"running": False, "operation": None}

    def is_locked(self, container_id):
        return self._locks.get(container_id, {}).get("running", False)
    
    # return true if any lock is active
    def has_active_locks(self):
        return any(v.get("running", False) for v in self._locks.values())

lock_manager = OperationLock()

def load_image(path, size=(20, 20)):
    try:
        img = Image.open(path)
        img = img.resize(size)
        return ImageTk.PhotoImage(img)
    except (FileNotFoundError, OSError):
        return None

def exec_compose(compose_file):
    
    cmd = None
    
    # Check if the standalone 'docker-compose' (v1) is available
    if shutil.which("docker-compose"):
        cmd = ["docker-compose", "-f", str(compose_file), "up", "-d"]
    # If not, check if 'docker' (which might include the 'compose' plugin, v2) is available
    elif shutil.which("docker"):
        try:
            # Try to run 'docker compose --version' to see if the v2 plugin is installed
            subprocess.run(["docker", "compose", "--version"], check=True, capture_output=True)
            cmd = ["docker", "compose", "-f", str(compose_file), "up", "-d"]
        except (subprocess.CalledProcessError, FileNotFoundError):
            # 'docker' executable exists, but the 'compose' plugin is missing
            pass # cmd remains None
            
    # If cmd is still None after all checks, show an error
    if cmd is None:
        messagebox.showerror(
            "Critical Error",
            "Docker Compose not found.\n\n"
            "This program requires either the standalone 'docker-compose' (v1) "
            "or the 'docker compose' plugin (v2) to be installed and available in your PATH."
        )
        return False

    try:
        # The 'up -d' command is idempotent; running it multiple times will not create 
        # duplicate containers but will update existing ones if the configuration changed.
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
    
    except subprocess.CalledProcessError as e:
        # Using the improved error message we discussed, translated into English
        error_message = (
            "An error occurred while running 'docker compose up'.\n\n"
            "This could be due to one of the following:\n\n"
            "1. Invalid Compose File: The selected file contains syntax errors, "
            "references an invalid path, or is unreadable.\n\n"
            "2. Image Not Found: A base image specified in the file (or its Dockerfile) "
            "could not be found or pulled.\n\n"
            "Please check the file's syntax and ensure all required Docker images "
            "are correct and accessible."
        )
        messagebox.showerror("Docker Compose Error", error_message)
        
        root.destroy()
        sys.exit()
        return False

    root.after(0, lambda: refresh_containers())
    return True

def get_project_containers(project_name):
    containers = client.containers.list(all=True, filters={"label":f"com.docker.compose.project={project_name}"})
    return sorted(containers, key=lambda c: c.name)

# Update docker container list
def refresh_containers():
    
    try:
        docker_containers = get_project_containers(project_name)
        docker_container_names = {c.name for c in docker_containers}
    except Exception as e:
        return 

    # container shown in TreeView
    tree_container_names = set(tree.get_children())

    # container in Tree but not in Docker
    deleted_names = tree_container_names - docker_container_names
    
    for name in deleted_names:
        tree.delete(name)
        
        if name in open_windows:
            try:
                open_windows[name].force_close()
            except (tk.TclError, KeyError): pass

    for c in docker_containers:
        if c.status != "running" and c.name in open_windows:
            try:
                open_windows[c.name].force_close()
            except (tk.TclError, KeyError): pass
       
        if not lock_manager.is_locked(c.id):
            if c.status == "running":
                icon = running_icon
            elif c.status == "exited":
                icon = exited_icon
            else:
                icon = other_icon

            if tree.exists(c.name): # update if it exists
                tree.item(c.name, values=(c.status,), image=icon)
            else: # insert if new  
                tree.insert(
                    "", "end",
                    iid=c.name,
                    text=f"  {c.name}",
                    values=(c.status,),
                    image=icon
                )

def start_container(row_id):

    container = client.containers.get(row_id)

    if lock_manager.is_locked(container.id):
        messagebox.showwarning("Busy", "You can't do that right now!")
        return

    if container.status == "running":
        messagebox.showinfo("Notice", f"{container.name} is already running!") 
        return
    
    lock_manager.lock(container.id, "start")
    
    def do_start():
        container.start()
        container.reload()

        def finalize():
            lock_manager.unlock(container.id)
            tree.item(container.name, values=(container.status,))
            refresh_containers()
 
        tree.after(0, finalize)

    threading.Thread(target=do_start).start()
    
def stop_container(row_id):

    container = client.containers.get(row_id)

    if lock_manager.is_locked(container.id):
        messagebox.showwarning("Busy", "You can't do that right now!")
        return

    if container.status == "exited":
       messagebox.showinfo("Notice", f"{container.name} is not running!")
       return
    
    lock_manager.lock(container.id, "stop")

    set_buttons_state("disabled") 

    tree.item(container.name, values=("exiting...",))
    tree.item(container.name, image=exited_icon)

    def close_window_if_open():
        if container.name in open_windows:
            try:
                open_windows[container.name].force_close()
            except (tk.TclError, KeyError):
                pass 

    tree.after(0, close_window_if_open)

    # New Thread to stop container
    def do_stop():
        container.stop()
        container.reload() 
        lock_manager.unlock(container.id)
        tree.after(0, reset_operation_flag) 
        tree.after(0, lambda: tree.item(container.name, values=(container.status)))
        
    threading.Thread(target=do_stop).start()

def restart_container(row_id):

    container = client.containers.get(row_id)

    if lock_manager.is_locked(container.id):
        messagebox.showwarning("Busy", "You can't do that right now!")
        return

    # Check if another long operation is running
    if not lock_manager.lock(container.id, "restart"):
        return

    set_buttons_state("disabled") 
    
    tree.item(container.name, values=("restarting...",))
    tree.item(container.name, image=exited_icon)
    
    def do_restart():
        container.restart()
        container.reload()
        tree.after(0, lambda: tree.item(container.name, values=(container.status,)))
        tree.after(0, lambda: tree.item(container.name, image=running_icon))
        tree.after(100, reset_operation_flag)
        lock_manager.unlock(container.id)
        

     # New Thread to restart container
    threading.Thread(target=do_restart).start()

def start_all_containers():
    containers = get_project_containers(project_name)
    for container in containers:
        if container.status != "running":
            start_container(container.name)

def stop_all_containers():

    set_buttons_state("disabled") 

    containers_to_stop = []
    for row_id in tree.get_children():
        current_status = tree.item(row_id, "values")[0]
        if "running" in current_status:
            tree.item(row_id, values=("exiting...",))
            tree.item(row_id, image=exited_icon)
            containers_to_stop.append(row_id)
            lock_manager.lock(client.containers.get(row_id).id, "stop")

            if row_id in open_windows:
                try:
                    open_windows[row_id].force_close()
                except(tk.TclError, KeyError):
                    pass

    def parallel_stop_manager():
        
        threads = []

        def stop_worker(container_name):
            container = client.containers.get(container_name)
            container.stop()
            lock_manager.unlock(container.id) 

        for name in containers_to_stop:
            thread = threading.Thread(target=stop_worker, args=(name,), daemon=True)
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        root.after(0, reset_operation_flag)
        root.after(0, refresh_containers)

    threading.Thread(target=parallel_stop_manager, daemon=True).start()

def open_terminal(row_id):
    container = client.containers.get(row_id)

    if lock_manager.is_locked(container.id):
        messagebox.showwarning("Busy", "You can't do that right now!")
        return

    if container.status != "running":
        messagebox.showinfo("Notice", f"{container.name} is not running!") 
        return

    system_platform = platform.system()
    escaped_name = shlex.quote(container.name)
    docker_cmd = f"docker exec -it {escaped_name} bash"
    title = f"{container.name} terminal"

    if system_platform == "Windows":
        # /c to run and terminate the process that start cmd.exe, /k to run and keep open the new cmd.exe
        terminal_cmd = ["cmd.exe", "/c", "start", f"{container.name} terminal",
                        "cmd.exe", "/c", f"{docker_cmd}"]
        
    elif system_platform == "Darwin":  # macOS
        # -e to execute AppleScript command to open Terminal and run docker exec, tell application "Terminal" to do script "command" (MAC specific)
        # \\033]0; sets the terminal title, \\007 ends the title command
        script = (
            f'tell application "Terminal" to do script '
            f'"echo -ne \'\\033]0;{title}\\007\'; {docker_cmd}; exit"'
        )
        terminal_cmd = ["osascript", "-e", script]
        
    else:  # Linux
        terminal_emulators = [
            "gnome-terminal",
            "konsole",
            "xfce4-terminal",
            "mate-terminal",
            "lxterminal",
            "x-terminal-emulator",
        ]
    
        found_term = False
        for term in terminal_emulators:
            path = shutil.which(term)
            if path:
                
                if "gnome-terminal" in os.path.realpath(path):
                    terminal_cmd = [path, "--title", title, "--", "bash", "-c", docker_cmd]

                elif term in ("konsole", "xfce4-terminal", "mate-terminal"):
                    terminal_cmd = [path, "--title", title, "-e", f"bash -c '{docker_cmd}'"]

                elif term == "lxterminal":
                    terminal_cmd = [path, "-T", title, "-e", f"bash -c '{docker_cmd}'"]

                else:  # fallback
                    terminal_cmd = [path, "-e", f"bash -c '{docker_cmd}'"]
                    
                
                found_term = True
                print(f"Debug: Terminal used: {term} (path: {path})")

                break
        
        if not found_term:
            messagebox.showerror(
                "Error",
                "No compatible terminal found.\n"
                "Please install one of:\n"
                "- gnome-terminal\n- konsole\n- xfce4-terminal\n- mate-terminal\n- lxterminal"
            )
            return

    try:
        subprocess.Popen(terminal_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open terminal:\n{e}")
    
# Menu
def show_context_menu(event):
    row_id = tree.identify_row(event.y)
    tree.selection_set(row_id)

    if row_id:
        context_menu.delete(0, tk.END)
        context_menu.add_command(label="Channel Emulator", font=("Arial", 14), command=lambda: open_container_window(row_id))
        context_menu.add_command(label="Start", font=("Arial", 14), command=lambda: start_container(row_id))
        context_menu.add_command(label="Stop", font=("Arial", 14), command=lambda: stop_container(row_id))
        context_menu.add_command(label="Restart", font=("Arial", 14), command=lambda: restart_container(row_id))
        context_menu.add_command(label="Terminal", font=("Arial", 14), command=lambda: open_terminal(row_id))
        context_menu.post(event.x_root, event.y_root)

def close_context_menu(event=None):
    try:
        context_menu.unpost()
    except:
        pass

def set_buttons_state(state):
    refresh_btn.config(state=state)
    start_button.config(state=state)
    stop_button.config(state=state)

def reset_operation_flag():
    if not lock_manager.has_active_locks():
        set_buttons_state("normal") # Riabilita i pulsanti

# Handle click
def on_tree_select(event):
    selected = tree.selection()
    if selected:
        container_name = selected[0]
        open_container_window(container_name)

def get_interfaces(container_id):

    container = client.containers.get(container_id)
    result = container.exec_run("ls /sys/class/net")
    
    if result.exit_code == 0:
        interfaces = result.output.decode('utf-8').strip().split('\n')
        interfaces =  [eth for eth in interfaces if eth and eth != "lo"]
    
        for eth in interfaces:

            # sh -c because of the pipe | that is not supported directly by exec_run
            cmd = f"sh -c \"ip a show {eth} | awk '/inet / {{print $2}}'\""
            result = container.exec_run(cmd)
            if result.exit_code == 0:
                ip = result.output.decode('utf-8').strip()
                if ip:
                    i = interfaces.index(eth)
                    eth += f" - {ip}"
                    interfaces[i] = eth
            else:
                interfaces.remove(eth)
            
        return interfaces
    
    return []

# Open Window
def open_container_window(container_name):
    
    container = client.containers.get(container_name)

    if container.status != "running":
        messagebox.showinfo("Notice", f"{container.name} is not running!")
        return
    else: 
        open_node_window(container_name)

def save_configs(container_name, interface, delay_spinbox, loss_spinbox, band_spinbox, limit_spinbox, win, config_status, save_btn):

    config = {
        "interface": interface,
        "delay": delay_spinbox.get(),
        "loss": loss_spinbox.get(),
        "band": band_spinbox.get(),
        "limit": limit_spinbox.get()
    }

    config_file = CONFIG_DIR / f"{container_name}_config.json"

    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        
        config_status[0] = True
        save_btn.config(text="Saved")

        def revert_save_text():
            try:
                if save_btn.winfo_exists():
                    if config_status[0] == True: 
                        save_btn.config(text="Save configs")
            except tk.TclError:
                pass

        win.after(2000, revert_save_text)

    except Exception:
        messagebox.showerror("Error", "Failed to save configs", parent=win)

def load_configs(container_name):

    config_file = CONFIG_DIR / f"{container_name}_config.json"

    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError: # if corrupted return default values
            pass

    return {"interface": "eth0", "delay": 0, "loss": 0, "band": 1.0, "limit": 10}

def open_node_window(container_name):

    config_status = [True]

    container = client.containers.get(container_name)

    if lock_manager.is_locked(container.id):
        messagebox.showwarning("Busy", "You can't do that right now!")
        return

    if container_name in open_windows:
        win = open_windows[container_name]
        win.lift()
        win.focus_force()
        return
    
    config = load_configs(container_name)

    win = tk.Toplevel(root)
    win.geometry("1150x700")
    win.wm_minsize(1150, 350)
    win.title(f"{container_name}")
    win.bind("<Button-1>", clear_focus)


    def on_close():
        
        if config_status[0] == False:
            # ask yer or no
            if not messagebox.askyesno(
                "Unsaved Changes", 
                "You have unsaved changes that will be lost.\nAre you sure you want to close?", 
                parent=win
            ):
                return

        del open_windows[container_name]
        win.destroy()

    def force_close():
        
        config_status[0] = True 
        on_close() 

    win.force_close = force_close       

    def set_config_dirty(*args):

        config_status[0] = False
        try:
            if save_btn.winfo_exists():
                save_btn.config(text="Save configs")
        except (tk.TclError, NameError):
            pass 


    title_frame = tk.Frame(win)
    ttk.Button(
        title_frame, 
        text="Close",  
        command=on_close,
        style="Accent.TButton"
    ).pack(padx=10, side="right")

    tk.Label(title_frame, text=f"Container: {container_name}", font=("Arial", 20, "bold")).pack(padx=10, side="left")
    title_frame.pack(fill="x", padx=5, pady=5)

    subtitle_frame = tk.Frame(win)
    tk.Label(subtitle_frame, text=f"Control window for channel emulator", font=("Arial", 16)).pack(padx=10, side="left")
    subtitle_frame.pack(fill="x",padx=5, pady=5)



    #  -- tc section --

    tc_frame = tc_frame = ttk.LabelFrame(win, text=" Traffic Control ", padding=(10,10))
    tc_frame.pack(pady=10, padx=10, fill="x")

    # Interface
    tk.Label(tc_frame, text="Interface:", font=("Arial", 13)).grid(row=1, column=0, padx=10, pady=5)
    interfaces = get_interfaces(container_name)
    interface_var = tk.StringVar()
    interface_combo = ttk.Combobox(tc_frame, textvariable=interface_var, values=interfaces, state="readonly", width=20, font=("Arial", 12))
    if interfaces:

        saved_iface_name = config.get("interface") 
        
        target_index = 0
        
        if saved_iface_name:
            for i, iface_string in enumerate(interfaces):
                if iface_string.startswith(saved_iface_name):
                    target_index = i
                    break 

        interface_combo.current(target_index)

    interface_combo.grid(row=2, column=0, padx=10)

    # Delay
    tk.Label(tc_frame, text="Delay (ms):", font=("Arial", 13)).grid(row=1, column=3, padx=10, pady=5)
    delay_spinbox = ttk.Spinbox(tc_frame, from_=0, to=999999, increment=10, font=("Arial", 12), width=5)
    delay_spinbox.set(config.get("delay", "0"))
    delay_spinbox.grid(row=2, column=3, padx=10)

    # Loss
    tk.Label(tc_frame, text="Loss (%):", font=("Arial", 13)).grid(row=1, column=4, padx=10, pady=5)
    loss_spinbox = ttk.Spinbox(tc_frame, from_=0, to=100, increment=5, font=("Arial", 12), width=5)
    loss_spinbox.set(config.get("loss", "0"))
    loss_spinbox.grid(row=2, column=4, padx=10)

    # Bandwidth
    tk.Label(tc_frame, text="Bandwidth (Mbit/s):", font=("Arial", 13)).grid(row=1, column=5, padx=10, pady=5)
    band_spinbox = ttk.Spinbox(
        tc_frame,
        from_=0.1,
        to=100.0,
        increment=0.1,   # 100 Kbps step
        font=("Arial", 12),
        format="%.1f",
        width=10
    )
    band_spinbox.set(config.get("band", "1.0"))
    band_spinbox.grid(row=2, column=5, padx=10)

    # Packet limit
    tk.Label(tc_frame, text="Limit (packets):", font=("Arial", 13)).grid(row=1, column=6, padx=10, pady=5)
    limit_spinbox = ttk.Spinbox(
        tc_frame,
        from_=0,
        to=100.0,
        increment=10,
        font=("Arial", 12),
        width=5
    )
    limit_spinbox.set(config.get("limit", "10"))
    limit_spinbox.grid(row=2, column=6, padx=10)

    # Apply button for tc qdisc
    apply_btn = ttk.Button(
        tc_frame, 
        text="Apply",
        command=lambda: do_tc(container_name, interface_var.get(), delay_spinbox, loss_spinbox, band_spinbox, limit_spinbox, output_box, win),
        style="Accent.TButton"
    )
    apply_btn.grid(row=2, column=7, padx=10, pady=5)

    # Save config button
    save_btn = ttk.Button(
        tc_frame, 
        text="Save configs",
        width=12,
        style="Accent.TButton",
        command=lambda: save_configs(
            container_name, 
            interface_var.get(), 
            delay_spinbox, 
            loss_spinbox, 
            band_spinbox, 
            limit_spinbox, 
            win, 
            config_status,
            save_btn
            )
    )
    save_btn.grid(row=2, column=8, padx=10, pady=10)
    
    # save every change on parameters

    interface_var.trace_add("write", set_config_dirty)
    
    delay_spinbox.bind("<KeyRelease>", set_config_dirty)
    delay_spinbox.bind("<ButtonRelease>", set_config_dirty) 
   
    loss_spinbox.bind("<KeyRelease>", set_config_dirty)
    loss_spinbox.bind("<ButtonRelease>", set_config_dirty)
   
    band_spinbox.bind("<KeyRelease>", set_config_dirty)
    band_spinbox.bind("<ButtonRelease>", set_config_dirty)

    limit_spinbox.bind("<KeyRelease>", set_config_dirty)
    limit_spinbox.bind("<ButtonRelease>", set_config_dirty)

    #  --  Ping section  --

    ping_frame = ttk.LabelFrame(win, text=" Network Test ", padding=(10,10))
    ping_frame.pack(pady=10)

    tk.Label(ping_frame, text="IP to ping:", font=("Arial", 13)).grid(row=0, column=0, padx=10, pady=5)
    ipaddr_entry = tk.Entry(ping_frame, width=16 ,font=("Arial", 13))
    ipaddr_entry.insert(0, "") 
    ipaddr_entry.grid(row=1, column=0, padx=10)

    ping_btn = ttk.Button(
        ping_frame, 
        text="Ping", 
        style="Accent.TButton",
        command=lambda: do_ping(container_name, ipaddr_entry, output_box, win, ping_btn)
    )
    ping_btn.grid(row=1, column=2, padx=10, pady=5)

    # -- Console section --

    # Toggle button
    toggle_btn = ttk.Button(win, text="Hide Console", command=lambda: toggle_console())
    toggle_btn.pack()

    # Frame console
    console_frame = tk.Frame(win)
    console_frame.pack(expand=True, fill="both", padx=10, pady=5)

    # Label + Clear Button
    label_frame = tk.Frame(console_frame)
    label_frame.pack(fill="x", padx=10, pady=5)
    output_label = tk.Label(label_frame, text="Output:", font=("Arial", 12))
    output_label.pack(side="left")
    clear_btn = ttk.Button(
        label_frame, 
        text="Clear console",
        command=lambda: clear_console(output_box))
    
    clear_btn.pack(side="right")

    # Textarea
    output_box = scrolledtext.ScrolledText(console_frame, font=("Courier New", 11))
    output_box.pack(expand=True, fill="both")
    output_box.config(state="disabled")

    show_console = False  # initial state
    def toggle_console():
        nonlocal show_console
        if show_console:
            console_frame.pack(expand=True, fill="both", padx=10, pady=5)
            toggle_btn.config(text="Hide Console")
            win.geometry("1150x700") # resize to original size
        else:
            console_frame.pack_forget()
            toggle_btn.config(text="Show Console")
            win.geometry("1150x430") # resize to smaller size
        show_console = not show_console
    
    win.protocol("WM_DELETE_WINDOW", on_close)
    open_windows[container_name] = win

def clear_console(output_box):
    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.config(state="disabled")

def do_tc(container_name, interface, delay_entry, loss_entry, band_entry, limit_entry, output_box, win):
    if not container_name: 
        return
    delay = delay_entry.get()
    loss = loss_entry.get()
    bandwidth = band_entry.get()
    limit = limit_entry.get()
    flag = True

    if not delay.isdigit() or int(delay) < 0:   
        messagebox.showwarning("Input Error", "Delay must be a non-negative integer.", parent=win)
        flag = False
    
    if not loss.isdigit() or int(loss) < 0 or int(loss) > 100:  
        messagebox.showwarning("Input Error", "Loss must be an integer between 0 and 100.", parent=win)
        flag = False

    if not limit.isdigit() or int(limit) < 0:  
        messagebox.showwarning("Input Error", "Limit must be a non negative integer.", parent=win)
        flag = False

    try:
        bw_value = float(bandwidth)
        if bw_value <= 0:
            messagebox.showwarning("Input Error", "Bandwidth must be a positive number.", parent=win)
            flag = False
    except ValueError:
        messagebox.showwarning("Input Error", "Bandwidth must be a valid number (e.g., 150 or 1.5).", parent=win)
        flag = False

    if flag == False:
        return
    
    container = client.containers.get(container_name)
    eth = interface.split(" - ")[0]  # get only the interface name without IP
    # tc qdisc replace dev eth1 root netem delay 20ms rate 10Mbit limit 50
    cmd = f"tc qdisc replace dev {eth} root netem delay {delay}ms loss {loss}% rate {bandwidth}Mbit limit {limit}"

    output_box.config(state="normal")

    result = container.exec_run(cmd)
    output_box.insert(tk.END, f"$ {cmd}\n{result.output.decode()}\n")
    output_box.see(tk.END)  # scroll to bottom

    output_box.config(state="disabled")

def do_ping(container_name, ipaddr_entry, output_box, win, ping_btn):
    if not container_name: 
        return
    ipaddr = ipaddr_entry.get()
    if not ipaddr:
        messagebox.showwarning("Input Error", "Please enter a valid IP address.", parent=win)
        return
    
    try:
        ipaddress.ip_address(ipaddr)
    except ValueError:
        messagebox.showerror(
            "Error", f'"{ipaddr}" is not a valid IP.n\nPlease, enter a correct one.',
            parent=win
        )
        return

    cmd = f"ping -c 4 {ipaddr}"
    container = client.containers.get(container_name)
    ping_btn.config(text="Pinging...", state="disabled")

    def run_ping():
        result = container.exec_run(cmd)
        win.after(0, lambda: on_ping_done(result))

    # New Thread to stop container
    threading.Thread(target=run_ping).start()

    def on_ping_done(result):
        # Show result
        output_box.config(state="normal")
        output_box.insert(tk.END, f"$ {cmd}\n{result.output.decode()}\n")
        output_box.see(tk.END)  # scroll to bottom
        output_box.config(state="disabled")
        ping_btn.config(text="Ping", state="normal")

def clear_focus(event):
    widget_with_focus = root.focus_get()
    event.widget.focus_set()
    widget_with_focus.selection_clear()

# handle recent projects
def load_recent_projects():
    if RECENT_PROJECTS_FILE.exists():
        try:
            with open(RECENT_PROJECTS_FILE, "r") as f:
                data = json.load(f)
                return data.get("recent_projects", [])
        except Exception:
            return []
    return []

def save_recent_project(path):
    BASE_DIR.mkdir(exist_ok=True)
    projects = load_recent_projects()

    # normalize path and add to top of list
    path = str(Path(path).resolve())
    projects = [p for p in projects if p != path]
    projects.insert(0, path)

    with open(RECENT_PROJECTS_FILE, "w") as f:
        json.dump({"recent_projects": projects[:10]}, f, indent=2)

def choose_project_popup():
    popup = tk.Toplevel(root)
    popup.title("Select Docker Compose project")
    popup.geometry("600x500")
    popup.wm_minsize(600, 500)

    ttk.Label(popup, text="Recent projects:", font=("Arial", 16)).pack(pady=10)
    projects = load_recent_projects()
    listbox = tk.Listbox(popup, font=("Arial", 13), selectmode=tk.SINGLE)
    listbox.pack(fill=tk.BOTH, padx=20, pady=10)
    
    for p in projects:
        listbox.insert(tk.END, p)

    selected_path = {"path": None}
    
    def select_existing():
        sel = listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Select a project from the list above or browse a new one.", parent=popup)
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
        popup.destroy()
        root.destroy()
        sys.exit(0)

    ttk.Button(popup, 
               text="Open selected project", 
               image= open_icon,
               compound=tk.LEFT,
               command=select_existing
            ).pack(pady=5)
    
    ttk.Button(popup, 
               text="Browse new file", 
               image= folder_icon,
               compound=tk.LEFT,
               command=browse_new
            ).pack(pady=5)
    
    ttk.Button(popup, 
               text="Exit", 
               image= stop_icon,
               compound=tk.LEFT,
               command=exit_popup,
               width=4
            ).pack(pady=5)

    popup.grab_set()
    popup.update()
    root.wait_window(popup)

    return selected_path["path"]

def on_main_window_close():
    # 
    if lock_manager.has_active_locks():
        messagebox.showwarning(
            "Operation running",
            "Wait for the operations to finish before closing",
            parent=root
        )
    else:
        root.destroy()

# GUI
root = tk.Tk()
root.withdraw()  # hide main window until project is selected

#Icons
running_icon = load_image(IMAGE_DIR / "running.png")
exited_icon = load_image(IMAGE_DIR / "exited.png")
other_icon = load_image(IMAGE_DIR / "other.png")
refresh_icon = load_image(IMAGE_DIR / "refresh.png")
start_icon = load_image(IMAGE_DIR / "start.png")
stop_icon = load_image(IMAGE_DIR / "stop.png")
folder_icon = load_image(IMAGE_DIR / "folder.png")
open_icon = load_image(IMAGE_DIR / "open.png")
exit_icon = load_image(IMAGE_DIR / "exit.png")

compose_file = choose_project_popup()

if not compose_file:
    exit(0)

compose_file = Path(compose_file)
project_name = compose_file.parent.name.lower()
client = docker.from_env()

if exec_compose(compose_file) is True:
    save_recent_project(compose_file)

sv_ttk.set_theme("dark")
root.title("DTN & Emulator Control GUI")


# Treeview for containers
tree = ttk.Treeview(root, columns=("Status",), show="tree headings")
tree.bind("<Double-1>", on_tree_select)  # double click for new window
tree.bind("<Button-3>", show_context_menu)  # right click for menu
root.bind("<FocusOut>", close_context_menu)
root.bind("<Button-1>", close_context_menu)
root.option_add("*TCombobox*Listbox.font", ("Arial", 12))
style = ttk.Style()
style.configure("Treeview", font=("Arial", 20)) 
style.configure("Treeview", rowheight=50)
style.configure("Treeview.Heading", font=("Arial", 18), padding=5)

tree.heading("#0", text="Container")
tree.heading("Status", text="Status")
tree.column("Status", anchor="center")
tree.pack()

buttons_frame = tk.Frame(root)
buttons_frame.pack(pady=10)

refresh_btn = ttk.Button(
    buttons_frame,
    text="Refresh",
    style="Normal.TButton",
    image=refresh_icon,
    compound=tk.LEFT,
    command=refresh_containers
)
refresh_btn.pack()

start_button = ttk.Button(
    buttons_frame,
    text="Start All",
    style="Normal.TButton",
    image=start_icon,
    compound=tk.LEFT,
    command=start_all_containers
)
start_button.pack(side=tk.LEFT, padx=10, pady= 5)

stop_button = ttk.Button(
    buttons_frame,
    text="Stop All", 
    style="Normal.TButton",
    image=stop_icon,
    compound=tk.LEFT,
    command=stop_all_containers
)
stop_button.pack(side=tk.LEFT, padx=10)


# single drop-down menu
context_menu = tk.Menu(root, tearoff=0)

# call function when user press "X" to close main window
root.protocol("WM_DELETE_WINDOW", on_main_window_close)

refresh_containers()
root.deiconify()
root.mainloop()