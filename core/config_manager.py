r"""
\file core/config_manager.py

\brief Configuration management utility functions for DTG

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
    r"""
    \brief Utility function to load recent projects from a file

    \return (list) List of recent projects or empty list

    \throws Exception If recent projects file is corrupted
    """
    if RECENT_PROJECTS_FILE.exists():
        try:
            with open(RECENT_PROJECTS_FILE, "r") as f:
                data = json.load(f)
                return data.get("recent_projects", [])
        except Exception:
            return []
    return []


def save_recent_project(path):
    r"""
    \brief Utility function to save recent projects to a file

    \param path (str) Path of the project to save

    \return (void)
    """
    CONFIG_DIR.mkdir(exist_ok=True)
    projects = load_recent_projects()

    # normalize path and add to top of list
    path = str(Path(path).resolve())
    projects = [p for p in projects if p != path]
    projects.insert(0, path)

    with open(RECENT_PROJECTS_FILE, "w") as f:
        json.dump({"recent_projects": projects[:10]}, f, indent=2)


def load_configs(project_name, container_name):
    r"""
    \brief Utility function to laod configs for a specific container from file

    \param project_name (str) The name of the project

    \param container_name (str) The name of the container

    \return (dict) Dictionary of configurations or empty dict
    """
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
    r"""
    \brief Utility function to laod configs for a specific container to file

    It requires project name, container name and the the current spinbox values.

    \return (dict) Dictionary of configurations or empty dict
    """
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