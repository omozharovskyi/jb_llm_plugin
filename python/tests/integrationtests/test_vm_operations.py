"""
Integration tests for the VM operations module.
"""
import unittest
import sys
import os
import argparse
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from python.vm_operations import create_vm, start_vm, stop_vm, delete_vm, list_vms
from python.llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from python.llm_vm_manager.config import ConfigLoader


class TestVMOperations(unittest.TestCase):
    """
    Integration tests for the VM operations module.
    """
    def setUp(self):
        """
        Set up the test environment.
        Create mock objects and patch functions that would interact with external services.
        """
        # Create a mock config
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get.side_effect = lambda key, default=None: {
            "gcp.instance_name": "test-instance",
            "llm_model": "test-model",
            "gcp.firewall_rule_name": "test-firewall-rule",
            "gcp.firewall_tag": "test-firewall-tag"
        }.get(key, default or "test_value")
        # Create a mock VM manager
        self.mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        self.mock_vm_manager.llm_vm_manager_config = self.mock_config
        # Configure the mock VM manager methods
        self.mock_vm_manager.instance_exists.return_value = False
        self.mock_vm_manager.find_instance_zone.return_value = "test-zone"
        self.mock_vm_manager.get_instance_external_ip.return_value = "1.2.3.4"
        # Create a mock args object
        self.mock_args = MagicMock(spec=argparse.Namespace)
        self.mock_args.name = None
        self.mock_args.model = None
        # Patch the ollama_utils functions
        self.setup_ollama_patch = patch('python.vm_operations.setup_ollama', return_value=True)
        self.check_ollama_availability_patch = patch('python.vm_operations.check_ollama_availability', return_value=True)
        # Start the patches
        self.mock_setup_ollama = self.setup_ollama_patch.start()
        self.mock_check_ollama_availability = self.check_ollama_availability_patch.start()
    
    def tearDown(self):
        """
        Clean up after the test.
        Stop all patches to avoid affecting other tests.
        """
        # Stop all patches
        self.setup_ollama_patch.stop()
        self.check_ollama_availability_patch.stop()
    
    def test_create_vm_success(self):
        """
        Test creating a VM successfully.
        """
        # Call the create_vm function
        create_vm(self.mock_vm_manager, self.mock_args)
        # Verify that the expected methods were called
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.create_instance.assert_called_once_with("test-instance")
        self.mock_vm_manager.find_instance_zone.assert_called_once_with("test-instance")
        self.mock_setup_ollama.assert_called_once_with(
            self.mock_vm_manager, "test-zone", "test-instance", "test-model"
        )
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with("test-zone", "test-instance")
        self.mock_check_ollama_availability.assert_called_once_with("1.2.3.4", "test-model")
    
    def test_create_vm_already_exists(self):
        """
        Test creating a VM that already exists.
        """
        # Configure the mock VM manager to indicate that the instance already exists
        self.mock_vm_manager.instance_exists.return_value = True
        # Call the create_vm function
        create_vm(self.mock_vm_manager, self.mock_args)
        # Verify that create_instance was not called
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.create_instance.assert_not_called()
        # Verify that list_vms was called
        self.mock_vm_manager.list_instances.assert_called_once()
    
    def test_start_vm_success(self):
        """
        Test starting a VM successfully.
        """
        # Configure the mock VM manager to indicate that the instance exists
        self.mock_vm_manager.instance_exists.return_value = True
        # Call the start_vm function
        start_vm(self.mock_vm_manager, self.mock_args)
        # Verify that the expected methods were called
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.start_instance.assert_called_once_with("test-instance")
        self.mock_vm_manager.find_instance_zone.assert_called_once_with("test-instance")
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with("test-zone", "test-instance")
        self.mock_check_ollama_availability.assert_called_once_with("1.2.3.4", "test-model")
    
    def test_start_vm_not_exists(self):
        """
        Test starting a VM that doesn't exist.
        """
        # Configure the mock VM manager to indicate that the instance doesn't exist
        self.mock_vm_manager.instance_exists.return_value = False
        # Call the start_vm function
        start_vm(self.mock_vm_manager, self.mock_args)
        # Verify that start_instance was not called
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.start_instance.assert_not_called()
    
    def test_stop_vm_success(self):
        """
        Test stopping a VM successfully.
        """
        # Configure the mock VM manager to indicate that the instance exists
        self.mock_vm_manager.instance_exists.return_value = True
        # Call the stop_vm function
        stop_vm(self.mock_vm_manager, self.mock_args)
        # Verify that the expected methods were called
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.stop_instance.assert_called_once_with("test-instance")
    
    def test_stop_vm_not_exists(self):
        """
        Test stopping a VM that doesn't exist.
        """
        # Configure the mock VM manager to indicate that the instance doesn't exist
        self.mock_vm_manager.instance_exists.return_value = False
        # Call the stop_vm function
        stop_vm(self.mock_vm_manager, self.mock_args)
        # Verify that stop_instance was not called
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.stop_instance.assert_not_called()
    
    def test_delete_vm_success(self):
        """
        Test deleting a VM successfully.
        """
        # Configure the mock VM manager to indicate that the instance exists
        self.mock_vm_manager.instance_exists.return_value = True
        # Call the delete_vm function
        delete_vm(self.mock_vm_manager, self.mock_args)
        # Verify that the expected methods were called
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.delete_instance.assert_called_once_with("test-instance")
    
    def test_delete_vm_not_exists(self):
        """
        Test deleting a VM that doesn't exist.
        """
        # Configure the mock VM manager to indicate that the instance doesn't exist
        self.mock_vm_manager.instance_exists.return_value = False
        # Call the delete_vm function
        delete_vm(self.mock_vm_manager, self.mock_args)
        # Verify that delete_instance was not called
        self.mock_vm_manager.instance_exists.assert_called_once_with("test-instance")
        self.mock_vm_manager.delete_instance.assert_not_called()
    
    def test_list_vms(self):
        """
        Test listing VMs.
        """
        # Call the list_vms function
        list_vms(self.mock_vm_manager, self.mock_args)
        # Verify that list_instances was called
        self.mock_vm_manager.list_instances.assert_called_once()


if __name__ == '__main__':
    unittest.main()