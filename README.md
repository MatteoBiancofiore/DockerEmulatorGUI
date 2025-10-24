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

## Requirements

docker, docker compose plugin

python3         # interpreter for python language,
python3-tk      # for the graphic environment 
python3-pip     # a tool used to install python libraries

Libraries:
docker          # used to communicate with Docker daemon
pillow          # used to load icons
sv_ttk          # used for prettier theme

# Here's a brief guide on how to install Docker on Linux(Debian based) (from official site!)

# Add Docker's official GPG key:
```bash
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# install Docker packages 
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

# you can check its status afterward with systemctl, it should be active and running
```bash
sudo systemctl status docker    
```

### GUI installation

# Note: having Docker installed is crucial for the gui!
# update repositories' dependancies and upgrade packages, 

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-tk python3-pip

# Install (or update) required libraries

pip3 install --upgrade docker
pip3 install --upgrade pillow
pip3 install --upgrade sv_ttk
```
# In order to connect with Docker, the user must have the proper permissions.
# Running the GUI with sudo (root permissions) does not work, because the user must be in the 'docker' group to allow a proper connection to the Docker daemon.
```bash
sudo usermod -aG docker $USER 
```
# Reboot your computer in order to make it permanent

# Make sure you have the image specified in the docker file! (e.g. unibo-dtn-base-image) 
# You can either pull it or build it from a Dockerfile
```bash
docker pull registry.gitlab.com/unibo-dtn-docker-environment/dtn-image/unibo-dtn-base-image
```

# Execute
### Execute
```bash
cd /path/to/gui/folder
python3 gui.py
```

### Windows installation

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
brew install python
```

Pip – Included with Python 3 (verify with python3 -m pip --version).

Python Libraries – Install the required dependencies:
```shell
pip3 install docker Pillow sv_ttk
```

### Execute
```shell
cd /path/to/gui/folder
python3 gui.py
```
