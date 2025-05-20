from abc import ABC, abstractmethod
import requests
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.jb_llm_logger import logger
from llm_vm_manager.ssh_base import SSHManager
from llm_vm_manager.ssh_client import SSHClient


class LLMVirtualMachineManager(ABC):
    def __init__(self, configuration: ConfigLoader):
        self.llm_vm_manager_config = configuration
        self.ssh_manager = SSHManager()
        self.ssh_client = SSHClient()

    @abstractmethod
    def create_instance(self, name: str):
        pass

    @abstractmethod
    def start_instance(self, name: str):
        pass

    @abstractmethod
    def stop_instance(self, name: str):
        pass

    @abstractmethod
    def delete_instance(self, name: str):
        pass

    @abstractmethod
    def list_instances(self):
        pass

    def get_my_ip(self):
        logger.debug("Getting my IP address...")
        my_ip_url = self.llm_vm_manager_config.get("my_ip_url")
        my_ip = requests.get(my_ip_url).text
        logger.debug(my_ip)
        return my_ip
