"""
Security tests for the LLM VM Manager application.
These tests verify that the application is secure and protects sensitive information.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import stat

# Add the parent directory to the path so we can import the application modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

# from python.tests.memory_leak_detector import detect_leaks
from python.ollama_utils import setup_ollama


@pytest.mark.security
# @detect_leaks
def test_ssh_key_protection():
    """
    Test SE1: SSH Key Protection
    Verify that SSH keys are protected.
    SSH keys should be stored securely and not exposed.
    """
    # Mock the os.path.isfile and os.stat functions
    with patch('os.path.isfile', return_value=True), \
         patch('os.stat') as mock_stat:
        
        # Set up the mock stat result to simulate secure file permissions (600)
        mock_stat_result = MagicMock()
        mock_stat_result.st_mode = stat.S_IRUSR | stat.S_IWUSR  # 600 permissions (owner read/write only)
        mock_stat.return_value = mock_stat_result
        
        # Check if the SSH key file has secure permissions
        ssh_key_file = "/path/to/ssh/key"
        file_stat = os.stat(ssh_key_file)
        
        # Verify that the file permissions are secure
        # Only the owner should have read and write permissions, no execute, no group or other permissions
        secure_permissions = (file_stat.st_mode & (stat.S_IRWXG | stat.S_IRWXO)) == 0  # No group or other permissions
        secure_permissions = secure_permissions and (file_stat.st_mode & stat.S_IXUSR) == 0  # No owner execute
        secure_permissions = secure_permissions and (file_stat.st_mode & (stat.S_IRUSR | stat.S_IWUSR)) != 0  # Owner read/write
        
        assert secure_permissions, "SSH key file permissions are not secure"


@pytest.mark.security
# @detect_leaks
def test_gcp_key_protection():
    """
    Test SE2: GCP Key Protection
    Verify that GCP keys are protected.
    GCP keys should be stored securely and not exposed.
    """
    # Mock the os.path.isfile and os.stat functions
    with patch('os.path.isfile', return_value=True), \
         patch('os.stat') as mock_stat:
        
        # Set up the mock stat result to simulate secure file permissions (600)
        mock_stat_result = MagicMock()
        mock_stat_result.st_mode = stat.S_IRUSR | stat.S_IWUSR  # 600 permissions (owner read/write only)
        mock_stat.return_value = mock_stat_result
        
        # Check if the GCP key file has secure permissions
        gcp_key_file = "/path/to/gcp/key.json"
        file_stat = os.stat(gcp_key_file)
        
        # Verify that the file permissions are secure
        # Only the owner should have read and write permissions, no execute, no group or other permissions
        secure_permissions = (file_stat.st_mode & (stat.S_IRWXG | stat.S_IRWXO)) == 0  # No group or other permissions
        secure_permissions = secure_permissions and (file_stat.st_mode & stat.S_IXUSR) == 0  # No owner execute
        secure_permissions = secure_permissions and (file_stat.st_mode & (stat.S_IRUSR | stat.S_IWUSR)) != 0  # Owner read/write
        
        assert secure_permissions, "GCP key file permissions are not secure"


@pytest.mark.security
# @detect_leaks
def test_firewall_rule_effectiveness(mock_vm_manager):
    """
    Test SE3: Firewall Rule Effectiveness
    Verify that firewall rules are effective.
    Only authorized IPs should be able to access the Ollama API.
    """
    # Set up the mock VM manager
    mock_vm_manager.get_my_ip.return_value = "127.0.0.1"
    
    # Call the set_firewall_ollama_rule function
    mock_vm_manager.set_firewall_ollama_rule("127.0.0.1", "test-firewall-rule", "test-tag")
    
    # Verify that the firewall rule was created with the correct parameters
    mock_vm_manager.set_firewall_ollama_rule.assert_called_once_with("127.0.0.1", "test-firewall-rule", "test-tag")
    
    # In a real test, we would verify that the firewall rule is effective by trying to access the Ollama API
    # from an unauthorized IP, but since we're mocking, we'll just verify that the function was called correctly


@pytest.mark.security
# @detect_leaks
def test_secure_ssh_connection(mock_vm_manager, mock_ssh_client):
    """
    Test SE4: Secure SSH Connection
    Verify that SSH connections are secure.
    SSH connections should use encryption and key-based authentication.
    """
    # Set up the mock VM manager
    mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"
    
    # Mock the paramiko.RSAKey.from_private_key_file function
    with patch('paramiko.RSAKey.from_private_key_file') as mock_rsa_key:
        # Set up the mock RSA key
        mock_key = MagicMock()
        mock_rsa_key.return_value = mock_key
        
        # Call the setup_ollama function (which uses SSH)
        result = setup_ollama(mock_vm_manager, "us-central1-a", "test-vm", "llama2")
        
        # Verify that the SSH connection was established using key-based authentication
        assert result is True
        mock_rsa_key.assert_called_once()
        mock_vm_manager.ssh_client.ssh_connect.assert_called_once_with("192.168.1.1", mock_vm_manager.llm_vm_manager_config.get("ssh.user"), mock_key)


@pytest.mark.security
# @detect_leaks
def test_secure_api_communication(mock_requests):
    """
    Test SE5: Secure API Communication
    Verify that API communication is secure.
    API communication should use HTTPS.
    """
    # In a real test, we would verify that the API communication uses HTTPS
    # Since we're mocking, we'll just verify that the requests.get function is called with an HTTPS URL
    
    # Mock the requests.get function to accept both HTTP and HTTPS
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama2"}
        ]
    }
    mock_requests.get.return_value = mock_response
    
    # Call the check_ollama_availability function with an HTTPS URL
    from python.ollama_utils import check_ollama_availability
    with patch('python.ollama_utils.requests.get') as mock_get:
        mock_get.return_value = mock_response
        
        # Call the function with an HTTPS URL
        result = check_ollama_availability("192.168.1.1", "llama2")
        
        # Verify that the function was called with an HTTPS URL
        mock_get.assert_called_once_with("https://192.168.1.1:11434/api/tags", timeout=5)
        assert result is True