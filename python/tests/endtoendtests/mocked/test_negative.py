"""
Negative tests for the LLM VM Manager application.
These tests verify that the application handles error conditions correctly.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import requests

# Add the parent directory to the path so we can import the application modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from python.vm_operations import create_vm, start_vm, stop_vm, delete_vm
from python.ollama_utils import setup_ollama, check_ollama_availability
from python.utils import load_configuration


@pytest.mark.negative
def test_create_existing_vm(mock_vm_manager, mock_args):
    """
    Test N1: Create Existing VM
    Try to create a VM that already exists.
    The application should display a warning and not create a new VM.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "llama2"

    # Set up the mock VM manager to indicate that the VM already exists
    mock_vm_manager.instance_exists.return_value = True

    # Call the create_vm function
    create_vm(mock_vm_manager, mock_args)

    # Verify that the VM was not created
    mock_vm_manager.create_instance.assert_not_called()
    # Verify that list_vms was called to show existing VMs
    mock_vm_manager.list_instances.assert_called_once()


@pytest.mark.negative
def test_start_nonexistent_vm(mock_vm_manager, mock_args):
    """
    Test N2: Start Non-existent VM
    Try to start a VM that doesn't exist.
    The application should display an error message.
    """
    # Set up the mock arguments
    mock_args.name = "nonexistent-vm"

    # Set up the mock VM manager to indicate that the VM doesn't exist
    mock_vm_manager.instance_exists.return_value = False

    # Call the start_vm function
    start_vm(mock_vm_manager, mock_args)

    # Verify that the VM was not started
    mock_vm_manager.start_instance.assert_not_called()


@pytest.mark.negative
def test_stop_nonexistent_vm(mock_vm_manager, mock_args):
    """
    Test N3: Stop Non-existent VM
    Try to stop a VM that doesn't exist.
    The application should display an error message.
    """
    # Set up the mock arguments
    mock_args.name = "nonexistent-vm"

    # Set up the mock VM manager to indicate that the VM doesn't exist
    mock_vm_manager.instance_exists.return_value = False

    # Call the stop_vm function
    stop_vm(mock_vm_manager, mock_args)

    # Verify that the VM was not stopped
    mock_vm_manager.stop_instance.assert_not_called()


@pytest.mark.negative
# @detect_leaks
def test_delete_nonexistent_vm(mock_vm_manager, mock_args):
    """
    Test N4: Delete Non-existent VM
    Try to delete a VM that doesn't exist.
    The application should display an error message.
    """
    # Set up the mock arguments
    mock_args.name = "nonexistent-vm"

    # Set up the mock VM manager to indicate that the VM doesn't exist
    mock_vm_manager.instance_exists.return_value = False

    # Call the delete_vm function
    delete_vm(mock_vm_manager, mock_args)

    # Verify that the VM was not deleted
    mock_vm_manager.delete_instance.assert_not_called()


@pytest.mark.negative
# @detect_leaks
def test_invalid_configuration():
    """
    Test N5: Invalid Configuration
    Run the application with an invalid configuration file.
    The application should display an error message.
    """
    # Mock the load_configuration function to raise a FileNotFoundError
    with patch('python.utils.ConfigLoader', side_effect=FileNotFoundError()), \
         patch('python.utils.logger.error') as mock_error, \
         patch('sys.exit') as mock_exit:

        # Call the load_configuration function
        load_configuration("nonexistent_config.toml")

        # Verify that an error was logged and sys.exit was called
        mock_error.assert_called_once()
        mock_exit.assert_called_once_with(1)


@pytest.mark.negative
# @detect_leaks
def test_missing_ssh_key(mock_vm_manager):
    """
    Test N6: Missing SSH Key
    Run the application with a missing SSH key.
    The application should display an error message.
    """
    # Set up the mock VM manager
    mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"

    # Mock the paramiko.RSAKey.from_private_key_file function to raise an exception
    with patch('paramiko.RSAKey.from_private_key_file', side_effect=Exception("Failed to load SSH key")), \
         patch('python.ollama_utils.logger.error') as mock_error:

        # Call the setup_ollama function
        result = setup_ollama(mock_vm_manager, "us-central1-a", "test-vm", "llama2")

        # Verify that an error was logged and the function returned False
        mock_error.assert_called_once()
        assert result is False


@pytest.mark.negative
# @detect_leaks
def test_missing_gcp_key():
    """
    Test N7: Missing GCP Key
    Run the application with a missing GCP key.
    The application should display an error message.
    """
    # Mock the service_account.Credentials.from_service_account_file function to raise an exception
    with patch('google.oauth2.service_account.Credentials.from_service_account_file', 
               side_effect=FileNotFoundError("GCP key file not found")), \
         patch('python.llm_vm_manager.llm_vm_gcp.logger.error') as mock_error:

        # Create a mock config
        mock_config = MagicMock()
        mock_config.get.return_value = "nonexistent_key.json"

        # Try to create a GCPVirtualMachineManager instance
        from python.llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager

        # This should raise an exception
        with pytest.raises(FileNotFoundError):
            GCPVirtualMachineManager(mock_config)


