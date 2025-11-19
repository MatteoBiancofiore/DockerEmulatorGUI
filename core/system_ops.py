r"""
\file core/system_ops.py

\brief Implementation of system operations for Docker Compose and terminal management.

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

import shutil, subprocess, platform, shlex

class ComposeNotFoundError(Exception):
    pass

class DockerComposeError(Exception):
    pass

class TerminalError(Exception):
    pass

def exec_compose(compose_file):
    r"""
    \brief Execute Docker Compose command to start the environment

    This fuction search for the version of Docker Compose installed on your system and
    execute the precise command with '-d' flag (detatched), containers will run in background.
    
    \param compose_file (Path or str) Absolute path to .yml/.yaml file.

    \return (list) List of argument of cmd (e.g. `['docker', 'compose', ...]`).

    \throws ComposeNotFoundError If Docker Compose is not installed.
    \throws DockerComposeError If errors occurs (e.g. invalid file, docker image not found)
    """
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
            
    if cmd is None:
        raise ComposeNotFoundError(
            "Docker Compose not found.\n\n"
            "This program requires either the standalone 'docker-compose' (v1) "
            "or the 'docker compose' plugin (v2) to be installed and available in your PATH."
        )

    try:
        # The 'up -d' command is idempotent; running it multiple times will not create 
        # duplicate containers but will update existing ones if the configuration changed.
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
    
    except subprocess.CalledProcessError as e:
        error_message = (
            "An error occurred while running 'docker compose up'.\n\n"
            "This could be due to one of the following:\n\n"
            "1. Docker is not currently running, make sure to start it first\n\n"
            "2. Invalid Compose File: The selected file contains syntax errors, "
            "references an invalid path, or is unreadable.\n\n"
            "3. Image Not Found: A base image specified in the file (or its Dockerfile) "
            "could not be found or pulled.\n\n"
            "Please check the file's syntax and ensure Docker is running and "
            "all required images are correct and accessible."
        )
        raise DockerComposeError(error_message)
        
    return cmd


def open_terminal(container_name: str):
    r"""
    \brief Opens a terminal attached to the specified container

    This fuction detects the host OS (via 'platform' module) and attemps
    to launch a shell session using the first terminal found on the system.   
    
    \param container_name (str) The name of the Docker container

    \return (subprocess.Popen) The process object opened, used for tracking

    \throws TerminalError If no compatible terminal emulator is found.
    """
    system_platform = platform.system()
    escaped_name = shlex.quote(container_name)
    docker_cmd = f"docker exec -it {escaped_name} bash"
    title = f"{container_name} terminal"


    if system_platform == "Windows":
        terminal_cmd = ["cmd.exe", "/c", "start", "/wait", f"{container_name} terminal",
                        "cmd.exe", "/c", f"{docker_cmd}"]
        
    elif system_platform == "Darwin": # macOS

        do_script_line = f'set newTab to do script "echo -ne \\"\\\\033]0;{container_name} terminal\\\\007\\"; {docker_cmd}"'

        script_lines = [
            'tell application "Terminal"',
            '    activate',
            f'    {do_script_line}',
            '    repeat while busy of newTab is true',
            '        delay 0.5',
            '    end repeat',
            '    try',
            '        set w to first window whose tabs contains newTab',
            '        close w',
            '    end try',
            'end tell'
        ]

        terminal_cmd = ["osascript"]
        for line in script_lines:
            terminal_cmd += ["-e", line]
        
    else: # Linux
        terminal_emulators = [
            "terminator",
            "gnome-terminal",
            "konsole",
            "xfce4-terminal",
            "mate-terminal",
            "lxterminal",
            "x-terminal-emulator"
        ]
    
        found_term = False
        for term in terminal_emulators:
            path = shutil.which(term)
            if path:
                
                if term == "terminator":
                    terminal_cmd = [path, "--title", title, "--command", f"{docker_cmd}"]

                elif term == "gnome-terminal":
                    terminal_cmd = [path, "--wait", "--title", title, "--", "bash", "-c", docker_cmd]

                elif term == "konsole":
                    terminal_cmd = [path, "-p", f"tabtitle={title}", "-e", f"bash -c '{docker_cmd}'"]

                elif term in ("xfce4-terminal", "mate-terminal"):
                    terminal_cmd = [path, "--title", title, "-e", f"bash -c '{docker_cmd}'"]

                elif term == "lxterminal":
                    terminal_cmd = [path, "-T", title, "-e", f"bash -c '{docker_cmd}'"]

                else: # fallback
                    terminal_cmd = [path, "-e", f"bash -c '{docker_cmd}'"]
                    
                found_term = True
                print(f"Debug:\nTerminal used: {term}\n Path: {path}\n Command: {terminal_cmd}")
                break
        
        if not found_term:
            raise TerminalError(
                "No compatible terminal found.\n"
                "Please install one of:\n"
                "- terminator\n- gnome-terminal\n- konsole\n- xfce4-terminal\n- mate-terminal\n- lxterminal"
            )

    try:
        proc = subprocess.Popen(terminal_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return proc
    except Exception as e:
        raise TerminalError(f"Failed to open terminal:\n{e}")