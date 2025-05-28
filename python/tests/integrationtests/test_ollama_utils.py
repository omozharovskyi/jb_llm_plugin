"""
Integration tests for the Ollama utilities module.
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock, call
import requests

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from python.ollama_utils import setup_ollama, check_ollama_availability
from python.llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from python.llm_vm_manager.config import ConfigLoader


class TestOllamaUtils(unittest.TestCase):
    """
    Integration tests for the Ollama utilities module.
    """
    
    def setUp(self):
        """
        Set up the test environment.
        Create mock objects and patch functions that would interact with external services.
        """
        # Create a mock config
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get.side_effect = lambda key, default=None: {
            "ssh.ssh_secret_key": "test-ssh-secret-key",
            "ssh.user": "test-user",
            "gcp.firewall_rule_name": "test-firewall-rule",
            "gcp.firewall_tag": "test-firewall-tag"
        }.get(key, default or "test_value")
        
        # Create a mock VM manager
        self.mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        self.mock_vm_manager.llm_vm_manager_config = self.mock_config
        self.mock_vm_manager.get_instance_external_ip.return_value = "1.2.3.4"
        self.mock_vm_manager.get_my_ip.return_value = "5.6.7.8"
        
        # Create a mock SSH client
        self.mock_ssh_client = MagicMock()
        self.mock_vm_manager.ssh_client = self.mock_ssh_client
        self.mock_ssh_client.ssh_connect.return_value = True
        self.mock_ssh_client.run_ssh_commands.return_value = True
        
        # Patch the paramiko.RSAKey.from_private_key_file function
        self.rsa_key_patch = patch('paramiko.RSAKey.from_private_key_file')
        self.mock_rsa_key = self.rsa_key_patch.start()
        self.mock_rsa_key.return_value = MagicMock()
        
        # Patch the requests.get function for check_ollama_availability
        self.requests_get_patch = patch('requests.get')
        self.mock_requests_get = self.requests_get_patch.start()
        self.mock_response = MagicMock()
        self.mock_requests_get.return_value = self.mock_response
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            "models": [
                {"name": "test-model"}
            ]
        }
    
    def tearDown(self):
        """
        Clean up after the test.
        Stop all patches to avoid affecting other tests.
        """
        # Stop all patches
        self.rsa_key_patch.stop()
        self.requests_get_patch.stop()
    
    def test_setup_ollama_success(self):
        """
        Test setting up Ollama successfully.
        """
        # Call the setup_ollama function
        result = setup_ollama(self.mock_vm_manager, "test-zone", "test-instance", "test-model")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with("test-zone", "test-instance")
        self.mock_ssh_client.remove_known_host.assert_called_once_with("1.2.3.4")
        self.mock_rsa_key.assert_called_once_with("test-ssh-secret-key")
        self.mock_ssh_client.ssh_connect.assert_called_once_with("1.2.3.4", "test-user", self.mock_rsa_key.return_value)
        self.mock_ssh_client.run_ssh_commands.assert_called_once()
        self.mock_ssh_client.ssh_disconnect.assert_called_once()
        self.mock_vm_manager.get_my_ip.assert_called_once()
        self.mock_vm_manager.set_firewall_ollama_rule.assert_called_once_with(
            "5.6.7.8", "test-firewall-rule", "test-firewall-tag"
        )
        self.assertTrue(result)
    
    def test_setup_ollama_no_ip(self):
        """
        Test setting up Ollama when the VM has no IP.
        """
        # Configure the mock VM manager to return no IP
        self.mock_vm_manager.get_instance_external_ip.return_value = None
        
        # Call the setup_ollama function
        result = setup_ollama(self.mock_vm_manager, "test-zone", "test-instance", "test-model")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with("test-zone", "test-instance")
        self.mock_ssh_client.remove_known_host.assert_not_called()
        self.mock_rsa_key.assert_not_called()
        self.mock_ssh_client.ssh_connect.assert_not_called()
        self.mock_ssh_client.run_ssh_commands.assert_not_called()
        self.mock_ssh_client.ssh_disconnect.assert_not_called()
        self.mock_vm_manager.get_my_ip.assert_not_called()
        self.mock_vm_manager.set_firewall_ollama_rule.assert_not_called()
        self.assertFalse(result)
    
    def test_setup_ollama_ssh_key_error(self):
        """
        Test setting up Ollama when there's an error loading the SSH key.
        """
        # Configure the mock RSA key to raise an exception
        self.mock_rsa_key.side_effect = Exception("Test error")
        
        # Call the setup_ollama function
        result = setup_ollama(self.mock_vm_manager, "test-zone", "test-instance", "test-model")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with("test-zone", "test-instance")
        self.mock_ssh_client.remove_known_host.assert_called_once_with("1.2.3.4")
        self.mock_rsa_key.assert_called_once_with("test-ssh-secret-key")
        self.mock_ssh_client.ssh_connect.assert_not_called()
        self.mock_ssh_client.run_ssh_commands.assert_not_called()
        self.mock_ssh_client.ssh_disconnect.assert_not_called()
        self.mock_vm_manager.get_my_ip.assert_not_called()
        self.mock_vm_manager.set_firewall_ollama_rule.assert_not_called()
        self.assertFalse(result)
    
    def test_setup_ollama_ssh_connect_error(self):
        """
        Test setting up Ollama when there's an error connecting via SSH.
        """
        # Configure the mock SSH client to fail to connect
        self.mock_ssh_client.ssh_connect.return_value = False
        
        # Call the setup_ollama function
        result = setup_ollama(self.mock_vm_manager, "test-zone", "test-instance", "test-model")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with("test-zone", "test-instance")
        self.mock_ssh_client.remove_known_host.assert_called_once_with("1.2.3.4")
        self.mock_rsa_key.assert_called_once_with("test-ssh-secret-key")
        self.mock_ssh_client.ssh_connect.assert_called_once_with("1.2.3.4", "test-user", self.mock_rsa_key.return_value)
        self.mock_ssh_client.run_ssh_commands.assert_not_called()
        self.mock_ssh_client.ssh_disconnect.assert_not_called()
        self.mock_vm_manager.get_my_ip.assert_not_called()
        self.mock_vm_manager.set_firewall_ollama_rule.assert_not_called()
        self.assertFalse(result)
    
    def test_setup_ollama_run_commands_error(self):
        """
        Test setting up Ollama when there's an error running commands.
        """
        # Configure the mock SSH client to fail to run commands
        self.mock_ssh_client.run_ssh_commands.return_value = False
        
        # Call the setup_ollama function
        result = setup_ollama(self.mock_vm_manager, "test-zone", "test-instance", "test-model")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with("test-zone", "test-instance")
        self.mock_ssh_client.remove_known_host.assert_called_once_with("1.2.3.4")
        self.mock_rsa_key.assert_called_once_with("test-ssh-secret-key")
        self.mock_ssh_client.ssh_connect.assert_called_once_with("1.2.3.4", "test-user", self.mock_rsa_key.return_value)
        self.mock_ssh_client.run_ssh_commands.assert_called_once()
        self.mock_ssh_client.ssh_disconnect.assert_called_once()
        self.mock_vm_manager.get_my_ip.assert_not_called()
        self.mock_vm_manager.set_firewall_ollama_rule.assert_not_called()
        self.assertFalse(result)
    
    def test_check_ollama_availability_success(self):
        """
        Test checking Ollama availability successfully.
        """
        # Call the check_ollama_availability function
        result = check_ollama_availability("1.2.3.4", "test-model")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_requests_get.assert_called_once_with("http://1.2.3.4:11434/api/tags", timeout=5)
        self.mock_response.json.assert_called_once()
        self.assertTrue(result)
    
    def test_check_ollama_availability_error_status(self):
        """
        Test checking Ollama availability when the API returns an error status.
        """
        # Configure the mock response to return an error status
        self.mock_response.status_code = 500
        
        # Call the check_ollama_availability function
        result = check_ollama_availability("1.2.3.4", "test-model")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_requests_get.assert_called_once_with("http://1.2.3.4:11434/api/tags", timeout=5)
        self.mock_response.json.assert_not_called()
        self.assertFalse(result)
    
    def test_check_ollama_availability_model_not_found(self):
        """
        Test checking Ollama availability when the model is not found.
        """
        # Configure the mock response to return a different model
        self.mock_response.json.return_value = {
            "models": [
                {"name": "different-model"}
            ]
        }
        
        # Call the check_ollama_availability function
        result = check_ollama_availability("1.2.3.4", "test-model")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_requests_get.assert_called_once_with("http://1.2.3.4:11434/api/tags", timeout=5)
        self.mock_response.json.assert_called_once()
        self.assertFalse(result)
    
    def test_check_ollama_availability_connection_error(self):
        """
        Test checking Ollama availability when there's a connection error.
        """
        # Configure the mock requests.get to raise an exception
        self.mock_requests_get.side_effect = requests.RequestException("Test error")

        # Call the check_ollama_availability function
        result = check_ollama_availability("1.2.3.4", "test-model")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_requests_get.assert_called_once_with("http://1.2.3.4:11434/api/tags", timeout=5)
        self.mock_response.json.assert_not_called()
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()