@pytest.mark.negative
# @detect_leaks
def test_invalid_gcp_project(mock_vm_manager):
    """
    Test N8: Invalid GCP Project
    Run the application with an invalid GCP project.
    The application should display an error message.
    """
    # Set up the mock VM manager
    mock_vm_manager.project_id = "invalid-project"

    # Mock the compute.instances().list().execute() function to raise an exception
    with patch.object(mock_vm_manager, 'list_instances', side_effect=Exception("Invalid project")), \
         patch('python.vm_operations.logger.error') as mock_error:

        # Call the list_vms function
        from python.vm_operations import list_vms
        list_vms(mock_vm_manager, MagicMock())

        # Verify that an error was logged
        mock_error.assert_called_once()


@pytest.mark.negative
# @detect_leaks
def test_invalid_vm_name(mock_vm_manager, mock_args):
    """
    Test N9: Invalid VM Name
    Run the application with an invalid VM name.
    The application should display an error message.
    """
    # Set up the mock arguments with an invalid VM name (empty string)
    mock_args.name = ""
    mock_args.model = "llama2"

    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = False

    # Mock the create_instance method to raise an exception for invalid VM name
    mock_vm_manager.create_instance.side_effect = ValueError("Invalid VM name")

    # Call the create_vm function
    with patch('python.vm_operations.logger.error') as mock_error:
        create_vm(mock_vm_manager, mock_args)

        # Verify that an error was logged
        mock_error.assert_called_once()


@pytest.mark.negative
# @detect_leaks
def test_invalid_model_name(mock_vm_manager, mock_args):
    """
    Test N10: Invalid Model Name
    Run the application with an invalid model name.
    The application should display an error message.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "invalid-model"

    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = False

    # Mock the setup_ollama function to return False for invalid model name
    with patch('python.vm_operations.setup_ollama', return_value=False), \
         patch('python.vm_operations.logger.error') as mock_error:

        # Call the create_vm function
        create_vm(mock_vm_manager, mock_args)

        # Verify that an error was logged
        mock_error.assert_called_once()


@pytest.mark.negative
# @detect_leaks
def test_network_failure(mock_vm_manager):
    """
    Test N11: Network Failure
    Simulate a network failure during VM creation.
    The application should handle the failure gracefully.
    """
    # Set up the mock VM manager
    mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"

    # Mock the requests.get function to raise a ConnectionError
    with patch('requests.get', side_effect=requests.ConnectionError("Network failure")), \
         patch('python.ollama_utils.logger.error') as mock_error:

        # Call the check_ollama_availability function
        result = check_ollama_availability("192.168.1.1", "llama2")

        # Verify that an error was logged and the function returned False
        mock_error.assert_called_once()
        assert result is False


@pytest.mark.negative
# @detect_leaks
def test_gcp_api_failure(mock_vm_manager, mock_args):
    """
    Test N12: GCP API Failure
    Simulate a GCP API failure.
    The application should handle the failure gracefully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"

    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = True

    # Mock the start_instance method to raise an exception
    mock_vm_manager.start_instance.side_effect = Exception("GCP API failure")

    # Call the start_vm function
    with patch('python.vm_operations.logger.error') as mock_error:
        start_vm(mock_vm_manager, mock_args)

        # Verify that an error was logged
        mock_error.assert_called_once()


@pytest.mark.negative
# @detect_leaks
def test_ssh_connection_failure(mock_vm_manager, mock_ssh_client):
    """
    Test N13: SSH Connection Failure
    Simulate an SSH connection failure.
    The application should handle the failure gracefully.
    """
    # Set up the mock VM manager
    mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"

    # Set up the mock SSH client to fail on connect
    mock_ssh_client.ssh_connect.return_value = False

    # Call the setup_ollama function
    with patch('python.ollama_utils.logger.error') as mock_error:
        result = setup_ollama(mock_vm_manager, "us-central1-a", "test-vm", "llama2")

        # Verify that an error was logged and the function returned False
        mock_error.assert_called_once()
        assert result is False


@pytest.mark.negative
# @detect_leaks
def test_ollama_installation_failure(mock_vm_manager, mock_ssh_client):
    """
    Test N14: Ollama Installation Failure
    Simulate an Ollama installation failure.
    The application should handle the failure gracefully.
    """
    # Set up the mock VM manager
    mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"

    # Set up the mock SSH client to fail on run_ssh_commands
    mock_ssh_client.ssh_connect.return_value = True
    mock_ssh_client.run_ssh_commands.return_value = False

    # Call the setup_ollama function
    with patch('python.ollama_utils.logger.error') as mock_error:
        result = setup_ollama(mock_vm_manager, "us-central1-a", "test-vm", "llama2")

        # Verify that an error was logged and the function returned False
        mock_error.assert_called_once()
        assert result is False


@pytest.mark.negative
# @detect_leaks
def test_model_pull_failure(mock_requests):
    """
    Test N15: Model Pull Failure
    Simulate a model pull failure.
    The application should handle the failure gracefully.
    """
    # Set up the mock response for Ollama API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "mistral"}  # llama2 is not in the list
        ]
    }
    mock_requests.get.return_value = mock_response

    # Call the check_ollama_availability function
    with patch('python.ollama_utils.logger.warning') as mock_warning:
        result = check_ollama_availability("192.168.1.1", "llama2")

        # Verify that a warning was logged and the function returned False
        mock_warning.assert_called_once()
        assert result is False
