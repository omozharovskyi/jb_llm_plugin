from abc import ABC, abstractmethod

class LLMVirtualMachineManager(ABC):
    def __init__(self, project_id: str):
        self.project_id = project_id

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
