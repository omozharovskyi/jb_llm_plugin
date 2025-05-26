"""
Pytest fixtures for mocked end-to-end tests.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List, Optional

# Add the parent directory to the path so we can import the application modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from tests.memory_leak_detector import MemoryLeakDetector, detect_leaks, memory_usage_decorator
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from llm_vm_manager.ssh_client import SSHClient

# Add the python directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


# Test categories
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "smoke: smoke tests")
    config.addinivalue_line("markers", "sanity: sanity tests")
    config.addinivalue_line("markers", "functional: functional tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "negative: negative tests")
    config.addinivalue_line("markers", "security: security tests")
    config.addinivalue_line("markers", "regression: regression tests")


# Memory leak detection fixture
@pytest.fixture
def memory_leak_detector():
    """Fixture for memory leak detection."""
    with MemoryLeakDetector(threshold_kb=100) as detector:
        yield detector
        detector.check_leaks()


# Mock configuration
@pytest.fixture
def mock_config():
    """Fixture for mocked configuration."""
    # Create a real ConfigLoader instance with a mock config_file attribute
    config = MagicMock()

    # Set up default configuration values
    config_values = {
        "gcp.project_name": "test-project",
        "gcp.instance_name": "test-vm",
        "gcp.zone": "us-central1-a",
        "gcp.machine_type": "n1-standard-1",
        "gcp.image_family": "ubuntu-2204-lts",
        "gcp.hdd_size": 10,
        "gcp.gpu_accelerator": "nvidia-tesla-t4",
        "gcp.restart_on_failure": True,
        "gcp.ssh_pub_key": "/path/to/ssh/key.pub",
        "gcp.firewall_tag": "ollama-server",
        "gcp.firewall_rule_name": "allow-ollama-api-from-my-ip",
        "gcp.sa_gcp_key": "/path/to/service-account-key.json",
        "ssh.ssh_secret_key": "/path/to/ssh/key",
        "ssh.user": "test-user",
        "llm_model": "llama2",
        "retry_interval": 5,
        "log_level": "INFO"
    }

    def get_side_effect(key, default=None):
        return config_values.get(key, default)

    config.get.side_effect = get_side_effect
    config.config_file = "test_config.toml"

    # Add any other methods or attributes needed
    config.get_section.return_value = {}

    return config


# Mock SSH client
@pytest.fixture
def mock_ssh_client():
    """Fixture for mocked SSH client."""
    ssh_client = MagicMock(spec=SSHClient)

    # Set up default behavior
    ssh_client.ssh_connect.return_value = True
    ssh_client.run_ssh_commands.return_value = True
    ssh_client.ssh_disconnect.return_value = None
    ssh_client.remove_known_host.return_value = None

    return ssh_client


# Mock GCP VM manager
@pytest.fixture
def mock_vm_manager(mock_config, mock_ssh_client):
    """Fixture for mocked GCP VM manager."""
    with patch('llm_vm_manager.llm_vm_gcp.discovery'), \
         patch('llm_vm_manager.llm_vm_gcp.service_account'):

        vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        vm_manager.llm_vm_manager_config = mock_config
        vm_manager.ssh_client = mock_ssh_client
        vm_manager.project_id = "test-project"

        # Set up default behavior
        vm_manager.create_instance.return_value = None
        vm_manager.start_instance.return_value = None
        vm_manager.stop_instance.return_value = None
        vm_manager.delete_instance.return_value = None
        vm_manager.list_instances.return_value = None
        vm_manager.instance_exists.return_value = False
        vm_manager.find_instance_zone.return_value = "us-central1-a"
        vm_manager.get_instance_external_ip.return_value = "192.168.1.1"
        vm_manager.set_firewall_ollama_rule.return_value = None
        vm_manager.get_my_ip.return_value = "127.0.0.1"

        return vm_manager


# Mock requests for Ollama API
@pytest.fixture
def mock_requests():
    """Fixture for mocked requests module."""
    with patch('ollama_utils.requests') as mock_req:
        # Set up default behavior for Ollama API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "mistral"}
            ]
        }
        mock_req.get.return_value = mock_response

        yield mock_req


# Mock command-line arguments
@pytest.fixture
def mock_args():
    """Fixture for mocked command-line arguments."""
    args = MagicMock()
    args.config_file = "test_config.toml"
    args.verbose = 0
    args.command = None
    args.name = None
    args.model = None

    return args


# Mock parser
@pytest.fixture
def mock_parser():
    """Fixture for mocked argument parser."""
    parser = MagicMock()
    parser.print_help.return_value = None

    return parser
