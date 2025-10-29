# Note: still under development !!!
> `gui.py` might cause crash due to its theme on some systems. If you experience crashes try to use `gui-fixed.py` which uses a lighter theme 


# DockerEmulatorGUI
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

- `gui.py` → main GUI file.
- `images/` → folder containing images used by the GUI.

**Note:** the `images/` folder **should be in the same directory as `gui.py`** for the images to load correctly. 
It is not strictly required, but recommended.

---

# Docker Emulator GUI - Setup Guide

This guide covers the requirements and installation steps for running the Docker 
Emulator GUI on Windows, macOS and Debian/Ubuntu-based systems.
It is also compatible with different Linux distributions.

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

# Linux installation (Debian/Ubuntu-based)

## Install Docker
> **Note:** Skip this passage if you have Docker & Docker-compose installed

### Step 1: Add Docker's official GPG key

```bash
sudo apt-get update
sudo apt-get install ca-certificates curl -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

### Step 2: Add the Docker repository

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

### Step 3: Install Docker packages

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```

### Step 4: Check Docker status

```bash
sudo systemctl status docker
```

It should display **active (running)**.

---

## GUI installation

> **Note:** Having Docker installed (and running) is crucial for the gui!

```bash
# Update repositories' dependancies and upgrade packages
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-tk python3-pip


# Install (or update) required libraries
pip3 install --upgrade docker
pip3 install --upgrade pillow
pip3 install --upgrade sv_ttk
```

## Permissions

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

## Running the GUI
Once the environment is ready:
```bash
# In gui.py folder
python3 gui.py
```

# Windows installation

Download Python 3 from python.org
`IMPORTANT` Make sure to check “Add Python to PATH” during installation.

Tkinter – Included with Python 3 (verify with python3 -m tkinter --version).
pip     – Included with Python 3 (verify with python -m pip --version in command shell CMD ).


Python Libraries – Install the required dependencies:
```shell
pip3 install docker pillow sv_ttk
```

### Execute
```shell
cd /path/to/gui/folder
python gui.py
```

### MacOS installation

Download Python 3 from python.org
 or install via Homebrew:
```shell
brew install python3-tk@3.14
```

Tkinter – Included with Python 3 (verify with python3 -m tkinter --version).

pip     – Included with Python 3 (verify with python3 -m pip --version).

Python Libraries – Install the required dependencies:
```shell
pip3 install docker pillow sv_ttk
```

### Execute
```shell
cd /path/to/gui/folder
python3 gui.py
```

