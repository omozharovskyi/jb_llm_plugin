import unittest
from unittest.mock import patch, MagicMock, call
import argparse
from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from llm_vm_manager.config import ConfigLoader
import vm_operations


class TestVMOperations(unittest.TestCase):
    """Test cases for VM operations functions in vm_operations.py."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock VM manager for testing
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        self.mock_vm_manager.llm_vm_manager_config = self.mock_config
        
        # Set up default return values
        self.mock_config.get.side_effect = lambda key, default=None: {
            "gcp.instance_name": "test-instance",
            "llm_model": "llama2"
        }.get(key, default)
        
        # Create mock args
        self.mock_args = MagicMock(spec=argparse.Namespace)
        self.mock_args.name = None
        self.mock_args.model = None

    @patch('vm_operations.logger')
    def test_create_vm_already_exists(self, mock_logger):
        """Test create_vm when VM already exists."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = True
        
        # Call the function
        vm_operations.create_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        mock_logger.warning.assert_called_once()
        self.mock_vm_manager.create_instance.assert_not_called()
        self.mock_vm_manager.list_instances.assert_called_once()

    @patch('vm_operations.setup_ollama')
    @patch('vm_operations.check_ollama_availability')
    @patch('vm_operations.logger')
    def test_create_vm_success(self, mock_logger, mock_check_ollama, mock_setup_ollama):
        """Test create_vm when VM is created successfully."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = False
        self.mock_vm_manager.find_instance_zone.return_value = "us-central1-a"
        self.mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"
        mock_setup_ollama.return_value = True
        mock_check_ollama.return_value = True
        
        # Call the function
        vm_operations.create_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.create_instance.assert_called_once_with("test-instance")
        self.mock_vm_manager.find_instance_zone.assert_called_once_with("test-instance")
        mock_setup_ollama.assert_called_once_with(
            self.mock_vm_manager, "us-central1-a", "test-instance", "llama2"
        )
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with(
            "us-central1-a", "test-instance"
        )
        mock_check_ollama.assert_called_once_with("192.168.1.1", "llama2")
        mock_logger.info.assert_called_with("Ollama is available at http://192.168.1.1:11434")

    @patch('vm_operations.setup_ollama')
    @patch('vm_operations.logger')
    def test_create_vm_zone_not_found(self, mock_logger, mock_setup_ollama):
        """Test create_vm when zone is not found."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = False
        self.mock_vm_manager.find_instance_zone.return_value = None
        
        # Call the function
        vm_operations.create_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.create_instance.assert_called_once_with("test-instance")
        self.mock_vm_manager.find_instance_zone.assert_called_once_with("test-instance")
        mock_logger.error.assert_called_once()
        mock_setup_ollama.assert_not_called()

    @patch('vm_operations.setup_ollama')
    @patch('vm_operations.check_ollama_availability')
    @patch('vm_operations.logger')
    def test_create_vm_ollama_not_available(self, mock_logger, mock_check_ollama, mock_setup_ollama):
        """Test create_vm when Ollama is not available."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = False
        self.mock_vm_manager.find_instance_zone.return_value = "us-central1-a"
        self.mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"
        mock_setup_ollama.return_value = True
        mock_check_ollama.return_value = False
        
        # Call the function
        vm_operations.create_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        mock_check_ollama.assert_called_once_with("192.168.1.1", "llama2")
        mock_logger.error.assert_called_once_with("Ollama is not available")

    @patch('vm_operations.logger')
    def test_start_vm_not_exists(self, mock_logger):
        """Test start_vm when VM does not exist."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = False
        
        # Call the function
        vm_operations.start_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        mock_logger.error.assert_called_once()
        self.mock_vm_manager.start_instance.assert_not_called()

    @patch('vm_operations.check_ollama_availability')
    @patch('vm_operations.logger')
    def test_start_vm_success(self, mock_logger, mock_check_ollama):
        """Test start_vm when VM is started successfully."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = True
        self.mock_vm_manager.find_instance_zone.return_value = "us-central1-a"
        self.mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"
        mock_check_ollama.return_value = True
        
        # Call the function
        vm_operations.start_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.start_instance.assert_called_once_with("test-instance")
        self.mock_vm_manager.find_instance_zone.assert_called_once_with("test-instance")
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with(
            "us-central1-a", "test-instance"
        )
        mock_check_ollama.assert_called_once_with("192.168.1.1", "llama2")
        mock_logger.info.assert_called_with("Ollama is available at http://192.168.1.1:11434")

    @patch('vm_operations.logger')
    def test_start_vm_zone_not_found(self, mock_logger):
        """Test start_vm when zone is not found."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = True
        self.mock_vm_manager.find_instance_zone.return_value = None
        
        # Call the function
        vm_operations.start_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.start_instance.assert_called_once_with("test-instance")
        self.mock_vm_manager.find_instance_zone.assert_called_once_with("test-instance")
        mock_logger.error.assert_called_once()

    @patch('vm_operations.check_ollama_availability')
    @patch('vm_operations.logger')
    def test_start_vm_ollama_not_available(self, mock_logger, mock_check_ollama):
        """Test start_vm when Ollama is not available."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = True
        self.mock_vm_manager.find_instance_zone.return_value = "us-central1-a"
        self.mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"
        mock_check_ollama.return_value = False
        
        # Call the function
        vm_operations.start_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        mock_check_ollama.assert_called_once_with("192.168.1.1", "llama2")
        mock_logger.warning.assert_called_once()

    @patch('vm_operations.logger')
    def test_stop_vm_not_exists(self, mock_logger):
        """Test stop_vm when VM does not exist."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = False
        
        # Call the function
        vm_operations.stop_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        mock_logger.error.assert_called_once()
        self.mock_vm_manager.stop_instance.assert_not_called()

    @patch('vm_operations.logger')
    def test_stop_vm_success(self, mock_logger):
        """Test stop_vm when VM is stopped successfully."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = True
        
        # Call the function
        vm_operations.stop_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.stop_instance.assert_called_once_with("test-instance")
        mock_logger.info.assert_called_once()

    @patch('vm_operations.logger')
    def test_delete_vm_not_exists(self, mock_logger):
        """Test delete_vm when VM does not exist."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = False
        
        # Call the function
        vm_operations.delete_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        mock_logger.error.assert_called_once()
        self.mock_vm_manager.delete_instance.assert_not_called()

    @patch('vm_operations.logger')
    def test_delete_vm_success(self, mock_logger):
        """Test delete_vm when VM is deleted successfully."""
        # Set up mocks
        self.mock_vm_manager.instance_exists.return_value = True
        
        # Call the function
        vm_operations.delete_vm(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.delete_instance.assert_called_once_with("test-instance")
        mock_logger.info.assert_called_once()

    @patch('vm_operations.logger')
    def test_list_vms(self, mock_logger):
        """Test list_vms."""
        # Call the function
        vm_operations.list_vms(self.mock_vm_manager, self.mock_args)
        
        # Verify the results
        self.mock_vm_manager.list_instances.assert_called_once()
        mock_logger.info.assert_called_once_with("Listing VM instances")


if __name__ == '__main__':
    unittest.main()