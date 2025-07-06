# End-to-End Testing Guideline for LLM VM Manager (Live Tests)

This document provides a detailed guideline for writing live end-to-end tests for the LLM VM Manager application. It focuses on tests marked as "Live" or "Mocked + Live" (following the "Live" logic) in the [e2e_testing.md](e2e_testing.md) file.

## Table of Contents

1. [Introduction](#introduction)
2. [Test Environment Setup](#test-environment-setup)
3. [Test Framework](#test-framework)
4. [Test Categories](#test-categories)
5. [Test Fixtures](#test-fixtures)
6. [Test Implementation](#test-implementation)
7. [Test Execution](#test-execution)
8. [Test Reporting](#test-reporting)
9. [Best Practices](#best-practices)
10. [Example Tests](#example-tests)

## Introduction

End-to-end tests verify that the entire application works correctly from start to finish. Live end-to-end tests interact with real external services (like GCP and Ollama) rather than using mocks. This makes them more realistic but also more complex to set up and maintain.

The LLM VM Manager application has the following main components:
- Command-line interface (main.py)
- VM operations (vm_operations.py)
- Ollama utilities (ollama_utils.py)
- GCP VM management (llm_vm_manager/llm_vm_gcp.py)

Live end-to-end tests should test the interaction between these components and the external services they depend on.

## Test Environment Setup

### Prerequisites

1. **GCP Account**: You need a GCP account with billing enabled and the necessary permissions to create and manage VMs.
2. **GCP Project**: Create a dedicated test project in GCP to avoid interfering with production resources.
3. **GCP Service Account**: Create a service account with the necessary permissions and download the key file.
4. **SSH Keys**: Generate SSH keys for connecting to the VMs.
5. **Python Environment**: Set up a Python environment with the necessary dependencies.

### Configuration

Create a dedicated test configuration file (e.g., `test_config.toml`) with the following settings:

```toml
# GCP settings
gcp.project_id = "your-test-project-id"
gcp.zone = "us-central1-a"
gcp.machine_type = "n1-standard-1"
gcp.image_family = "ubuntu-2204-lts"
gcp.hdd_size = 10
gcp.gpu_accelerator = "nvidia-tesla-t4"
gcp.restart_on_failure = true
gcp.ssh_pub_key_file = "path/to/your/ssh/key.pub"
gcp.firewall_tag = "ollama-server"
gcp.firewall_rule_name = "allow-ollama-api-from-my-ip"
gcp.service_account_file = "path/to/your/service-account-key.json"

# SSH settings
ssh.ssh_secret_key = "path/to/your/ssh/key"
ssh.user = "your-ssh-username"

# LLM settings
llm_model = "llama2"

# Logging settings
log_level = "DEBUG"
```

## Test Framework

We'll use pytest as our test framework. Pytest provides a powerful and flexible way to write and organize tests.

### Directory Structure

Create the following directory structure for your end-to-end tests:

```
python/tests/endtoendtests/
├── conftest.py           # Pytest configuration and fixtures
├── e2e_testing.md        # Test plan
├── e2e_live_guideline.md # This guideline
└── test_e2e_live.py      # Live end-to-end tests
```

### Basic Test Structure

Here's a basic structure for a pytest test file:

```python
import pytest
import os
import sys
import subprocess
import time
import requests

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from python.llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from python.llm_vm_manager.config import ConfigLoader
from python.vm_operations import create_vm, start_vm, stop_vm, delete_vm, list_vms
from python.ollama_utils import setup_ollama, check_ollama_availability

# Test functions will be defined here
```

## Test Categories

Based on the e2e_testing.md file, we'll focus on the following test categories for live tests:

1. **Smoke Tests**: Basic functionality tests (S1, S2)
2. **Sanity Tests**: Core functionality tests (SN1, SN2, SN3, SN4, SN5, SN6)
3. **Integration Tests**: Tests for component interaction (I1, I2, I3, I4, I5)
4. **Performance Tests**: Tests for performance metrics (P1, P2, P3, P4, P5, P6, P7)
5. **Security Tests**: Tests for security aspects (SE3, SE4)
6. **Regression Tests**: Tests for ensuring existing functionality (R1)

## Test Fixtures

Pytest fixtures are a powerful way to set up and tear down test environments. We'll define fixtures for:

1. **Configuration**: Load the test configuration
2. **VM Manager**: Create a VM manager instance
3. **Test VM**: Create, start, and delete a test VM
4. **Test Categories**: Mark tests by category

### Example Fixtures

Here's an example of how to define these fixtures in `conftest.py`:

```python
import pytest
import os
import sys
import time

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from python.llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from python.llm_vm_manager.config import ConfigLoader
from python.vm_operations import create_vm, start_vm, stop_vm, delete_vm, list_vms

# Configuration fixture
@pytest.fixture(scope="session")
def config():
    """Load the test configuration."""
    config_file = os.path.join(os.path.dirname(__file__), "test_config.toml")
    return ConfigLoader(config_file)

# VM Manager fixture
@pytest.fixture(scope="session")
def vm_manager(config):
    """Create a VM manager instance."""
    return GCPVirtualMachineManager(config)

# Test VM fixture
@pytest.fixture(scope="function")
def test_vm(vm_manager, request):
    """Create, start, and delete a test VM."""
    # Generate a unique VM name for this test
    vm_name = f"test-vm-{int(time.time())}"
    
    # Create a namespace object to pass to create_vm
    class Args:
        pass
    
    args = Args()
    args.name = vm_name
    args.model = vm_manager.llm_vm_manager_config.get("llm_model")
    
    # Create the VM
    create_vm(vm_manager, args)
    
    # Yield the VM name to the test
    yield vm_name
    
    # Clean up after the test
    try:
        # Stop the VM if it's running
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            stop_vm(vm_manager, args)
            # Delete the VM
            delete_vm(vm_manager, args)
    except Exception as e:
        print(f"Error cleaning up VM {vm_name}: {e}")

# Test category markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "smoke: mark a test as a smoke test")
    config.addinivalue_line("markers", "sanity: mark a test as a sanity test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "performance: mark a test as a performance test")
    config.addinivalue_line("markers", "security: mark a test as a security test")
    config.addinivalue_line("markers", "regression: mark a test as a regression test")
```

## Test Implementation

Now let's implement the live end-to-end tests for each category.

### Smoke Tests

```python
@pytest.mark.smoke
def test_help_command():
    """
    Test Case ID: S1
    Test that the help command works correctly.
    """
    # Run the application with the --help flag
    result = subprocess.run(["python", "python/main.py", "--help"], capture_output=True, text=True)
    
    # Check that the output contains help information
    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert "Manage LLM VMs for running Large Language Models" in result.stdout

@pytest.mark.smoke
def test_version_command():
    """
    Test Case ID: S2
    Test that the version command works correctly.
    """
    # Run the application with the --version flag
    result = subprocess.run(["python", "python/main.py", "--version"], capture_output=True, text=True)
    
    # Check that the output contains version information
    assert result.returncode == 0
    assert "main.py" in result.stdout
    assert "." in result.stdout  # Version number should contain a dot
```

### Sanity Tests

```python
@pytest.mark.sanity
def test_create_vm(vm_manager):
    """
    Test Case ID: SN1
    Test creating a new VM instance.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-create-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = vm_manager.llm_vm_manager_config.get("llm_model")
        
        # Create the VM
        create_vm(vm_manager, args)
        
        # Check that the VM exists
        assert vm_manager.instance_exists(vm_name)
        
        # Find the zone where the VM was created
        zone = vm_manager.find_instance_zone(vm_name)
        assert zone is not None
        
        # Get the VM's external IP
        vm_ip = vm_manager.get_instance_external_ip(zone, vm_name)
        assert vm_ip is not None
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            stop_vm(vm_manager, args)
            delete_vm(vm_manager, args)

@pytest.mark.sanity
def test_start_vm(vm_manager):
    """
    Test Case ID: SN2
    Test starting an existing VM instance.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-start-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = vm_manager.llm_vm_manager_config.get("llm_model")
        
        # Create the VM
        create_vm(vm_manager, args)
        
        # Stop the VM
        stop_vm(vm_manager, args)
        
        # Start the VM
        start_vm(vm_manager, args)
        
        # Find the zone where the VM was created
        zone = vm_manager.find_instance_zone(vm_name)
        assert zone is not None
        
        # Get the VM's external IP
        vm_ip = vm_manager.get_instance_external_ip(zone, vm_name)
        assert vm_ip is not None
        
        # Check that the VM is running
        instance_info = vm_manager.compute.instances().get(
            project=vm_manager.llm_vm_manager_config.get("gcp.project_id"),
            zone=zone,
            instance=vm_name
        ).execute()
        assert instance_info["status"] == "RUNNING"
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            stop_vm(vm_manager, args)
            delete_vm(vm_manager, args)

@pytest.mark.sanity
def test_stop_vm(vm_manager):
    """
    Test Case ID: SN3
    Test stopping a running VM instance.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-stop-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = vm_manager.llm_vm_manager_config.get("llm_model")
        
        # Create the VM
        create_vm(vm_manager, args)
        
        # Stop the VM
        stop_vm(vm_manager, args)
        
        # Find the zone where the VM was created
        zone = vm_manager.find_instance_zone(vm_name)
        assert zone is not None
        
        # Check that the VM is stopped
        instance_info = vm_manager.compute.instances().get(
            project=vm_manager.llm_vm_manager_config.get("gcp.project_id"),
            zone=zone,
            instance=vm_name
        ).execute()
        assert instance_info["status"] == "TERMINATED"
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            delete_vm(vm_manager, args)

@pytest.mark.sanity
def test_delete_vm(vm_manager):
    """
    Test Case ID: SN4
    Test deleting a VM instance.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-delete-{int(time.time())}"
    
    # Create a namespace object to pass to create_vm
    class Args:
        pass
    
    args = Args()
    args.name = vm_name
    args.model = vm_manager.llm_vm_manager_config.get("llm_model")
    
    # Create the VM
    create_vm(vm_manager, args)
    
    # Delete the VM
    delete_vm(vm_manager, args)
    
    # Check that the VM no longer exists
    assert not vm_manager.instance_exists(vm_name)

@pytest.mark.sanity
def test_ollama_setup(test_vm, vm_manager):
    """
    Test Case ID: SN5
    Test setting up Ollama on a VM.
    """
    # Find the zone where the VM was created
    zone = vm_manager.find_instance_zone(test_vm)
    assert zone is not None
    
    # Get the VM's external IP
    vm_ip = vm_manager.get_instance_external_ip(zone, test_vm)
    assert vm_ip is not None
    
    # Check that Ollama is available
    llm_model = vm_manager.llm_vm_manager_config.get("llm_model")
    assert check_ollama_availability(vm_ip, llm_model)

@pytest.mark.sanity
def test_ollama_model_pull(test_vm, vm_manager):
    """
    Test Case ID: SN6
    Test pulling an LLM model to Ollama.
    """
    # Find the zone where the VM was created
    zone = vm_manager.find_instance_zone(test_vm)
    assert zone is not None
    
    # Get the VM's external IP
    vm_ip = vm_manager.get_instance_external_ip(zone, test_vm)
    assert vm_ip is not None
    
    # Check that the model is available
    llm_model = vm_manager.llm_vm_manager_config.get("llm_model")
    assert check_ollama_availability(vm_ip, llm_model)
    
    # Try to pull another model
    new_model = "orca-mini"
    
    # Load SSH key
    ssh_key_path = vm_manager.llm_vm_manager_config.get("ssh.ssh_secret_key")
    ssh_user = vm_manager.llm_vm_manager_config.get("ssh.user")
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    
    # Connect to the VM
    assert vm_manager.ssh_client.ssh_connect(vm_ip, ssh_user, key)
    
    # Pull the new model
    assert vm_manager.ssh_client.run_ssh_commands([f"ollama pull {new_model}"])
    
    # Disconnect from the VM
    vm_manager.ssh_client.ssh_disconnect()
    
    # Check that the new model is available
    assert check_ollama_availability(vm_ip, new_model)
```

### Integration Tests

```python
@pytest.mark.integration
def test_create_and_start_vm(vm_manager):
    """
    Test Case ID: I1
    Test creating a VM and then starting it.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-create-start-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = vm_manager.llm_vm_manager_config.get("llm_model")
        
        # Create the VM
        create_vm(vm_manager, args)
        
        # Stop the VM
        stop_vm(vm_manager, args)
        
        # Start the VM
        start_vm(vm_manager, args)
        
        # Find the zone where the VM was created
        zone = vm_manager.find_instance_zone(vm_name)
        assert zone is not None
        
        # Get the VM's external IP
        vm_ip = vm_manager.get_instance_external_ip(zone, vm_name)
        assert vm_ip is not None
        
        # Check that the VM is running
        instance_info = vm_manager.compute.instances().get(
            project=vm_manager.llm_vm_manager_config.get("gcp.project_id"),
            zone=zone,
            instance=vm_name
        ).execute()
        assert instance_info["status"] == "RUNNING"
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            stop_vm(vm_manager, args)
            delete_vm(vm_manager, args)

@pytest.mark.integration
def test_start_and_stop_vm(vm_manager):
    """
    Test Case ID: I2
    Test starting a VM and then stopping it.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-start-stop-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = vm_manager.llm_vm_manager_config.get("llm_model")
        
        # Create the VM
        create_vm(vm_manager, args)
        
        # Stop the VM
        stop_vm(vm_manager, args)
        
        # Start the VM
        start_vm(vm_manager, args)
        
        # Find the zone where the VM was created
        zone = vm_manager.find_instance_zone(vm_name)
        assert zone is not None
        
        # Check that the VM is running
        instance_info = vm_manager.compute.instances().get(
            project=vm_manager.llm_vm_manager_config.get("gcp.project_id"),
            zone=zone,
            instance=vm_name
        ).execute()
        assert instance_info["status"] == "RUNNING"
        
        # Stop the VM again
        stop_vm(vm_manager, args)
        
        # Check that the VM is stopped
        instance_info = vm_manager.compute.instances().get(
            project=vm_manager.llm_vm_manager_config.get("gcp.project_id"),
            zone=zone,
            instance=vm_name
        ).execute()
        assert instance_info["status"] == "TERMINATED"
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            delete_vm(vm_manager, args)

@pytest.mark.integration
def test_create_start_delete_vm(vm_manager):
    """
    Test Case ID: I3
    Test creating a VM, starting it, and then deleting it.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-create-start-delete-{int(time.time())}"
    
    # Create a namespace object to pass to create_vm
    class Args:
        pass
    
    args = Args()
    args.name = vm_name
    args.model = vm_manager.llm_vm_manager_config.get("llm_model")
    
    # Create the VM
    create_vm(vm_manager, args)
    
    # Stop the VM
    stop_vm(vm_manager, args)
    
    # Start the VM
    start_vm(vm_manager, args)
    
    # Find the zone where the VM was created
    zone = vm_manager.find_instance_zone(vm_name)
    assert zone is not None
    
    # Get the VM's external IP
    vm_ip = vm_manager.get_instance_external_ip(zone, vm_name)
    assert vm_ip is not None
    
    # Check that the VM is running
    instance_info = vm_manager.compute.instances().get(
        project=vm_manager.llm_vm_manager_config.get("gcp.project_id"),
        zone=zone,
        instance=vm_name
    ).execute()
    assert instance_info["status"] == "RUNNING"
    
    # Delete the VM
    delete_vm(vm_manager, args)
    
    # Check that the VM no longer exists
    assert not vm_manager.instance_exists(vm_name)

@pytest.mark.integration
def test_create_vm_check_ollama(vm_manager):
    """
    Test Case ID: I4
    Test creating a VM and checking if Ollama is available.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-create-ollama-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = vm_manager.llm_vm_manager_config.get("llm_model")
        
        # Create the VM
        create_vm(vm_manager, args)
        
        # Find the zone where the VM was created
        zone = vm_manager.find_instance_zone(vm_name)
        assert zone is not None
        
        # Get the VM's external IP
        vm_ip = vm_manager.get_instance_external_ip(zone, vm_name)
        assert vm_ip is not None
        
        # Check that Ollama is available
        llm_model = vm_manager.llm_vm_manager_config.get("llm_model")
        assert check_ollama_availability(vm_ip, llm_model)
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            stop_vm(vm_manager, args)
            delete_vm(vm_manager, args)

@pytest.mark.integration
def test_create_vm_pull_model_check_model(vm_manager):
    """
    Test Case ID: I5
    Test creating a VM, pulling a model, and checking if the model is available.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-create-pull-check-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = vm_manager.llm_vm_manager_config.get("llm_model")
        
        # Create the VM
        create_vm(vm_manager, args)
        
        # Find the zone where the VM was created
        zone = vm_manager.find_instance_zone(vm_name)
        assert zone is not None
        
        # Get the VM's external IP
        vm_ip = vm_manager.get_instance_external_ip(zone, vm_name)
        assert vm_ip is not None
        
        # Check that the model is available
        llm_model = vm_manager.llm_vm_manager_config.get("llm_model")
        assert check_ollama_availability(vm_ip, llm_model)
        
        # Try to pull another model
        new_model = "orca-mini"
        
        # Load SSH key
        ssh_key_path = vm_manager.llm_vm_manager_config.get("ssh.ssh_secret_key")
        ssh_user = vm_manager.llm_vm_manager_config.get("ssh.user")
        key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
        
        # Connect to the VM
        assert vm_manager.ssh_client.ssh_connect(vm_ip, ssh_user, key)
        
        # Pull the new model
        assert vm_manager.ssh_client.run_ssh_commands([f"ollama pull {new_model}"])
        
        # Disconnect from the VM
        vm_manager.ssh_client.ssh_disconnect()
        
        # Check that the new model is available
        assert check_ollama_availability(vm_ip, new_model)
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            stop_vm(vm_manager, args)
            delete_vm(vm_manager, args)
```

### Performance Tests

```python
@pytest.mark.performance
def test_vm_creation_time(vm_manager):
    """
    Test Case ID: P1
    Measure the time it takes to create a VM.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-creation-time-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = vm_manager.llm_vm_manager_config.get("llm_model")
        
        # Measure the time it takes to create the VM
        start_time = time.time()
        create_vm(vm_manager, args)
        end_time = time.time()
        
        # Calculate the creation time
        creation_time = end_time - start_time
        
        # Log the creation time
        print(f"VM creation time: {creation_time:.2f} seconds")
        
        # Check that the VM exists
        assert vm_manager.instance_exists(vm_name)
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            stop_vm(vm_manager, args)
            delete_vm(vm_manager, args)

@pytest.mark.performance
def test_vm_start_time(vm_manager):
    """
    Test Case ID: P2
    Measure the time it takes to start a VM.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-start-time-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = vm_manager.llm_vm_manager_config.get("llm_model")
        
        # Create the VM
        create_vm(vm_manager, args)
        
        # Stop the VM
        stop_vm(vm_manager, args)
        
        # Measure the time it takes to start the VM
        start_time = time.time()
        start_vm(vm_manager, args)
        end_time = time.time()
        
        # Calculate the start time
        vm_start_time = end_time - start_time
        
        # Log the start time
        print(f"VM start time: {vm_start_time:.2f} seconds")
        
        # Find the zone where the VM was created
        zone = vm_manager.find_instance_zone(vm_name)
        assert zone is not None
        
        # Check that the VM is running
        instance_info = vm_manager.compute.instances().get(
            project=vm_manager.llm_vm_manager_config.get("gcp.project_id"),
            zone=zone,
            instance=vm_name
        ).execute()
        assert instance_info["status"] == "RUNNING"
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            stop_vm(vm_manager, args)
            delete_vm(vm_manager, args)

@pytest.mark.performance
def test_vm_stop_time(vm_manager):
    """
    Test Case ID: P3
    Measure the time it takes to stop a VM.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-stop-time-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = vm_manager.llm_vm_manager_config.get("llm_model")
        
        # Create the VM
        create_vm(vm_manager, args)
        
        # Measure the time it takes to stop the VM
        start_time = time.time()
        stop_vm(vm_manager, args)
        end_time = time.time()
        
        # Calculate the stop time
        vm_stop_time = end_time - start_time
        
        # Log the stop time
        print(f"VM stop time: {vm_stop_time:.2f} seconds")
        
        # Find the zone where the VM was created
        zone = vm_manager.find_instance_zone(vm_name)
        assert zone is not None
        
        # Check that the VM is stopped
        instance_info = vm_manager.compute.instances().get(
            project=vm_manager.llm_vm_manager_config.get("gcp.project_id"),
            zone=zone,
            instance=vm_name
        ).execute()
        assert instance_info["status"] == "TERMINATED"
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            delete_vm(vm_manager, args)

@pytest.mark.performance
def test_vm_deletion_time(vm_manager):
    """
    Test Case ID: P4
    Measure the time it takes to delete a VM.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-deletion-time-{int(time.time())}"
    
    # Create a namespace object to pass to create_vm
    class Args:
        pass
    
    args = Args()
    args.name = vm_name
    args.model = vm_manager.llm_vm_manager_config.get("llm_model")
    
    # Create the VM
    create_vm(vm_manager, args)
    
    # Stop the VM
    stop_vm(vm_manager, args)
    
    # Measure the time it takes to delete the VM
    start_time = time.time()
    delete_vm(vm_manager, args)
    end_time = time.time()
    
    # Calculate the deletion time
    deletion_time = end_time - start_time
    
    # Log the deletion time
    print(f"VM deletion time: {deletion_time:.2f} seconds")
    
    # Check that the VM no longer exists
    assert not vm_manager.instance_exists(vm_name)

@pytest.mark.performance
def test_ollama_setup_time(vm_manager):
    """
    Test Case ID: P5
    Measure the time it takes to set up Ollama.
    """
    # Generate a unique VM name
    vm_name = f"test-vm-ollama-setup-time-{int(time.time())}"
    
    try:
        # Create a namespace object to pass to create_vm
        class Args:
            pass
        
        args = Args()
        args.name = vm_name
        args.model = None  # Don't pull a model yet
        
        # Create the VM without setting up Ollama
        vm_manager.create_instance(vm_name)
        
        # Find the zone where the VM was created
        zone = vm_manager.find_instance_zone(vm_name)
        assert zone is not None
        
        # Get the VM's external IP
        vm_ip = vm_manager.get_instance_external_ip(zone, vm_name)
        assert vm_ip is not None
        
        # Measure the time it takes to set up Ollama
        start_time = time.time()
        llm_model = vm_manager.llm_vm_manager_config.get("llm_model")
        setup_ollama(vm_manager, zone, vm_name, llm_model)
        end_time = time.time()
        
        # Calculate the setup time
        setup_time = end_time - start_time
        
        # Log the setup time
        print(f"Ollama setup time: {setup_time:.2f} seconds")
        
        # Check that Ollama is available
        assert check_ollama_availability(vm_ip, llm_model)
    finally:
        # Clean up
        if vm_manager.instance_exists(vm_name):
            args.name = vm_name
            stop_vm(vm_manager, args)
            delete_vm(vm_manager, args)

@pytest.mark.performance
def test_model_pull_time(test_vm, vm_manager):
    """
    Test Case ID: P6
    Measure the time it takes to pull a model.
    """
    # Find the zone where the VM was created
    zone = vm_manager.find_instance_zone(test_vm)
    assert zone is not None
    
    # Get the VM's external IP
    vm_ip = vm_manager.get_instance_external_ip(zone, test_vm)
    assert vm_ip is not None
    
    # Load SSH key
    ssh_key_path = vm_manager.llm_vm_manager_config.get("ssh.ssh_secret_key")
    ssh_user = vm_manager.llm_vm_manager_config.get("ssh.user")
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    
    # Connect to the VM
    assert vm_manager.ssh_client.ssh_connect(vm_ip, ssh_user, key)
    
    # Choose a model to pull
    new_model = "orca-mini"
    
    # Measure the time it takes to pull the model
    start_time = time.time()
    assert vm_manager.ssh_client.run_ssh_commands([f"ollama pull {new_model}"])
    end_time = time.time()
    
    # Calculate the pull time
    pull_time = end_time - start_time
    
    # Log the pull time
    print(f"Model pull time: {pull_time:.2f} seconds")
    
    # Disconnect from the VM
    vm_manager.ssh_client.ssh_disconnect()
    
    # Check that the model is available
    assert check_ollama_availability(vm_ip, new_model)

@pytest.mark.performance
def test_multiple_vm_creation(vm_manager):
    """
    Test Case ID: P7
    Create multiple VMs and measure the time.
    """
    # Number of VMs to create
    num_vms = 3
    
    # Generate unique VM names
    vm_names = [f"test-vm-multi-{i}-{int(time.time())}" for i in range(num_vms)]
    
    try:
        # Create namespace objects to pass to create_vm
        args_list = []
        for vm_name in vm_names:
            class Args:
                pass
            
            args = Args()
            args.name = vm_name
            args.model = None  # Don't pull a model to save time
            args_list.append(args)
        
        # Measure the time it takes to create multiple VMs
        start_time = time.time()
        for args in args_list:
            vm_manager.create_instance(args.name)
        end_time = time.time()
        
        # Calculate the creation time
        creation_time = end_time - start_time
        
        # Log the creation time
        print(f"Multiple VM creation time ({num_vms} VMs): {creation_time:.2f} seconds")
        
        # Check that all VMs exist
        for vm_name in vm_names:
            assert vm_manager.instance_exists(vm_name)
    finally:
        # Clean up
        for vm_name in vm_names:
            if vm_manager.instance_exists(vm_name):
                class Args:
                    pass
                
                args = Args()
                args.name = vm_name
                stop_vm(vm_manager, args)
                delete_vm(vm_manager, args)
```

### Security Tests

```python
@pytest.mark.security
def test_firewall_rule_effectiveness(test_vm, vm_manager):
    """
    Test Case ID: SE3
    Verify that firewall rules are effective.
    """
    # Find the zone where the VM was created
    zone = vm_manager.find_instance_zone(test_vm)
    assert zone is not None
    
    # Get the VM's external IP
    vm_ip = vm_manager.get_instance_external_ip(zone, test_vm)
    assert vm_ip is not None
    
    # Check that Ollama is available from the current IP
    llm_model = vm_manager.llm_vm_manager_config.get("llm_model")
    assert check_ollama_availability(vm_ip, llm_model)
    
    # TODO: Test that Ollama is not available from a different IP
    # This would require a proxy or a different machine to test from

@pytest.mark.security
def test_secure_ssh_connection(test_vm, vm_manager):
    """
    Test Case ID: SE4
    Verify that SSH connections are secure.
    """
    # Find the zone where the VM was created
    zone = vm_manager.find_instance_zone(test_vm)
    assert zone is not None
    
    # Get the VM's external IP
    vm_ip = vm_manager.get_instance_external_ip(zone, test_vm)
    assert vm_ip is not None
    
    # Load SSH key
    ssh_key_path = vm_manager.llm_vm_manager_config.get("ssh.ssh_secret_key")
    ssh_user = vm_manager.llm_vm_manager_config.get("ssh.user")
    key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    
    # Connect to the VM
    assert vm_manager.ssh_client.ssh_connect(vm_ip, ssh_user, key)
    
    # Check that the connection is using encryption
    transport = vm_manager.ssh_client.client.get_transport()
    assert transport.is_active()
    assert transport.is_authenticated()
    
    # Check the encryption algorithm
    assert "aes" in transport.local_cipher.lower() or "chacha" in transport.local_cipher.lower()
    
    # Disconnect from the VM
    vm_manager.ssh_client.ssh_disconnect()
```

### Regression Tests

```python
@pytest.mark.regression
def test_full_workflow(vm_manager):
    """
    Test Case ID: R1
    Run a full workflow (create, start, stop, delete).
    """
    # Generate a unique VM name
    vm_name = f"test-vm-workflow-{int(time.time())}"
    
    # Create a namespace object to pass to create_vm
    class Args:
        pass
    
    args = Args()
    args.name = vm_name
    args.model = vm_manager.llm_vm_manager_config.get("llm_model")
    
    # Create the VM
    create_vm(vm_manager, args)
    
    # Find the zone where the VM was created
    zone = vm_manager.find_instance_zone(vm_name)
    assert zone is not None
    
    # Get the VM's external IP
    vm_ip = vm_manager.get_instance_external_ip(zone, vm_name)
    assert vm_ip is not None
    
    # Check that Ollama is available
    llm_model = vm_manager.llm_vm_manager_config.get("llm_model")
    assert check_ollama_availability(vm_ip, llm_model)
    
    # Stop the VM
    stop_vm(vm_manager, args)
    
    # Check that the VM is stopped
    instance_info = vm_manager.compute.instances().get(
        project=vm_manager.llm_vm_manager_config.get("gcp.project_id"),
        zone=zone,
        instance=vm_name
    ).execute()
    assert instance_info["status"] == "TERMINATED"
    
    # Start the VM
    start_vm(vm_manager, args)
    
    # Check that the VM is running
    instance_info = vm_manager.compute.instances().get(
        project=vm_manager.llm_vm_manager_config.get("gcp.project_id"),
        zone=zone,
        instance=vm_name
    ).execute()
    assert instance_info["status"] == "RUNNING"
    
    # Get the VM's external IP again (it might have changed)
    vm_ip = vm_manager.get_instance_external_ip(zone, vm_name)
    assert vm_ip is not None
    
    # Check that Ollama is still available
    assert check_ollama_availability(vm_ip, llm_model)
    
    # Delete the VM
    delete_vm(vm_manager, args)
    
    # Check that the VM no longer exists
    assert not vm_manager.instance_exists(vm_name)
```

## Test Execution

To run the tests, you can use the following command:

```bash
cd python
python -m pytest tests/endtoendtests/test_e2e_live.py -v
```

You can also run tests by category:

```bash
# Run smoke tests
python -m pytest tests/endtoendtests/test_e2e_live.py -v -m smoke

# Run sanity tests
python -m pytest tests/endtoendtests/test_e2e_live.py -v -m sanity

# Run integration tests
python -m pytest tests/endtoendtests/test_e2e_live.py -v -m integration

# Run performance tests
python -m pytest tests/endtoendtests/test_e2e_live.py -v -m performance

# Run security tests
python -m pytest tests/endtoendtests/test_e2e_live.py -v -m security

# Run regression tests
python -m pytest tests/endtoendtests/test_e2e_live.py -v -m regression
```

## Test Reporting

Pytest provides built-in reporting capabilities. You can generate HTML reports using the pytest-html plugin:

```bash
# Install the plugin
pip install pytest-html

# Run tests and generate a report
python -m pytest tests/endtoendtests/test_e2e_live.py -v --html=report.html
```

## Best Practices

1. **Use unique VM names**: Always use unique VM names to avoid conflicts with existing VMs.
2. **Clean up resources**: Always clean up resources after tests, even if they fail.
3. **Use fixtures**: Use pytest fixtures to set up and tear down test environments.
4. **Use markers**: Use pytest markers to categorize tests.
5. **Log performance metrics**: Log performance metrics to track changes over time.
6. **Use assertions**: Use assertions to verify that tests are working correctly.
7. **Handle exceptions**: Handle exceptions gracefully to avoid leaving resources in an inconsistent state.
8. **Use timeouts**: Use timeouts to avoid tests hanging indefinitely.
9. **Use parameterization**: Use pytest parameterization to test with different inputs.
10. **Use skip and xfail**: Use pytest skip and xfail to handle known issues.

## Example Tests

See the [Test Implementation](#test-implementation) section for example tests.