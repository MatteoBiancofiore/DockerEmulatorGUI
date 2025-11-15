r"""
\file core/docker_ops.py

\brief Docker operations utility functions for DTG

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
import docker
from typing import List

from docker.client import DockerClient
from docker.models.containers import Container

def get_container(client: DockerClient, container_id: str) -> Container:
    try:
        return client.containers.get(container_id)
    except docker.errors.NotFound:
        raise
    except Exception as e:
        raise Exception(f"Error while accessing the container: {e}")    

def get_project_containers(client: DockerClient, project_name: str) -> List[Container]:
    r"""
    \brief Utility function to get all containers belonging to the specified project 
    
    \param client (DockerClient) Docker Client instance

    \param project_name (str) The name of the project

    \return (list) List of containers of the specified project

    \throws Exception If no containers are found
    """
    try:
        containers = client.containers.list(all=True, filters={"label":f"com.docker.compose.project={project_name}"})   
        return sorted(containers, key=lambda c: c.name)
    except Exception as e:
        raise Exception(f"Can't get project containers: {e}")
    
def get_container_interfaces(client: DockerClient, container_id: str) -> List[str]:
    r"""
    \brief Utility function to get interfaces names and associated ips of the specified container

    This function executes commands inside the container 
    to list network interfaces and retrieve their IP addresses.
    
    \param client (DockerClient) Docker Client instance

    \param container_id (str) The id of the container

    \return (list) List of {interface_name - ip} entries
    """

    container = client.containers.get(container_id)
    result = container.exec_run("ls /sys/class/net")
    
    if result.exit_code != 0:
        return []
    
    interfaces = result.output.decode('utf-8').strip().split('\n')
    interfaces =  [eth for eth in interfaces if eth and eth.startswith("eth")]
    
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

def start_container_by_id(client: DockerClient, container_id: str):
    r"""
    \brief Utility function to start a container by its id

    This fuction uses the Docker SDK for Python to interact with the Docker daemon
    and start a certain container. It is invoked by the GUI when the user requests a container start.
    
    \param client (DockerClient) Docker Client instance

    \param container_id (str) The id of the container to start

    \return (None)
    """

    container = get_container(client, container_id)

    if container.status != "running":
        container.start()
        container.reload()

def stop_container_by_id(client: DockerClient, container_id: str):
    r"""
    \brief Utility function to stop a container by its id

    This fuction uses the Docker SDK for Python to interact with the Docker daemon
    and stop a certain container. It is invoked by the GUI when the user requests a container stop.
    
    \param client (DockerClient) Docker Client instance

    \param container_id (str) The id of the container to stop

    \return (None)
    """
  
    container = get_container(client, container_id)
    if container.status != "exited":
        container.stop()
        container.reload()

def restart_container_by_id(client: DockerClient, container_id: str):
    r"""
    \brief Utility function to restart a container by its id

    This fuction uses the Docker SDK for Python to interact with the Docker daemon
    and restart a certain container. It is invoked by the GUI when the user requests a container restart.
    
    \param client (DockerClient) Docker Client instance

    \param container_id (str) The id of the container to restart

    \return (None)
    """

    container = get_container(client, container_id)
    container.restart()
    container.reload()

def apply_tc_rules(client: DockerClient, container_id: str, eth: str, delay: str, loss: str, band: str, limit: str):
    r"""
    \brief Utility function to execute tc command inside a container to apply network emulation rules

    This fuction uses the Docker SDK for Python to interact with the Docker daemon
    and apply tc command to a certain container. 
    It is invoked by the GUI when the user requests a container restart.

    \param client (DockerClient) Docker Client instance

    \param container_id_ (str) The id of the container

    \param eth (str) The network interface name

    \param delay (str) The delay value in ms

    \param loss (str) The packet loss percentage

    \param band (str) The bandwidth limit in Mbit

    \param limit (str) The queue limit in packets

    \return (Docker.models.exec.ExecResult) The result of the command execution
    """
    container = get_container(client, container_id)
    cmd = f"tc qdisc replace dev {eth} root netem delay {delay}ms loss {loss}% rate {band}Mbit limit {limit}"
    return container.exec_run(cmd)

def run_container_ping(client: DockerClient, container_id: str, ipaddr: str):
    r"""
    \brief Utility function to execute ping command inside a container to a specified IP address

    This fuction uses the Docker SDK for Python to interact with the Docker daemon
    and apply tc command to a certain container. 
    It is invoked by the GUI when the user requests a container restart.

    \param client (DockerClient) Docker Client instance

    \param container_id_ (str) The id of the container 

    \param ipaddr (str) The target IP address to ping

    \return (Docker.models.exec.ExecResult) The result of the command execution
    """
    container = get_container(client, container_id)
    cmd = f"ping -c 4 {ipaddr}"
    return container.exec_run(cmd)