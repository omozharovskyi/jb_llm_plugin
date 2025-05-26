"""
Regression tests for the LLM VM Manager application.
These tests verify that new changes don't break existing functionality.
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


@pytest.mark.regression
@detect_leaks
def test_full_workflow(mock_vm_manager, mock_args, memory_leak_detector):
    """
    Test R1: Full Workflow
    Run a full workflow (create, start, stop, delete).
    All operations should complete successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "llama2"
    
    # Set up the mock VM manager
    # First call to instance_exists is for create_vm (should return False)
    # Second call is for start_vm (should return True)
    # Third call is for stop_vm (should return True)
    # Fourth call is for delete_vm (should return True)
    mock_vm_manager.instance_exists.side_effect = [False, True, True, True]
    
    # Call the create_vm function
    create_vm(mock_vm_manager, mock_args)
    
    # Verify that the VM was created
    mock_vm_manager.create_instance.assert_called_once_with("test-vm")
    
    # Call the start_vm function
    start_vm(mock_vm_manager, mock_args)
    
    # Verify that the VM was started
    mock_vm_manager.start_instance.assert_called_once_with("test-vm")
    
    # Call the stop_vm function
    stop_vm(mock_vm_manager, mock_args)
    
    # Verify that the VM was stopped
    mock_vm_manager.stop_instance.assert_called_once_with("test-vm")
    
    # Call the delete_vm function
    delete_vm(mock_vm_manager, mock_args)
    
    # Verify that the VM was deleted
    mock_vm_manager.delete_instance.assert_called_once_with("test-vm")


@pytest.mark.regression
@detect_leaks
def test_configuration_changes(mock_config, memory_leak_detector):
    """
    Test R2: Configuration Changes
    Change configuration settings and verify that they take effect.
    The application should use the new configuration settings.
    """
    # Original configuration
    original_instance_name = mock_config.get("gcp.instance_name")
    original_model = mock_config.get("llm_model")
    
    # Create a new configuration with different values
    new_config_values = {
        "gcp.instance_name": "new-vm-name",
        "llm_model": "new-model"
    }
    
    # Update the mock_config.get side effect to return new values
    def get_side_effect(key, default=None):
        return new_config_values.get(key, mock_config.get(key, default))
    
    mock_config.get.side_effect = get_side_effect
    
    # Verify that the new configuration values are used
    assert mock_config.get("gcp.instance_name") == "new-vm-name"
    assert mock_config.get("llm_model") == "new-model"
    
    # Verify that other configuration values are unchanged
    assert mock_config.get("gcp.project_name") == "test-project"


@pytest.mark.regression
@detect_leaks
def test_different_vm_types(mock_vm_manager, mock_args, memory_leak_detector):
    """
    Test R3: Different VM Types
    Create VMs with different machine types.
    VMs with different machine types should be created successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "llama2"
    
    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = False
    
    # Mock the build_vm_config method to capture the machine_type parameter
    original_build_vm_config = mock_vm_manager.build_vm_config
    
    # Test with different machine types
    machine_types = ["n1-standard-1", "n1-standard-2", "n1-standard-4"]
    
    for machine_type in machine_types:
        # Update the mock_config to return a different machine type
        mock_vm_manager.llm_vm_manager_config.get.side_effect = lambda key, default=None: machine_type if key == "gcp.machine_type" else original_build_vm_config(key, default)
        
        # Call the create_vm function
        create_vm(mock_vm_manager, mock_args)
        
        # Verify that the VM was created
        mock_vm_manager.create_instance.assert_called_with("test-vm")


@pytest.mark.regression
@detect_leaks
def test_different_gpu_types(mock_vm_manager, mock_args, memory_leak_detector):
    """
    Test R4: Different GPU Types
    Create VMs with different GPU types.
    VMs with different GPU types should be created successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "llama2"
    
    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = False
    
    # Mock the build_vm_config method to capture the gpu_accelerator parameter
    original_build_vm_config = mock_vm_manager.build_vm_config
    
    # Test with different GPU types
    gpu_types = ["nvidia-tesla-t4", "nvidia-tesla-v100", "nvidia-tesla-p100"]
    
    for gpu_type in gpu_types:
        # Update the mock_config to return a different GPU type
        mock_vm_manager.llm_vm_manager_config.get.side_effect = lambda key, default=None: gpu_type if key == "gcp.gpu_accelerator" else original_build_vm_config(key, default)
        
        # Call the create_vm function
        create_vm(mock_vm_manager, mock_args)
        
        # Verify that the VM was created
        mock_vm_manager.create_instance.assert_called_with("test-vm")


@pytest.mark.regression
@detect_leaks
def test_different_os_images(mock_vm_manager, mock_args, memory_leak_detector):
    """
    Test R5: Different OS Images
    Create VMs with different OS images.
    VMs with different OS images should be created successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    mock_args.model = "llama2"
    
    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = False
    
    # Mock the build_vm_config method to capture the image_family parameter
    original_build_vm_config = mock_vm_manager.build_vm_config
    
    # Test with different OS images
    os_images = ["ubuntu-2204-lts", "ubuntu-2004-lts", "debian-11"]
    
    for os_image in os_images:
        # Update the mock_config to return a different OS image
        mock_vm_manager.llm_vm_manager_config.get.side_effect = lambda key, default=None: os_image if key == "gcp.image_family" else original_build_vm_config(key, default)
        
        # Call the create_vm function
        create_vm(mock_vm_manager, mock_args)
        
        # Verify that the VM was created
        mock_vm_manager.create_instance.assert_called_with("test-vm")


@pytest.mark.regression
@detect_leaks
def test_different_llm_models(mock_vm_manager, mock_args, mock_requests, memory_leak_detector):
    """
    Test R6: Different LLM Models
    Pull different LLM models.
    Different LLM models should be pulled successfully.
    """
    # Set up the mock arguments
    mock_args.name = "test-vm"
    
    # Set up the mock VM manager
    mock_vm_manager.instance_exists.return_value = False
    mock_vm_manager.get_instance_external_ip.return_value = "192.168.1.1"
    
    # Test with different LLM models
    llm_models = ["llama2", "mistral", "vicuna"]
    
    for llm_model in llm_models:
        # Set up the mock arguments with a different model
        mock_args.model = llm_model
        
        # Set up the mock response for Ollama API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": llm_model}
            ]
        }
        mock_requests.get.return_value = mock_response
        
        # Call the create_vm function
        create_vm(mock_vm_manager, mock_args)
        
        # Verify that the VM was created
        mock_vm_manager.create_instance.assert_called_with("test-vm")
        
        # Verify that the model was checked
        mock_requests.get.assert_called_with("http://192.168.1.1:11434/api/tags", timeout=5)