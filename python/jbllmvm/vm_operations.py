import argparse
from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from llm_vm_manager.jb_llm_logger import logger
from ollama_utils import setup_ollama, check_ollama_availability

def create_vm(vm_manager: GCPVirtualMachineManager, args: argparse.Namespace) -> None:
    """
    Create a new VM instance with the specified configuration.
    If VM already exists, show warning and list VMs.
    After VM is created, pull the specified LLM model to Ollama with autostart upon VM start.
    Args:
        vm_manager: The VM manager instance
        args: Command-line arguments
    """
    instance_name = args.name or vm_manager.llm_vm_manager_config.get("gcp.instance_name")
    llm_model = args.model or vm_manager.llm_vm_manager_config.get("llm_model")
    # Check if VM already exists
    if vm_manager.instance_exists(instance_name):
        logger.warning(f"VM instance '{instance_name}' already exists. Not creating a new one.")
        list_vms(vm_manager, args)
        return
    # Create the VM
    logger.info(f"Creating VM instance: {instance_name}")
    vm_manager.create_instance(instance_name)
    # Find the zone where the VM was created
    zone = vm_manager.find_instance_zone(instance_name)
    if not zone:
        logger.error(f"Could not find zone for instance {instance_name}")
        return
    # Set up Ollama and pull the model
    logger.info(f"Setting up Ollama and pulling model: {llm_model}")
    if setup_ollama(vm_manager, zone, instance_name, llm_model):
        # Check if Ollama is available
        vm_ip = vm_manager.get_instance_external_ip(zone, instance_name)
        if vm_ip and check_ollama_availability(vm_ip, llm_model):
            logger.info(f"Ollama is available at http://{vm_ip}:11434")
        else:
            logger.error("Ollama is not available")

def start_vm(vm_manager: GCPVirtualMachineManager, args: argparse.Namespace) -> None:
    """
    Start an existing VM instance.
    Ensures that the VM exists before attempting to start it.
    Args:
        vm_manager: The VM manager instance
        args: Command-line arguments
    """
    instance_name = args.name or vm_manager.llm_vm_manager_config.get("gcp.instance_name")
    llm_model = vm_manager.llm_vm_manager_config.get("llm_model")
    # Check if VM exists
    if not vm_manager.instance_exists(instance_name):
        logger.error(f"VM instance '{instance_name}' does not exist. Cannot start.")
        return
    logger.info(f"Starting VM instance: {instance_name}")
    vm_manager.start_instance(instance_name)
    # Find the zone where the VM is located
    zone = vm_manager.find_instance_zone(instance_name)
    if not zone:
        logger.error(f"Could not find zone for instance {instance_name}")
        return
    # Get the VM's external IP address
    vm_ip = vm_manager.get_instance_external_ip(zone, instance_name)
    if vm_ip:
        # Check if Ollama is available
        if check_ollama_availability(vm_ip, llm_model):
            logger.info(f"Ollama is available at http://{vm_ip}:11434")
        else:
            logger.warning(f"Ollama is not available at http://{vm_ip}:11434")
    else:
        logger.error(f"Could not get external IP for instance {instance_name}")

def stop_vm(vm_manager: GCPVirtualMachineManager, args: argparse.Namespace) -> None:
    """
    Stop a running VM instance.
    Ensures that the VM exists before attempting to stop it.
    Args:
        vm_manager: The VM manager instance
        args: Command-line arguments
    """
    instance_name = args.name or vm_manager.llm_vm_manager_config.get("gcp.instance_name")
    # Check if VM exists
    if not vm_manager.instance_exists(instance_name):
        logger.error(f"VM instance '{instance_name}' does not exist. Cannot stop.")
        return
    logger.info(f"Stopping VM instance: {instance_name}")
    vm_manager.stop_instance(instance_name)

def delete_vm(vm_manager: GCPVirtualMachineManager, args: argparse.Namespace) -> None:
    """
    Delete a VM instance.
    Ensures that the VM exists before attempting to delete it.
    Args:
        vm_manager: The VM manager instance
        args: Command-line arguments
    """
    instance_name = args.name or vm_manager.llm_vm_manager_config.get("gcp.instance_name")
    # Check if VM exists
    if not vm_manager.instance_exists(instance_name):
        logger.error(f"VM instance '{instance_name}' does not exist. Cannot delete.")
        return
    logger.info(f"Deleting VM instance: {instance_name}")
    vm_manager.delete_instance(instance_name)

def list_vms(vm_manager: GCPVirtualMachineManager, args: argparse.Namespace) -> None:
    """
    List all VM instances.
    Args:
        vm_manager: The VM manager instance
        args: Command-line arguments
    """
    logger.info("Listing VM instances")
    vm_manager.list_instances()
