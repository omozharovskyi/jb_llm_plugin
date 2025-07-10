import paramiko
import requests
from typing import Optional, Any, Dict, List, Union, Tuple
from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from llm_vm_manager.jb_llm_logger import logger
import time

def setup_ollama(vm_manager: GCPVirtualMachineManager, zone: str, instance_name: str, llm_model: str) -> bool:
    """
    Set up Ollama on the VM and pull the specified LLM model.
    Args:
        vm_manager: The VM manager instance
        zone: The zone where the VM is located
        instance_name: The name of the VM
        llm_model: The name of the LLM model to pull
    Returns:
        bool: True if setup was successful, False otherwise
    """
    # Get the VM's external IP
    vm_ip = vm_manager.get_instance_external_ip(zone, instance_name)
    if not vm_ip:
        logger.error(f"Could not get external IP for instance {instance_name}")
        return False
    # Remove the VM from known hosts to prevent SSH issues
    vm_manager.ssh_client.remove_known_host(vm_ip)
    # Load SSH key
    ssh_key_path = vm_manager.llm_vm_manager_config.get("ssh.ssh_secret_key")
    ssh_user = vm_manager.llm_vm_manager_config.get("ssh.user")
    try:
        key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    except Exception as ssh_expt:
        logger.error(f"Failed to load SSH key: {ssh_expt}")
        return False
    # Connect to the VM
    if not vm_manager.ssh_client.ssh_connect(vm_ip, ssh_user, key):
        logger.error(f"Failed to connect to {vm_ip}")
        return False
    # Install and configure Ollama
    commands = [
        "sudo DEBIAN_FRONTEND=noninteractive apt-get update -y && sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -yq",
        "curl https://ollama.com/install.sh | sh",
        "sudo sed -i '/^Environment/ i Environment=\"OLLAMA_HOST=0.0.0.0\"' /etc/systemd/system/ollama.service",
        "sudo systemctl daemon-reload",
        "sudo systemctl restart ollama",
        "ollama --version",
        f"ollama pull {llm_model}"
    ]
    if not vm_manager.ssh_client.run_ssh_commands(commands):
        logger.error("Failed to set up Ollama")
        vm_manager.ssh_client.ssh_disconnect()
        return False
    # Disconnect from the VM
    vm_manager.ssh_client.ssh_disconnect()
    # Set up firewall rule to allow access to Ollama API
    my_ip = vm_manager.get_my_ip()
    firewall_rule_name = vm_manager.llm_vm_manager_config.get("gcp.firewall_rule_name")
    firewall_tag = vm_manager.llm_vm_manager_config.get("gcp.firewall_tag")
    vm_manager.set_firewall_ollama_rule(my_ip, firewall_rule_name, firewall_tag)

    return True


def check_ollama_availability(vm_ip: str, llm_model: str, retries: int = 7, retry_interval: int = 30) -> bool:
    """
    Check if Ollama is available and the specified model is loaded.
    Args:
        vm_ip: The IP address of the VM
        llm_model: The name of the LLM model to check
        retries: The number of retries to attempt before giving up
        retry_interval: The interval in seconds between retries
    Returns:
        bool: True if Ollama is available and the model is loaded, False otherwise
    """
    for attempt in range(1, retries + 1):
        logger.info(f"[{attempt}/{retries}]: Checking LLM model availability via Ollama API...")
        try:
            # Check if Ollama API is accessible
            response = requests.get(f"http://{vm_ip}:11434/api/tags", timeout=5)
            if response.status_code != 200:
                logger.error(f"Ollama API returned error: {response.status_code}")
                return False
            # Check if the model is available
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            if llm_model in model_names:
                logger.info(f"Model '{llm_model}' is available")
                return True
            else:
                logger.warning(f"Model '{llm_model}' is not available. Available models: {model_names}")
                return False
        except requests.RequestException as conn_err:
            logger.error(f"Failed to connect to Ollama at {vm_ip}: {conn_err}")
        if attempt < retries:
            logger.info(f"Waiting {retry_interval} second before next attempt...")
            time.sleep(retry_interval)
        else:
            logger.error(f"All retries {retries} failed. Error upon checking model {llm_model} availability.")
    return False