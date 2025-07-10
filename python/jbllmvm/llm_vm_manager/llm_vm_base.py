"""
Base module for LLM Virtual Machine Management.

This module provides an abstract base class for managing virtual machines
that run Large Language Models (LLMs). It defines the interface that all
VM manager implementations must follow and provides some common utility methods.
"""

from abc import ABC, abstractmethod
import requests
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.jb_llm_logger import logger
from llm_vm_manager.ssh_base import SSHManager
from llm_vm_manager.ssh_client import SSHClient


class LLMVirtualMachineManager(ABC):
    """
    Abstract base class for managing virtual machines that run Large Language Models.

    This class defines the interface that all VM manager implementations must follow.
    It provides abstract methods for common VM operations like creating, starting,
    stopping, and deleting instances, as well as concrete utility methods for
    working with LLMs running on those VMs.
    """

    def __init__(self, configuration: ConfigLoader) -> None:
        """
        Initialize the LLM Virtual Machine Manager.
        Args:
            configuration (ConfigLoader): Configuration object containing settings
                                         for the VM manager.
        """
        self.llm_vm_manager_config = configuration
        self.ssh_manager = SSHManager()
        self.ssh_client = SSHClient()

    @abstractmethod
    def create_instance(self, name: str) -> None:
        """
        Create a new virtual machine instance.
        Args:
            name (str): The name for the new VM instance.
        Returns:
            None
        """
        pass

    @abstractmethod
    def start_instance(self, name: str) -> None:
        """
        Start a stopped virtual machine instance.
        Args:
            name (str): The name of the VM instance to start.
        Returns:
            None
        """
        pass

    @abstractmethod
    def stop_instance(self, name: str) -> None:
        """
        Stop a running virtual machine instance.
        Args:
            name (str): The name of the VM instance to stop.
        Returns:
            None
        """
        pass

    @abstractmethod
    def delete_instance(self, name: str) -> None:
        """
        Delete a virtual machine instance.
        Args:
            name (str): The name of the VM instance to delete.
        Returns:
            None
        """
        pass

    @abstractmethod
    def list_instances(self) -> None:
        """
        List all virtual machine instances.
        This method should display information about all VM instances
        managed by this VM manager.
        Returns:
            None
        """
        pass

    def get_my_ip(self) -> str:
        """
        Get the public IP address of the current machine.

        This method uses a configured URL to retrieve the public IP address
        of the machine running this code.
        Returns:
            str: The public IP address as a string.
        """
        logger.debug("Getting my IP address...")
        my_ip_url = self.llm_vm_manager_config.get("my_ip_url")
        my_ip = requests.get(my_ip_url).text
        logger.debug(my_ip)
        return my_ip

    def check_ollama_model_available(self, llm_ip: str, llm_name: str) -> bool:
        """
        Check if a specific Ollama LLM model is available on a given IP address.
        This method queries the Ollama API on the specified IP address to check
        if the requested model is available for use.
        Args:
            llm_ip (str): The IP address where Ollama is running.
            llm_name (str): The name of the LLM model to check for.
        Returns:
            bool: True if the model is available, False otherwise.
        """
        try:
            resp = requests.get(f"http://{llm_ip}:11434/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                model_names = [m["name"] for m in models]
                if llm_name in model_names:
                    logger.info(f"Model '{llm_name}' is present in list of available models ({model_names}).")
                    return True
                else:
                    logger.warning(f"Model '{llm_name}' is not available in list of available models ({model_names}).")
                    return False
            else:
                logger.error(f"Ollama returned error: \n{resp.status_code}\n{resp.text}")
                return False
        except requests.RequestException as er_exp:
            logger.error(f"Failed to connect to Ollama at {llm_ip}: {er_exp}")
            return False
