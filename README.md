# DTG (DTN Testbed GUI)
Lightweight Python-based GUI for configuring network channel emulators
(using tc qdisc) and simplify the management of Docker containers on the host machine.
It aims to enhance **transparency** and reduce the complexity of command-line configuration.

---

## Main Features

- Start or stop containers on the host machine.
- Select a container and modify the parameters of its channel emulator using `tc qdisc` command.
- Perform connectivity tests using the integrated `ping` command.
- Open a terminal collected to the specified node, (intended for low-level management purposes only)
- Simple and intuitive interface, designed to be easy to use.

---

## File Structure

- `main.py` → main file to start the app.
- `app.py` →  brain of GUI: handle life cycle and app state
- `core/` →  core logic of the application
- `gui/` → windows displayed to user  
- `utils/` → utility tools (like OperationLock class)
- `images/` → folder containing images used by the GUI.
- `requirements.txt` → required python libraries

**Note:** All folders (and files also) must be in the same directory as main.py.

---

# DTG - Setup Guide

This guide covers the requirements and installation steps required to run DTG on Windows, macOS and Debian/Ubuntu-based systems. It is also compatible with different Linux distros.

---

## System Requirements

### 1. Docker

* Docker Engine
* Docker Compose plugin

### 2. Python

* **python3** — Python interpreter
* **python3-tk** — For the graphical environment (Tkinter)
* **python3-pip** — Tool to install Python libraries

### 3. Python Libraries

* **docker** — Communicates with Docker daemon
* **pillow** — Loads icons for GUI
* **sv_ttk** — Provides prettier themes for Tkinter

## Install Docker and Docker Compose
> **Note:** Skip this passage if you have Docker & Docker-compose installed

> **Note:** Docker Compose comes with Docker Desktop on Windows and MacOS

For this passage you can either follow the Docker_Testbeds\_guide.pdf file in

👉 [https://gitlab.com/unibo-dtn-docker-environment/DTN2hops](https://gitlab.com/unibo-dtn-docker-environment/DTN2hops)

or, otherwise, follow the official guide for Docker

👉 [https://docs.docker.com/desktop/](https://docs.docker.com/desktop/)

and Docker Compose

👉 [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)


# GUI installation

## Linux installation (Debian/Ubuntu-based)

> **Note:** Having Docker and Docker Compose installed (and running) is crucial for the GUI!

### Step 1: Install Python, tkinter, and pip 

```bash
# Update repositories' dependancies and upgrade packages
sudo apt update
sudo apt upgrade -y # -y to automatically say yes

# Install needed python packages
sudo apt install python3 python3-tk python3-pip
```

### Step 2: Install required libraries 

> **Note:** From Ubuntu 22.04 python packages are managed externally by apt, this means you have to either install them globally or create a python venv.

#### Virtual environment
```bash
# In the project's root folder (where main.py is)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Global installation
> **Note:** sv_ttk is a library for style. Its not included in apt packages and can only be installed with pip!
```bash
# global installation using apt
sudo apt install python3-docker
sudo apt install python3-pil
sudo apt install python3-pil.imagetk
pip3 install sv_ttk --break-system-packages     # this may sound scary but this just ignores the protection and install this library into system's python
```
### Step 3: Give the user the permission needed for Docker

In order to connect with Docker, the user must have the proper permissions: running the GUI with `sudo`  does not work,
because the user must be in the '`docker`' group to allow a proper connection to the Docker daemon.

```bash
# Add $USER to group docker
sudo usermod -aG docker $USER
```

`IMPORTANT` You must **reboot your pc** in order to make this change permanent.

After this, you can use docker cmds without root permissions, try:

```bash
docker ps
```

---

## Windows Installation

### Step 1: Download Python

Go to the Python official website:
👉 [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)
and download latest version, Windows Installer(64 bit)

### Step 2: Install Python, tkinter and pip should be included

1. Open `python-xx.exe`
2. `IMPORTANT`<u>Make sure to check “Add Python to PATH” during installation</u>
3. Follow displayed instructions

### Step 3: Verify Python Installation
Open PowerShell or Command Prompt and type:
```powershell
python --version
pip --version
```
You should see version numbers for both commands if the installation was successful.

If for some reason pip is not installed run:
```powershell
python -m ensurepip --upgrade
```

### Step 4: Install required libraries
```powershell
# In the project's root folder (where main.py is)

# Install requirements
pip3 install -r requirements.txt
```

## MacOS installation

### Step 1: Download and install python

Download Python 3 from 👉 [https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/)
 or install via Homebrew:
```shell
brew install python3-tk@3.14
```

Tkinter – Included with Python 3 (verify with python3 -m tkinter --version).

pip     – Included with Python 3 (verify with python3 -m pip --version).

Python Libraries – Install the required dependencies:
```shell
pip3 install -r requirements.txt
```

# Running the GUI

Once the environment is ready:
```bash
# In the project's root folder (where main.py is)
python main.py
```

### Linux
> **Note:** On Linux command is `python3`, furthermore if you created a venv during installation phase you have to activate it everytime you want to run the GUI.

```bash
# In the project's root folder (where main.py is)

# activate virtual env
source venv/bin/activate
python3 main.py

# when you are done, deactivate venv
deactivate
```

