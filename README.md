# Note: still under development !!!
# DockerEmulatorGUI
simple python gui to configure channel emulators (tc qdisc) on Docker containers asd

`gui.py` is a graphical interface designed to simplify the management of Docker containers on the host machine.  
Its purpose is to increase **transparency** and avoid complex command-line syntax.

---

## Main Features

- Start or stop containers on the host machine.
- Select a container and modify the parameters of its channel emulator using `tc qdisc` command.
- Perform connectivity tests using the integrated `ping` command.
- Open a terminal collected to the specified node. This is a feature intended for low-level management purposes only
- Simple and intuitive interface, designed to be easy to use.

---

## File Structure

- `gui.py` → main GUI file.
- `images/` → folder containing images used by the GUI.

**Note:** the `images/` folder **should be in the same directory as `gui.py`** for the images to load correctly. 
It is not strictly required, but recommended.

---

# Docker Emulator GUI - Setup Guide

This guide covers the requirements and installation steps needed to run the Docker Emulator GUI on a Debian/Ubuntu-based system.

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


## Install Docker on Linux (Debian/Ubuntu-based)
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

It should show **active (running)**.

---

## GUI installation

> **Note:** Having Docker installed is crucial for the gui!

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
sudo usermod -aG docker $USER
```

`IMPORTANT` You must **reboot** in order to make this change permanent.

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

## Windows

Download Python 3 from python.org
`IMPORTANT` Make sure to check “Add Python to PATH” during installation.
pip – Included with Python 3 (verify with python -m pip --version in command shell CMD ).

```shell
pip3 install docker Pillow sv_ttk
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
Pip     – Included with Python 3 (verify with python3 -m pip --version).

Python Libraries – Install the required dependencies:
```shell
pip3 install docker pillow sv_ttk
```

### Execute
```shell
cd /path/to/gui/folder
python3 gui.py
```
