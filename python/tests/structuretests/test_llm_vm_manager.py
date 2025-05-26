import unittest
from unittest.mock import patch, MagicMock, call
import requests
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.llm_vm_base import LLMVirtualMachineManager
from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from llm_vm_manager.ssh_client import SSHClient


class TestLLMVirtualMachineManager(unittest.TestCase):
    """Test cases for the LLMVirtualMachineManager base class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a concrete subclass for testing the abstract base class
        class ConcreteLLMVirtualMachineManager(LLMVirtualMachineManager):
            def create_instance(self, name):
                pass

            def start_instance(self, name):
                pass

            def stop_instance(self, name):
                pass

            def delete_instance(self, name):
                pass

            def list_instances(self):
                pass

        # Create mock objects
        self.mock_config = MagicMock(spec=ConfigLoader)

        # Create an instance of the concrete subclass
        self.vm_manager = ConcreteLLMVirtualMachineManager(self.mock_config)

    def tearDown(self):
        """Clean up after tests."""
        # Clean up resources
        if hasattr(self, 'vm_manager') and self.vm_manager:
            if hasattr(self.vm_manager, 'ssh_client') and self.vm_manager.ssh_client:
                self.vm_manager.ssh_client.ssh_disconnect()
            self.vm_manager = None

    def test_init(self):
        """Test initialization of LLMVirtualMachineManager."""
        self.assertEqual(self.vm_manager.llm_vm_manager_config, self.mock_config)
        self.assertIsNotNone(self.vm_manager.ssh_manager)
        self.assertIsNotNone(self.vm_manager.ssh_client)

    @patch('requests.get')
    def test_get_my_ip(self, mock_requests_get):
        """Test get_my_ip method."""
        # Set up mocks
        mock_response = MagicMock()
        mock_response.text = "192.168.1.1"
        mock_requests_get.return_value = mock_response
        self.mock_config.get.return_value = "https://api.ipify.org"

        # Call the method
        result = self.vm_manager.get_my_ip()

        # Verify the results
        self.assertEqual(result, "192.168.1.1")
        self.mock_config.get.assert_called_once_with("my_ip_url")
        mock_requests_get.assert_called_once_with("https://api.ipify.org")

    @patch('requests.get')
    def test_check_ollama_model_available_success(self, mock_requests_get):
        """Test check_ollama_model_available when model is available."""
        # Set up mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2"}
            ]
        }
        mock_requests_get.return_value = mock_response

        # Call the method
        result = self.vm_manager.check_ollama_model_available("192.168.1.1", "llama2")

        # Verify the results
        self.assertTrue(result)
        mock_requests_get.assert_called_once_with(
            "http://192.168.1.1:11434/api/tags", timeout=5
        )

    @patch('requests.get')
    def test_check_ollama_model_available_model_not_found(self, mock_requests_get):
        """Test check_ollama_model_available when model is not found."""
        # Set up mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "other-model"}
            ]
        }
        mock_requests_get.return_value = mock_response

        # Call the method
        result = self.vm_manager.check_ollama_model_available("192.168.1.1", "llama2")

        # Verify the results
        self.assertFalse(result)
        mock_requests_get.assert_called_once_with(
            "http://192.168.1.1:11434/api/tags", timeout=5
        )

    @patch('requests.get')
    def test_check_ollama_model_available_error_status(self, mock_requests_get):
        """Test check_ollama_model_available when API returns error status."""
        # Set up mocks
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests_get.return_value = mock_response

        # Call the method
        result = self.vm_manager.check_ollama_model_available("192.168.1.1", "llama2")

        # Verify the results
        self.assertFalse(result)
        mock_requests_get.assert_called_once_with(
            "http://192.168.1.1:11434/api/tags", timeout=5
        )

    @patch('requests.get')
    def test_check_ollama_model_available_connection_error(self, mock_requests_get):
        """Test check_ollama_model_available when connection fails."""
        # Set up mocks
        mock_requests_get.side_effect = requests.RequestException("Connection error")

        # Call the method
        result = self.vm_manager.check_ollama_model_available("192.168.1.1", "llama2")

        # Verify the results
        self.assertFalse(result)
        mock_requests_get.assert_called_once_with(
            "http://192.168.1.1:11434/api/tags", timeout=5
        )


class TestGCPVirtualMachineManager(unittest.TestCase):
    """Test cases for the GCPVirtualMachineManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock objects
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_compute = MagicMock()
        self.mock_service_account = MagicMock()

        # Set up default return values
        self.mock_config.get.side_effect = lambda key, default=None: {
            "gcp.project_id": "test-project",
            "gcp.project_name": "test-project",
            "gcp.zone": "us-central1-a",
            "gcp.machine_type": "n1-standard-1",
            "gcp.service_account_file": "/path/to/sa.json",
            "gcp.sa_gcp_key": "/path/to/sa.json",
            "gcp.image_project": "ubuntu-os-cloud",
            "gcp.image_family": "ubuntu-2204-lts",
            "gcp.disk_size_gb": 10,
            "gcp.network": "default",
            "gcp.firewall_tag": "ollama-server",
            "ssh.ssh_public_key": "/path/to/ssh.pub",
            "ssh.user": "testuser"
        }.get(key, default)

        # Patch the service account and discovery imports
        patcher1 = patch('google.oauth2.service_account.Credentials.from_service_account_file')
        patcher2 = patch('googleapiclient.discovery.build')
        self.mock_from_service_account_file = patcher1.start()
        self.mock_build = patcher2.start()

        # Set up return values for the patched functions
        self.mock_from_service_account_file.return_value = self.mock_service_account
        self.mock_build.return_value = self.mock_compute

        # Create an instance of GCPVirtualMachineManager
        self.gcp_vm_manager = GCPVirtualMachineManager(self.mock_config)

        # Add cleanup
        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)

    def tearDown(self):
        """Clean up after tests."""
        # Clean up resources
        if hasattr(self, 'gcp_vm_manager') and self.gcp_vm_manager:
            if hasattr(self.gcp_vm_manager, 'ssh_client') and self.gcp_vm_manager.ssh_client:
                self.gcp_vm_manager.ssh_client.ssh_disconnect()
            self.gcp_vm_manager = None

    def test_init(self):
        """Test initialization of GCPVirtualMachineManager."""
        # Verify the results
        self.assertEqual(self.gcp_vm_manager.llm_vm_manager_config, self.mock_config)
        self.assertIsNotNone(self.gcp_vm_manager.ssh_manager)
        self.assertIsNotNone(self.gcp_vm_manager.ssh_client)
        self.mock_from_service_account_file.assert_called_once_with(
            "/path/to/sa.json",
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        self.mock_build.assert_called_once_with('compute', 'v1', credentials=self.mock_service_account)

    @patch('llm_vm_manager.llm_vm_gcp.GCPVirtualMachineManager.build_vm_config')
    @patch('llm_vm_manager.llm_vm_gcp.GCPVirtualMachineManager.wait_operation_state')
    @patch('llm_vm_manager.llm_vm_gcp.GCPVirtualMachineManager.list_zones_with_gpus')
    def test_create_instance(self, mock_list_zones, mock_wait_operation, mock_build_vm_config):
        """Test create_instance method."""
        # Set up mocks
        mock_list_zones.return_value = ["us-central1-a"]
        mock_build_vm_config.return_value = {"name": "test-instance"}
        mock_operation = {"name": "operation-1"}
        mock_instances = self.mock_compute.instances.return_value
        mock_insert = mock_instances.insert.return_value
        mock_insert.execute.return_value = mock_operation
        mock_wait_operation.return_value = True

        # Call the method
        self.gcp_vm_manager.create_instance("test-instance")

        # Verify the results
        mock_list_zones.assert_called_once_with('nvidia-tesla-t4')
        mock_build_vm_config.assert_called_once()
        mock_instances.insert.assert_called_once_with(
            project="test-project",
            zone="us-central1-a",
            body={"name": "test-instance"}
        )
        mock_insert.execute.assert_called_once()
        mock_wait_operation.assert_called_once_with(
            "us-central1-a", "operation-1", 
            ["DONE"], ["PENDING", "RUNNING"], ["STOPPED"], None
        )

    @patch('llm_vm_manager.llm_vm_gcp.GCPVirtualMachineManager.wait_operation_state')
    def test_start_instance(self, mock_wait_operation):
        """Test start_instance method."""
        # Set up mocks
        mock_operation = {"name": "operation-1"}
        mock_instances = self.mock_compute.instances.return_value
        mock_start = mock_instances.start.return_value
        mock_start.execute.return_value = mock_operation
        mock_wait_operation.return_value = True

        # Call the method
        self.gcp_vm_manager.start_instance("test-instance")

        # Verify the results
        mock_instances.start.assert_called_once_with(
            project="test-project",
            zone="us-central1-a",
            instance="test-instance"
        )
        mock_start.execute.assert_called_once()
        mock_wait_operation.assert_called_once_with(
            "us-central1-a", "operation-1", 
            ["DONE"], ["PENDING", "RUNNING"], ["STOPPED"], None
        )

    @patch('llm_vm_manager.llm_vm_gcp.GCPVirtualMachineManager.wait_operation_state')
    def test_stop_instance(self, mock_wait_operation):
        """Test stop_instance method."""
        # Set up mocks
        mock_operation = {"name": "operation-1"}
        mock_instances = self.mock_compute.instances.return_value
        mock_stop = mock_instances.stop.return_value
        mock_stop.execute.return_value = mock_operation
        mock_wait_operation.return_value = True

        # Call the method
        self.gcp_vm_manager.stop_instance("test-instance")

        # Verify the results
        mock_instances.stop.assert_called_once_with(
            project="test-project",
            zone="us-central1-a",
            instance="test-instance"
        )
        mock_stop.execute.assert_called_once()
        mock_wait_operation.assert_called_once_with(
            "us-central1-a", "operation-1", 
            ["DONE"], ["PENDING", "RUNNING"], ["STOPPED"], None
        )

    @patch('llm_vm_manager.llm_vm_gcp.GCPVirtualMachineManager.wait_operation_state')
    def test_delete_instance(self, mock_wait_operation):
        """Test delete_instance method."""
        # Set up mocks
        mock_operation = {"name": "operation-1"}
        mock_instances = self.mock_compute.instances.return_value
        mock_delete = mock_instances.delete.return_value
        mock_delete.execute.return_value = mock_operation
        mock_wait_operation.return_value = True

        # Call the method
        self.gcp_vm_manager.delete_instance("test-instance")

        # Verify the results
        mock_instances.delete.assert_called_once_with(
            project="test-project",
            zone="us-central1-a",
            instance="test-instance"
        )
        mock_delete.execute.assert_called_once()
        mock_wait_operation.assert_called_once_with(
            "us-central1-a", "operation-1", 
            ["DONE"], ["PENDING", "RUNNING"], ["STOPPED"], None
        )

    def test_instance_exists_true(self):
        """Test instance_exists method when instance exists."""
        # Set up mocks
        mock_instances = self.mock_compute.instances.return_value
        mock_list = mock_instances.list.return_value
        mock_list.execute.return_value = {
            "items": [
                {"name": "other-instance"},
                {"name": "test-instance"}
            ]
        }

        # Call the method
        result = self.gcp_vm_manager.instance_exists("test-instance")

        # Verify the results
        self.assertTrue(result)
        mock_instances.list.assert_called_once_with(
            project="test-project",
            filter=f"name=test-instance"
        )
        mock_list.execute.assert_called_once()

    def test_instance_exists_false(self):
        """Test instance_exists method when instance does not exist."""
        # Set up mocks
        mock_instances = self.mock_compute.instances.return_value
        mock_list = mock_instances.list.return_value
        mock_list.execute.return_value = {
            "items": [
                {"name": "other-instance"}
            ]
        }

        # Call the method
        result = self.gcp_vm_manager.instance_exists("test-instance")

        # Verify the results
        self.assertFalse(result)
        mock_instances.list.assert_called_once_with(
            project="test-project",
            filter=f"name=test-instance"
        )
        mock_list.execute.assert_called_once()

    def test_instance_exists_no_items(self):
        """Test instance_exists method when no instances exist."""
        # Set up mocks
        mock_instances = self.mock_compute.instances.return_value
        mock_list = mock_instances.list.return_value
        mock_list.execute.return_value = {}

        # Call the method
        result = self.gcp_vm_manager.instance_exists("test-instance")

        # Verify the results
        self.assertFalse(result)
        mock_instances.list.assert_called_once_with(
            project="test-project",
            filter=f"name=test-instance"
        )
        mock_list.execute.assert_called_once()

    def test_list_instances(self):
        """Test list_instances method."""
        # Set up mocks
        mock_instances = self.mock_compute.instances.return_value
        mock_list = mock_instances.list.return_value
        mock_list.execute.return_value = {
            "items": [
                {
                    "name": "instance-1",
                    "status": "RUNNING",
                    "networkInterfaces": [{"accessConfigs": [{"natIP": "192.168.1.1"}]}]
                },
                {
                    "name": "instance-2",
                    "status": "TERMINATED",
                    "networkInterfaces": [{"accessConfigs": [{"natIP": "192.168.1.2"}]}]
                }
            ]
        }

        # Call the method
        self.gcp_vm_manager.list_instances()

        # Verify the results
        mock_instances.list.assert_called_once_with(
            project="test-project",
            filter=""
        )
        mock_list.execute.assert_called_once()

    def test_find_instance_zone(self):
        """Test find_instance_zone method."""
        # Set up mocks
        mock_zones = self.mock_compute.zones.return_value
        mock_list = mock_zones.list.return_value
        mock_list.execute.return_value = {
            "items": [
                {"name": "us-central1-a"},
                {"name": "us-central1-b"}
            ]
        }

        mock_instances = self.mock_compute.instances.return_value
        mock_list_instances = mock_instances.list.return_value
        mock_list_instances.execute.side_effect = [
            {},  # No instances in first zone
            {
                "items": [
                    {"name": "test-instance"}
                ]
            }  # Instance found in second zone
        ]

        # Call the method
        result = self.gcp_vm_manager.find_instance_zone("test-instance")

        # Verify the results
        self.assertEqual(result, "us-central1-b")
        mock_zones.list.assert_called_once_with(
            project="test-project"
        )
        mock_list.execute.assert_called_once()
        self.assertEqual(mock_instances.list.call_count, 2)
        mock_instances.list.assert_has_calls([
            call(project="test-project", zone="us-central1-a", filter="name=test-instance"),
            call(project="test-project", zone="us-central1-b", filter="name=test-instance")
        ])
        self.assertEqual(mock_list_instances.execute.call_count, 2)

    def test_get_instance_external_ip(self):
        """Test get_instance_external_ip method."""
        # Set up mocks
        mock_instances = self.mock_compute.instances.return_value
        mock_get = mock_instances.get.return_value
        mock_get.execute.return_value = {
            "networkInterfaces": [
                {
                    "accessConfigs": [
                        {"natIP": "192.168.1.1"}
                    ]
                }
            ]
        }

        # Call the method
        result = self.gcp_vm_manager.get_instance_external_ip("us-central1-a", "test-instance")

        # Verify the results
        self.assertEqual(result, "192.168.1.1")
        mock_instances.get.assert_called_once_with(
            project="test-project",
            zone="us-central1-a",
            instance="test-instance"
        )
        mock_get.execute.assert_called_once()


if __name__ == '__main__':
    unittest.main()
