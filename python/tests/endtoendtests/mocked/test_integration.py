"""
Integration tests for the LLM VM Manager application.
These tests verify that different components of the application work together correctly.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

# Add the parent directory to the path so we can import the application modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from python.vm_operations import create_vm, start_vm, stop_vm, delete_vm
from python.ollama_utils import setup_ollama, check_ollama_availability


@pytest.mark.integration
def test_create_and_start_vm(mock_vm_manager, mock_args):
    """
    Test I1: Create and Start VM
    Create a VM and then start it.
    The VM should be created and started successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "llama2"

    # Set up the mock VM manager
    mock_vm_manager.instance_exists.side_effect = [False, True]  # First call returns False, second call returns True

    # Call the create_vm function
    create_vm(mock_vm_manager, mock_args)

    # Verify that the VM was created
    mock_vm_manager.create_instance.assert_called_once_with("test-vm")

    # Call the start_vm function
    start_vm(mock_vm_manager, mock_args)

    # Verify that the VM was started
    mock_vm_manager.start_instance.assert_called_once_with("test-vm")


@pytest.mark.integration
def test_start_and_stop_vm(mock_vm_manager, mock_args):
    """
    Test I2: Start and Stop VM
    Start a VM and then stop it.
    The VM should be started and stopped successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"

    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = True

    # Call the start_vm function
    start_vm(mock_vm_manager, mock_args)

    # Verify that the VM was started
    mock_vm_manager.start_instance.assert_called_once_with("test-vm")

    # Call the stop_vm function
    stop_vm(mock_vm_manager, mock_args)

    # Verify that the VM was stopped
    mock_vm_manager.stop_instance.assert_called_once_with("test-vm")


@pytest.mark.integration
def test_create_start_and_delete_vm(mock_vm_manager, mock_args):
    """
    Test I3: Create, Start, and Delete VM
    Create a VM, start it, and then delete it.
    The VM should be created, started, and deleted successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "llama2"

    # Set up the mock VM manager
    mock_vm_manager.instance_exists.side_effect = [False, True, True]  # First call returns False, others return True

    # Call the create_vm function
    create_vm(mock_vm_manager, mock_args)

    # Verify that the VM was created
    mock_vm_manager.create_instance.assert_called_once_with("test-vm")

    # Call the start_vm function
    start_vm(mock_vm_manager, mock_args)

    # Verify that the VM was started
    mock_vm_manager.start_instance.assert_called_once_with("test-vm")

    # Call the delete_vm function
    delete_vm(mock_vm_manager, mock_args)

    # Verify that the VM was deleted
    mock_vm_manager.delete_instance.assert_called_once_with("test-vm")


@pytest.mark.integration
def test_create_vm_and_check_ollama(mock_vm_manager, mock_args, mock_requests):
    """
    Test I4: Create VM and Check Ollama
    Create a VM and check if Ollama is available.
    The VM should be created and Ollama should be available.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "llama2"

    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = False
    mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"

    # Set up the mock response for Ollama API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama2"}
        ]
    }
    mock_requests.get.return_value = mock_response

    # Call the create_vm function
    create_vm(mock_vm_manager, mock_args)

    # Verify that the VM was created
    mock_vm_manager.create_instance.assert_called_once_with("test-vm")

    # Verify that Ollama was checked
    mock_requests.get.assert_called_with("http://192.168.1.1:11434/api/tags", timeout=5)


@pytest.mark.integration
def test_create_vm_pull_model_and_check_model(mock_vm_manager, mock_args, mock_requests):
    """
    Test I5: Create VM, Pull Model, and Check Model
    Create a VM, pull a model, and check if the model is available.
    The VM should be created, the model should be pulled, and the model should be available.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "llama2"

    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = False
    mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"

    # Set up the mock response for Ollama API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama2"}
        ]
    }
    mock_requests.get.return_value = mock_response

    # Call the create_vm function
    create_vm(mock_vm_manager, mock_args)

    # Verify that the VM was created
    mock_vm_manager.create_instance.assert_called_once_with("test-vm")

    # Verify that the model was pulled
    # This is indirectly verified by checking that run_ssh_commands was called
    mock_vm_manager.ssh_client.run_ssh_commands.assert_called_once()

    # Verify that the model was checked
    mock_requests.get.assert_called_with("http://192.168.1.1:11434/api/tags", timeout=5)
