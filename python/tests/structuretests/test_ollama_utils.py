import unittest
from unittest.mock import patch, MagicMock, call
import paramiko
import requests
from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.ssh_client import SSHClient
import ollama_utils


class TestOllamaUtils(unittest.TestCase):
    """Test cases for Ollama utility functions in ollama_utils.py."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_ssh_client = MagicMock(spec=SSHClient)
        self.mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        self.mock_vm_manager.llm_vm_manager_config = self.mock_config
        self.mock_vm_manager.ssh_client = self.mock_ssh_client

        # Set up default return values
        self.mock_config.get.side_effect = lambda key, default=None: {
            "ssh.ssh_secret_key": "/path/to/ssh_key",
            "ssh.user": "testuser",
            "gcp.firewall_rule_name": "test-firewall-rule",
            "gcp.firewall_tag": "test-firewall-tag"
        }.get(key, default)

        # Test parameters
        self.test_zone = "us-central1-a"
        self.test_instance_name = "test-instance"
        self.test_llm_model = "llama2"
        self.test_vm_ip = "192.168.1.1"

    def tearDown(self):
        """Clean up after tests."""
        # Ensure SSH client is disconnected
        if hasattr(self, 'mock_ssh_client') and self.mock_ssh_client:
            if self.mock_ssh_client.ssh_disconnect.called:
                self.mock_ssh_client.ssh_disconnect.assert_called_with()
            else:
                self.mock_ssh_client.ssh_disconnect()

    @patch('paramiko.RSAKey.from_private_key_file')
    @patch('ollama_utils.logger')
    def test_setup_ollama_no_ip(self, mock_logger, mock_rsa_key):
        """Test setup_ollama when VM IP cannot be obtained."""
        # Set up mocks
        self.mock_vm_manager.get_instance_external_ip.return_value = None

        # Call the function
        result = ollama_utils.setup_ollama(
            self.mock_vm_manager, self.test_zone, self.test_instance_name, self.test_llm_model
        )

        # Verify the results
        self.assertFalse(result)
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with(
            self.test_zone, self.test_instance_name
        )
        mock_logger.error.assert_called_once()
        self.mock_ssh_client.remove_known_host.assert_not_called()
        mock_rsa_key.assert_not_called()

    @patch('paramiko.RSAKey.from_private_key_file')
    @patch('ollama_utils.logger')
    def test_setup_ollama_ssh_key_error(self, mock_logger, mock_rsa_key):
        """Test setup_ollama when SSH key cannot be loaded."""
        # Set up mocks
        self.mock_vm_manager.get_instance_external_ip.return_value = self.test_vm_ip
        mock_rsa_key.side_effect = Exception("SSH key error")

        # Call the function
        result = ollama_utils.setup_ollama(
            self.mock_vm_manager, self.test_zone, self.test_instance_name, self.test_llm_model
        )

        # Verify the results
        self.assertFalse(result)
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with(
            self.test_zone, self.test_instance_name
        )
        self.mock_ssh_client.remove_known_host.assert_called_once_with(self.test_vm_ip)
        mock_rsa_key.assert_called_once_with("/path/to/ssh_key")
        mock_logger.error.assert_called_once()
        self.mock_ssh_client.ssh_connect.assert_not_called()

    @patch('paramiko.RSAKey.from_private_key_file')
    @patch('ollama_utils.logger')
    def test_setup_ollama_ssh_connect_failure(self, mock_logger, mock_rsa_key):
        """Test setup_ollama when SSH connection fails."""
        # Set up mocks
        self.mock_vm_manager.get_instance_external_ip.return_value = self.test_vm_ip
        mock_key = MagicMock(spec=paramiko.PKey)
        mock_rsa_key.return_value = mock_key
        self.mock_ssh_client.ssh_connect.return_value = False

        # Call the function
        result = ollama_utils.setup_ollama(
            self.mock_vm_manager, self.test_zone, self.test_instance_name, self.test_llm_model
        )

        # Verify the results
        self.assertFalse(result)
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with(
            self.test_zone, self.test_instance_name
        )
        self.mock_ssh_client.remove_known_host.assert_called_once_with(self.test_vm_ip)
        mock_rsa_key.assert_called_once_with("/path/to/ssh_key")
        self.mock_ssh_client.ssh_connect.assert_called_once_with(
            self.test_vm_ip, "testuser", mock_key
        )
        mock_logger.error.assert_called_once()
        self.mock_ssh_client.run_ssh_commands.assert_not_called()

    @patch('paramiko.RSAKey.from_private_key_file')
    @patch('ollama_utils.logger')
    def test_setup_ollama_command_failure(self, mock_logger, mock_rsa_key):
        """Test setup_ollama when SSH commands fail."""
        # Set up mocks
        self.mock_vm_manager.get_instance_external_ip.return_value = self.test_vm_ip
        mock_key = MagicMock(spec=paramiko.PKey)
        mock_rsa_key.return_value = mock_key
        self.mock_ssh_client.ssh_connect.return_value = True
        self.mock_ssh_client.run_ssh_commands.return_value = False

        # Call the function
        result = ollama_utils.setup_ollama(
            self.mock_vm_manager, self.test_zone, self.test_instance_name, self.test_llm_model
        )

        # Verify the results
        self.assertFalse(result)
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with(
            self.test_zone, self.test_instance_name
        )
        self.mock_ssh_client.remove_known_host.assert_called_once_with(self.test_vm_ip)
        mock_rsa_key.assert_called_once_with("/path/to/ssh_key")
        self.mock_ssh_client.ssh_connect.assert_called_once_with(
            self.test_vm_ip, "testuser", mock_key
        )
        self.mock_ssh_client.run_ssh_commands.assert_called_once()
        mock_logger.error.assert_called_once()
        self.mock_ssh_client.ssh_disconnect.assert_called_once()

    @patch('paramiko.RSAKey.from_private_key_file')
    @patch('ollama_utils.logger')
    def test_setup_ollama_success(self, mock_logger, mock_rsa_key):
        """Test setup_ollama when setup is successful."""
        # Set up mocks
        self.mock_vm_manager.get_instance_external_ip.return_value = self.test_vm_ip
        mock_key = MagicMock(spec=paramiko.PKey)
        mock_rsa_key.return_value = mock_key
        self.mock_ssh_client.ssh_connect.return_value = True
        self.mock_ssh_client.run_ssh_commands.return_value = True
        self.mock_vm_manager.get_my_ip.return_value = "10.0.0.1"

        # Call the function
        result = ollama_utils.setup_ollama(
            self.mock_vm_manager, self.test_zone, self.test_instance_name, self.test_llm_model
        )

        # Verify the results
        self.assertTrue(result)
        self.mock_vm_manager.get_instance_external_ip.assert_called_once_with(
            self.test_zone, self.test_instance_name
        )
        self.mock_ssh_client.remove_known_host.assert_called_once_with(self.test_vm_ip)
        mock_rsa_key.assert_called_once_with("/path/to/ssh_key")
        self.mock_ssh_client.ssh_connect.assert_called_once_with(
            self.test_vm_ip, "testuser", mock_key
        )
        self.mock_ssh_client.run_ssh_commands.assert_called_once()
        self.mock_ssh_client.ssh_disconnect.assert_called_once()
        self.mock_vm_manager.get_my_ip.assert_called_once()
        self.mock_vm_manager.set_firewall_ollama_rule.assert_called_once_with(
            "10.0.0.1", "test-firewall-rule", "test-firewall-tag"
        )

    @patch('requests.get')
    @patch('ollama_utils.logger')
    def test_check_ollama_availability_connection_error(self, mock_logger, mock_requests_get):
        """Test check_ollama_availability when connection fails."""
        # Set up mocks
        mock_requests_get.side_effect = requests.RequestException("Connection error")

        # Call the function
        result = ollama_utils.check_ollama_availability(self.test_vm_ip, self.test_llm_model)

        # Verify the results
        self.assertFalse(result)
        mock_requests_get.assert_called_once_with(
            f"http://{self.test_vm_ip}:11434/api/tags", timeout=5
        )
        mock_logger.error.assert_called_once()

    @patch('requests.get')
    @patch('ollama_utils.logger')
    def test_check_ollama_availability_error_status(self, mock_logger, mock_requests_get):
        """Test check_ollama_availability when API returns error status."""
        # Set up mocks
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests_get.return_value = mock_response

        # Call the function
        result = ollama_utils.check_ollama_availability(self.test_vm_ip, self.test_llm_model)

        # Verify the results
        self.assertFalse(result)
        mock_requests_get.assert_called_once_with(
            f"http://{self.test_vm_ip}:11434/api/tags", timeout=5
        )
        mock_logger.error.assert_called_once()

    @patch('requests.get')
    @patch('ollama_utils.logger')
    def test_check_ollama_availability_model_not_available(self, mock_logger, mock_requests_get):
        """Test check_ollama_availability when model is not available."""
        # Set up mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "other-model"}
            ]
        }
        mock_requests_get.return_value = mock_response

        # Call the function
        result = ollama_utils.check_ollama_availability(self.test_vm_ip, self.test_llm_model)

        # Verify the results
        self.assertFalse(result)
        mock_requests_get.assert_called_once_with(
            f"http://{self.test_vm_ip}:11434/api/tags", timeout=5
        )
        mock_logger.warning.assert_called_once()

    @patch('requests.get')
    @patch('ollama_utils.logger')
    def test_check_ollama_availability_success(self, mock_logger, mock_requests_get):
        """Test check_ollama_availability when model is available."""
        # Set up mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": self.test_llm_model}
            ]
        }
        mock_requests_get.return_value = mock_response

        # Call the function
        result = ollama_utils.check_ollama_availability(self.test_vm_ip, self.test_llm_model)

        # Verify the results
        self.assertTrue(result)
        mock_requests_get.assert_called_once_with(
            f"http://{self.test_vm_ip}:11434/api/tags", timeout=5
        )
        mock_logger.info.assert_called_once()


if __name__ == '__main__':
    unittest.main()
