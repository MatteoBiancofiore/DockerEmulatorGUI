# gui/container_window.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import ipaddress

# Import of our modules
from core import docker_ops, config_manager

class NodeWindow(tk.Toplevel):
    
    # Constructor
    def __init__(self, parent, controller, container_name):
        super().__init__(parent)
        
        self.controller = controller
        self.container_name = container_name
        
        self.config_status = [True]
        self.current_iface_tracker = [None]
        
        # Load configuration using config_manager
        self.all_container_configs = config_manager.load_configs(
            self.controller.project_name, 
            self.container_name
        )

        self.geometry("1150x700")
        self.wm_minsize(1150, 350)
        self.title(f"{self.container_name}")
        self.bind("<Button-1>", self._clear_focus)
        
        # Bind X button to close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self.force_close = self._force_close

        # Build UI
        self._build_ui()

    # 2. Widget creation
    def _build_ui(self):
        title_frame = tk.Frame(self)
        ttk.Button(
            title_frame, text="Close",  
            command=self._on_close,
            style="Accent.TButton"
        ).pack(padx=10, side="right")
        tk.Label(title_frame, text=f"Container: {self.container_name}", font=("Arial", 20, "bold")).pack(padx=10, side="left")
        title_frame.pack(fill="x", padx=5, pady=5)

        subtitle_frame = tk.Frame(self)
        tk.Label(subtitle_frame, text="Control window for channel emulator", font=("Arial", 16)).pack(padx=10, side="left")
        subtitle_frame.pack(fill="x",padx=5, pady=5)

        #  -- tc section --
        tc_frame = ttk.LabelFrame(self, text=" Traffic Control ", padding=(10,10))
        tc_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(tc_frame, text="Interface:", font=("Arial", 13)).grid(row=1, column=0, padx=10, pady=5)
        
        try:
            interfaces = docker_ops.get_container_interfaces(self.controller.client, self.container_name)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot find interfaces for {self.container_name}.\n{e}", parent=self)
            interfaces = []
            
        self.interface_var = tk.StringVar()
        interface_combo = ttk.Combobox(tc_frame, textvariable=self.interface_var, values=interfaces, state="readonly", width=20, font=("Arial", 12))
        
        if interfaces:
            saved_iface_name = None
            existing_saved_ifaces = [iface for iface in self.all_container_configs.keys() if iface in [i.split(" - ")[0] for i in interfaces]]
            if existing_saved_ifaces: saved_iface_name = existing_saved_ifaces[0]
            target_index = 0
            if saved_iface_name:
                for i, iface_string in enumerate(interfaces):
                    if iface_string.startswith(saved_iface_name):
                        target_index = i
                        break 
            interface_combo.current(target_index)
            self.current_iface_tracker[0] = interfaces[target_index].split(" - ")[0]

        interface_combo.grid(row=2, column=0, padx=10)
        interface_combo.bind("<<ComboboxSelected>>", self._update_spinboxes_for_interface)

        tk.Label(tc_frame, text="Delay (ms):", font=("Arial", 13)).grid(row=1, column=3, padx=10, pady=5)
        self.delay_spinbox = ttk.Spinbox(tc_frame, from_=0, to=999999, increment=10, font=("Arial", 12), width=5)
        self.delay_spinbox.set("20")
        self.delay_spinbox.grid(row=2, column=3, padx=10)

        tk.Label(tc_frame, text="Loss (%):", font=("Arial", 13)).grid(row=1, column=4, padx=10, pady=5)
        self.loss_spinbox = ttk.Spinbox(tc_frame, from_=0, to=100, increment=5, font=("Arial", 12), width=5)
        self.loss_spinbox.set("0")
        self.loss_spinbox.grid(row=2, column=4, padx=10)

        tk.Label(tc_frame, text="Bandwidth (Mbit/s):", font=("Arial", 13)).grid(row=1, column=5, padx=10, pady=5)
        self.band_spinbox = ttk.Spinbox(tc_frame, from_=0.1, to=100.0, increment=0.1, font=("Arial", 12), format="%.1f", width=10)
        self.band_spinbox.set("1.0")
        self.band_spinbox.grid(row=2, column=5, padx=10)

        tk.Label(tc_frame, text="Limit (packets):", font=("Arial", 13)).grid(row=1, column=6, padx=10, pady=5)
        self.limit_spinbox = ttk.Spinbox(tc_frame, from_=0, to=100.0, increment=10, font=("Arial", 12), width=5)
        self.limit_spinbox.set("10")
        self.limit_spinbox.grid(row=2, column=6, padx=10)

        apply_btn = ttk.Button(tc_frame, text="Apply",
            command=self.do_tc, # call for do_tc methon of self(this class)
            style="Accent.TButton")
        apply_btn.grid(row=2, column=7, padx=10, pady=5)

        self.save_btn = ttk.Button(tc_frame, text="Save configs", width=12, style="Accent.TButton",
            command=self._save_configs_action)
        self.save_btn.grid(row=2, column=8, padx=10, pady=10)
        
        if interfaces:
            self._update_spinboxes_for_interface()
            self.config_status[0] = True
            self.save_btn.config(text="Save configs")
        
        self.delay_spinbox.bind("<KeyRelease>", self._set_config_dirty)
        self.delay_spinbox.bind("<ButtonRelease>", self._set_config_dirty) 
        self.loss_spinbox.bind("<KeyRelease>", self._set_config_dirty)
        self.loss_spinbox.bind("<ButtonRelease>", self._set_config_dirty)
        self.band_spinbox.bind("<KeyRelease>", self._set_config_dirty)
        self.band_spinbox.bind("<ButtonRelease>", self._set_config_dirty)
        self.limit_spinbox.bind("<KeyRelease>", self._set_config_dirty)
        self.limit_spinbox.bind("<ButtonRelease>", self._set_config_dirty)

        #  --  Ping section  --
        ping_frame = ttk.LabelFrame(self, text=" Network Test ", padding=(10,10))
        ping_frame.pack(pady=10)
        tk.Label(ping_frame, text="IP to ping:", font=("Arial", 13)).grid(row=0, column=0, padx=10, pady=5)
        self.ipaddr_entry = tk.Entry(ping_frame, width=16 , font=("Arial", 13), highlightthickness=1, highlightbackground="#888888", highlightcolor="#0078D7")
        self.ipaddr_entry.insert(0, "") 
        self.ipaddr_entry.grid(row=1, column=0, padx=10)
        
        self.ping_btn = ttk.Button(ping_frame, text="Ping", style="Accent.TButton",
            command=self.do_ping)
        self.ping_btn.grid(row=1, column=2, padx=10, pady=5)
        
        # -- Console section --
        self.toggle_btn = ttk.Button(self, text="Hide Console", command=self._toggle_console)
        self.toggle_btn.pack()
        self.console_frame = tk.Frame(self)
        self.console_frame.pack(expand=True, fill="both", padx=10, pady=5)
        label_frame = tk.Frame(self.console_frame)
        label_frame.pack(fill="x", padx=10, pady=5)
        output_label = tk.Label(label_frame, text="Output:", font=("Arial", 12))
        output_label.pack(side="left")
        clear_btn = ttk.Button(label_frame, text="Clear console", command=self.clear_console)
        clear_btn.pack(side="right")
        
        self.output_box = scrolledtext.ScrolledText(self.console_frame, font=("Courier New", 11))
        self.output_box.pack(expand=True, fill="both")
        self.output_box.config(state="disabled")

        self.show_console = False
        self._toggle_console()

    # Logic to handle edits on parameters
    
    def _update_spinboxes_for_interface(self, event=None):
        new_iface_name = self.interface_var.get().split(" - ")[0]
        old_iface_name = self.current_iface_tracker[0]
        
        if old_iface_name and old_iface_name != new_iface_name:
            current_values_in_spinbox = {
                "delay": self.delay_spinbox.get(), "loss": self.loss_spinbox.get(),
                "band": self.band_spinbox.get(), "limit": self.limit_spinbox.get()
            }
            stored_values_for_old_iface = self.all_container_configs.get(old_iface_name, {
                "delay": "20", "loss": "0", "band": "1.0", "limit": "10"
            })
            if current_values_in_spinbox != stored_values_for_old_iface:
                self.all_container_configs[old_iface_name] = current_values_in_spinbox
                self._set_config_dirty()
        
        iface_config = self.all_container_configs.get(new_iface_name)
        if iface_config:
            self.delay_spinbox.set(iface_config.get("delay", "20"))
            self.loss_spinbox.set(iface_config.get("loss", "0"))
            self.band_spinbox.set(iface_config.get("band", "1.0"))
            self.limit_spinbox.set(iface_config.get("limit", "10"))
        else: 
            self.delay_spinbox.set("20")
            self.loss_spinbox.set("0")
            self.band_spinbox.set("1.0")
            self.limit_spinbox.set("10")
        self.current_iface_tracker[0] = new_iface_name

    def _on_close(self):
        if self.config_status[0] == False:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes that will be lost.\nAre you sure you want to close?", parent=self):
                return
        
        # remove this window from window tracker
        del self.controller.open_windows[self.container_name]
        self.destroy()

    def _force_close(self):
        self.config_status[0] = True 
        self._on_close() 

    def _set_config_dirty(self, *args):
        self.config_status[0] = False
        try:
            if self.save_btn.winfo_exists():
                self.save_btn.config(text="Save configs")
        except (tk.TclError, NameError):
            pass 

    def _save_configs_action(self):
        # Call core_function
        config_manager.save_configs(
            self.controller.project_name,
            self.container_name, 
            self.interface_var.get(), 
            self.delay_spinbox, 
            self.loss_spinbox, 
            self.band_spinbox, 
            self.limit_spinbox, 
            self, # win is now self
            self.config_status,
            self.save_btn,
            self.all_container_configs
        )

    def _toggle_console(self):
        self.show_console = not self.show_console
        if self.show_console:
            self.console_frame.pack(expand=True, fill="both", padx=10, pady=5)
            self.toggle_btn.config(text="Hide Console")
            self.geometry("1150x700")
        else:
            self.console_frame.pack_forget()
            self.toggle_btn.config(text="Show Console")
            self.geometry("1150x430")

    def _clear_focus(self, event):
        try:
            widget_with_focus = self.focus_get()
            event.widget.focus_set()
            widget_with_focus.selection_clear()
        except KeyError:
            pass
    
    def clear_console(self):
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)
        self.output_box.config(state="disabled")

    def do_tc(self):
        delay = self.delay_spinbox.get()
        loss = self.loss_spinbox.get()
        bandwidth = self.band_spinbox.get()
        limit = self.limit_spinbox.get()
        flag = True
        
        if not delay.isdigit() or int(delay) < 0:   
            messagebox.showwarning("Input Error", "Delay must be a non-negative integer.", parent=self)
            flag = False
        
        if not loss.isdigit() or int(loss) < 0 or int(loss) > 100:  
            messagebox.showwarning("Input Error", "Loss must be an integer between 0 and 100.", parent=self)
            flag = False

        try:
            bandwidth_value = float(bandwidth) 

            if bandwidth_value < 0:
                messagebox.showwarning("Input Error", "Bandwidth must be a non-negative number.", parent=self)
                flag = False
            
        except ValueError:
            messagebox.showwarning("Input Error", "Bandwidth must be a valid number.", parent=self)
            flag = False

        if not limit.isdigit() or int(limit) <= 0:  
            messagebox.showwarning("Input Error", "Limit must be a non negative integer.", parent=self)
            flag = False
        
        if flag == False: 
            return
        
        eth = self.interface_var.get().split(" - ")[0]
        cmd_string_for_output = f"tc qdisc replace dev {eth} root netem delay {delay}ms loss {loss}% rate {bandwidth}Mbit limit {limit}"

        def do_tc_worker():
            try:
                result = docker_ops.apply_tc_rules(
                    self.controller.client,
                    self.container_name, 
                    eth, delay, loss, bandwidth, limit
                )
                
                self.after(0, _on_tc_done, cmd_string_for_output, result.output.decode())
            except Exception as e:
                self.after(0, _on_tc_error, str(e))
        
        def _on_tc_done(cmd_text, output_text):
            self.output_box.config(state="normal")
            self.output_box.insert(tk.END, f"$ {cmd_text}\n{output_text}\n")
            self.output_box.see(tk.END)
            self.output_box.config(state="disabled")
        
        def _on_tc_error(error_message):
            messagebox.showerror("TC Error", f"Tc rules could not be applied:\n{error_message}", parent=self)

        threading.Thread(target=do_tc_worker, daemon=True).start()

    def do_ping(self):
        ipaddr = self.ipaddr_entry.get()
        if not ipaddr:
            messagebox.showwarning("Input Error", "Please enter a valid IP address.", parent=self)
            return
        try:
            ipaddress.ip_address(ipaddr)
        except ValueError:
            messagebox.showerror("Error", f'"{ipaddr}" is not a valid IP.', parent=self)
            return

        self.ping_btn.config(text="Pinging...", state="disabled")
        cmd_string_for_output = f"ping -c 4 {ipaddr}"

        def do_ping_worker():
            try:
                result = docker_ops.run_container_ping(
                    self.controller.client,
                    self.container_name, 
                    ipaddr
                )
                self.after(0, _on_ping_done, cmd_string_for_output, result.output.decode())
            except Exception as e:
                self.after(0, _on_ping_error, str(e))
        
        def _on_ping_done(cmd_text, output_text):
            self.output_box.config(state="normal")
            self.output_box.insert(tk.END, f"$ {cmd_text}\n{output_text}\n")
            self.output_box.see(tk.END)
            self.output_box.config(state="disabled")
            self.ping_btn.config(text="Ping", state="normal")
        
        def _on_ping_error(error_message):
            messagebox.showerror("Errore Ping", f"Impossibile eseguire il ping:\n{error_message}", parent=self)
            self.ping_btn.config(text="Ping", state="normal")

        threading.Thread(target=do_ping_worker, daemon=True).start()