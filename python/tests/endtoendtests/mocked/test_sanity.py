"""
Sanity tests for the LLM VM Manager application.
These tests verify that the core functionality of the application works correctly.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the application modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from python.tests.memory_leak_detector import detect_leaks
from python.vm_operations import create_vm, start_vm, stop_vm, delete_vm
from python.ollama_utils import setup_ollama, check_ollama_availability


@pytest.mark.sanity
@detect_leaks
def test_create_vm(mock_vm_manager, mock_args, memory_leak_detector):
    """
    Test SN1: Create VM
    Create a new VM instance.
    The VM should be created successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "llama2"
    
    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = False
    
    # Call the create_vm function
    create_vm(mock_vm_manager, mock_args)
    
    # Verify that the VM was created
    mock_vm_manager.create_instance.assert_called_once_with("test-vm")
    mock_vm_manager.find_instance_zone.assert_called_with("test-vm")


@pytest.mark.sanity
@detect_leaks
def test_start_vm(mock_vm_manager, mock_args, memory_leak_detector):
    """
    Test SN2: Start VM
    Start an existing VM instance.
    The VM should start successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    
    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = True
    
    # Call the start_vm function
    start_vm(mock_vm_manager, mock_args)
    
    # Verify that the VM was started
    mock_vm_manager.start_instance.assert_called_once_with("test-vm")
    mock_vm_manager.find_instance_zone.assert_called_with("test-vm")


@pytest.mark.sanity
@detect_leaks
def test_stop_vm(mock_vm_manager, mock_args, memory_leak_detector):
    """
    Test SN3: Stop VM
    Stop a running VM instance.
    The VM should stop successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    
    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = True
    
    # Call the stop_vm function
    stop_vm(mock_vm_manager, mock_args)
    
    # Verify that the VM was stopped
    mock_vm_manager.stop_instance.assert_called_once_with("test-vm")


@pytest.mark.sanity
@detect_leaks
def test_delete_vm(mock_vm_manager, mock_args, memory_leak_detector):
    """
    Test SN4: Delete VM
    Delete a VM instance.
    The VM should be deleted successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    
    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = True
    
    # Call the delete_vm function
    delete_vm(mock_vm_manager, mock_args)
    
    # Verify that the VM was deleted
    mock_vm_manager.delete_instance.assert_called_once_with("test-vm")


@pytest.mark.sanity
@detect_leaks
def test_ollama_setup(mock_vm_manager, mock_ssh_client, memory_leak_detector):
    """
    Test SN5: Ollama Setup
    Set up Ollama on a VM.
    Ollama should be set up successfully.
    """
    # Set up the mock VM manager
    mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"
    
    # Call the setup_ollama function
    result = setup_ollama(mock_vm_manager, "us-central1-a", "test-vm", "llama2")
    
    # Verify that Ollama was set up
    assert result is True
    mock_vm_manager.ssh_client.remove_known_host.assert_called_once_with("192.168.1.1")
    mock_vm_manager.ssh_client.ssh_connect.assert_called_once()
    mock_vm_manager.ssh_client.run_ssh_commands.assert_called_once()
    mock_vm_manager.ssh_client.ssh_disconnect.assert_called_once()
    mock_vm_manager.set_firewall_ollama_rule.assert_called_once()


@pytest.mark.sanity
@detect_leaks
def test_ollama_model_pull(mock_requests, memory_leak_detector):
    """
    Test SN6: Ollama Model Pull
    Pull an LLM model to Ollama.
    The model should be pulled successfully.
    """
    # Call the check_ollama_availability function
    result = check_ollama_availability("192.168.1.1", "llama2")
    
    # Verify that the model was pulled
    assert result is True
    mock_requests.get.assert_called_once_with("http://192.168.1.1:11434/api/tags", timeout=5)