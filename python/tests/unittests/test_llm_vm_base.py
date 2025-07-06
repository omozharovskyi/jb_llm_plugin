import unittest
from unittest.mock import patch, MagicMock
import requests
from requests.exceptions import RequestException

from llm_vm_manager.llm_vm_base import LLMVirtualMachineManager
from llm_vm_manager.config import ConfigLoader


class ConcreteLLMVirtualMachineManager(LLMVirtualMachineManager):
    """Concrete implementation of LLMVirtualMachineManager for testing."""
    
    def create_instance(self, name: str) -> None:
        pass
        
    def start_instance(self, name: str) -> None:
        pass
        
    def stop_instance(self, name: str) -> None:
        pass
        
    def delete_instance(self, name: str) -> None:
        pass
        
    def list_instances(self) -> None:
        pass


class TestLLMVirtualMachineManager(unittest.TestCase):
    """Test cases for LLMVirtualMachineManager class."""

    def setUp(self):
        """Set up test environment before each test."""
        # Mock configuration
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get.side_effect = self._mock_config_get
        
        # Create instance of concrete implementation
        self.vm_manager = ConcreteLLMVirtualMachineManager(self.mock_config)
        
    def _mock_config_get(self, key):
        """Mock configuration get method."""
        config_values = {
            'my_ip_url': 'https://api.ipify.org'
        }
        return config_values.get(key, None)
        
    def test_init(self):
        """Test initialization of LLMVirtualMachineManager."""
        self.assertEqual(self.vm_manager.llm_vm_manager_config, self.mock_config)
        self.assertIsNotNone(self.vm_manager.ssh_manager)
        self.assertIsNotNone(self.vm_manager.ssh_client)
        
    @patch('llm_vm_manager.llm_vm_base.requests.get')
    def test_get_my_ip(self, mock_requests_get):
        """Test get_my_ip method."""
        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.text = '192.168.1.1'
        mock_requests_get.return_value = mock_response
        
        # Call get_my_ip
        result = self.vm_manager.get_my_ip()
        
        # Verify the result
        self.assertEqual(result, '192.168.1.1')
        mock_requests_get.assert_called_once_with('https://api.ipify.org')
        
    @patch('llm_vm_manager.llm_vm_base.requests.get')
    @patch('llm_vm_manager.llm_vm_base.logger')
    def test_check_ollama_model_available_success(self, mock_logger, mock_requests_get):
        """Test check_ollama_model_available method when model is available."""
        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama2'},
                {'name': 'mistral'}
            ]
        }
        mock_requests_get.return_value = mock_response
        
        # Call check_ollama_model_available
        result = self.vm_manager.check_ollama_model_available('10.0.0.1', 'llama2')
        
        # Verify the result
        self.assertTrue(result)
        mock_requests_get.assert_called_once_with('http://10.0.0.1:11434/api/tags', timeout=5)
        mock_logger.info.assert_called_once()
        
    @patch('llm_vm_manager.llm_vm_base.requests.get')
    @patch('llm_vm_manager.llm_vm_base.logger')
    def test_check_ollama_model_available_not_found(self, mock_logger, mock_requests_get):
        """Test check_ollama_model_available method when model is not available."""
        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'mistral'}
            ]
        }
        mock_requests_get.return_value = mock_response
        
        # Call check_ollama_model_available
        result = self.vm_manager.check_ollama_model_available('10.0.0.1', 'llama2')
        
        # Verify the result
        self.assertFalse(result)
        mock_requests_get.assert_called_once_with('http://10.0.0.1:11434/api/tags', timeout=5)
        mock_logger.warning.assert_called_once()
        
    @patch('llm_vm_manager.llm_vm_base.requests.get')
    @patch('llm_vm_manager.llm_vm_base.logger')
    def test_check_ollama_model_available_error_status(self, mock_logger, mock_requests_get):
        """Test check_ollama_model_available method when API returns error status."""
        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_requests_get.return_value = mock_response
        
        # Call check_ollama_model_available
        result = self.vm_manager.check_ollama_model_available('10.0.0.1', 'llama2')
        
        # Verify the result
        self.assertFalse(result)
        mock_requests_get.assert_called_once_with('http://10.0.0.1:11434/api/tags', timeout=5)
        mock_logger.error.assert_called_once()
        
    @patch('llm_vm_manager.llm_vm_base.requests.get')
    @patch('llm_vm_manager.llm_vm_base.logger')
    def test_check_ollama_model_available_request_exception(self, mock_logger, mock_requests_get):
        """Test check_ollama_model_available method when request raises exception."""
        # Mock requests.get to raise RequestException
        mock_requests_get.side_effect = RequestException("Connection error")
        
        # Call check_ollama_model_available
        result = self.vm_manager.check_ollama_model_available('10.0.0.1', 'llama2')
        
        # Verify the result
        self.assertFalse(result)
        mock_requests_get.assert_called_once_with('http://10.0.0.1:11434/api/tags', timeout=5)
        mock_logger.error.assert_called_once()


if __name__ == '__main__':
    unittest.main()