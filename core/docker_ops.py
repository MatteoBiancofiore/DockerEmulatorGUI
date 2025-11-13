# core/docker_ops.py
import docker
from typing import List

from docker.client import DockerClient
from docker.models.containers import Container

def get_container(client: DockerClient, container_id_or_name: str) -> Container:
    try:
        return client.containers.get(container_id_or_name)
    except docker.errors.NotFound:
        raise
    except Exception as e:
        raise Exception(f"Error while accessing the container: {e}")    

def get_project_containers(client: DockerClient, project_name: str) -> List[Container]:
    try:
        containers = client.containers.list(all=True, filters={"label":f"com.docker.compose.project={project_name}"})   
        return sorted(containers, key=lambda c: c.name)
    except Exception as e:
        raise Exception(f"Can't get project containers: {e}")
    
def get_container_interfaces(client: DockerClient, container_id: str) -> List[str]:

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

    container = get_container(client, container_id)

    if container.status != "running":
        container.start()
        container.reload()

def stop_container_by_id(client: DockerClient, container_id: str):
  
    container = get_container(client, container_id)
    if container.status != "exited":
        container.stop()
        container.reload()

def restart_container_by_id(client: DockerClient, container_id: str):
    container = get_container(client, container_id)
    container.restart()
    container.reload()

def apply_tc_rules(client: DockerClient, container_id_or_name: str, eth: str, delay: str, loss: str, band: str, limit: str):
    container = get_container(client, container_id_or_name)
    cmd = f"tc qdisc replace dev {eth} root netem delay {delay}ms loss {loss}% rate {band}Mbit limit {limit}"
    return container.exec_run(cmd)

def run_container_ping(client: DockerClient, container_id_or_name: str, ipaddr: str):
    container = get_container(client, container_id_or_name)
    cmd = f"ping -c 4 {ipaddr}"
    return container.exec_run(cmd)