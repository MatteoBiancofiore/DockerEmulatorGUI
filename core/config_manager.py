# core/config_manager.py
import sys, json
from pathlib import Path

APP_NAME = "DTG"

def get_config_dir():
    if sys.platform == "win32":
        config_path = Path.home() / "AppData" / "Roaming" / APP_NAME
    elif sys.platform == "darwin":
        config_path = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        config_path = Path.home() / ".config" / APP_NAME
    
    config_path.mkdir(parents=True, exist_ok=True)
    return config_path

CONFIG_DIR = get_config_dir()
RECENT_PROJECTS_FILE = CONFIG_DIR / "recent_projects.json"

# Recent projects

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
    CONFIG_DIR.mkdir(exist_ok=True)
    projects = load_recent_projects()

    # normalize path and add to top of list
    path = str(Path(path).resolve())
    projects = [p for p in projects if p != path]
    projects.insert(0, path)

    with open(RECENT_PROJECTS_FILE, "w") as f:
        json.dump({"recent_projects": projects[:10]}, f, indent=2)


def load_configs(project_name, container_name):
    project_config_dir = CONFIG_DIR / project_name
    config_file = project_config_dir / f"{container_name}_config.json"

    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}


def save_configs(project_name, container_name, interface, delay_spinbox, loss_spinbox, band_spinbox, limit_spinbox, win, config_status, save_btn, all_container_configs):
    
    iface_name = interface.split(" - ")[0]

    all_container_configs[iface_name] = {
        "delay": delay_spinbox.get(),
        "loss": loss_spinbox.get(),
        "band": band_spinbox.get(),
        "limit": limit_spinbox.get()
    }

    project_config_dir = CONFIG_DIR / project_name
    project_config_dir.mkdir(parents=True, exist_ok=True)
    config_file = project_config_dir / f"{container_name}_config.json"

    try:
        with open(config_file, "w") as f:
            json.dump(all_container_configs, f, indent=2)
        
        config_status[0] = True
        save_btn.config(text="Saved")

        def revert_save_text():
            try:
                if save_btn.winfo_exists():
                    if config_status[0] == True: 
                        save_btn.config(text="Save configs")
            except Exception:
                pass

        win.after(2000, revert_save_text)

    except Exception:
        print(f"Error: Failed to save configs for {container_name}")