# core/system_ops.py
import shutil, subprocess, platform, shlex

class ComposeNotFoundError(Exception):
    pass

class DockerComposeError(Exception):
    pass

class TerminalError(Exception):
    pass

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
        raise DockerComposeError(error_message)
        
    return cmd


def open_terminal(container_name: str):
   
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
                    terminal_cmd = [path, "--title", title, "-x", f"bash -c '{docker_cmd}'"]

                elif term == "gnome-terminal":
                    terminal_cmd = [path, "--wait", "--title", title, "--", "bash", "-c", docker_cmd]

                elif term in ("konsole", "xfce4-terminal", "mate-terminal"):
                    terminal_cmd = [path, "--title", title, "-e", f"bash -c '{docker_cmd}'"]

                elif term == "lxterminal":
                    terminal_cmd = [path, "-T", title, "-e", f"bash -c '{docker_cmd}'"]

                else: # fallback
                    terminal_cmd = [path, "-e", f"bash -c '{docker_cmd}'"]
                    
                
                found_term = True
                print(f"Debug: used {term} (path: {path})")
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