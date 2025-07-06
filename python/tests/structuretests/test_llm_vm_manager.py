import unittest
from unittest.mock import patch, MagicMock, call
import requests
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.llm_vm_base import LLMVirtualMachineManager
from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager


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
    def setUp(self):
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_compute = MagicMock()
        self.mock_credentials = MagicMock()

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

        patcher1 = patch('google.oauth2.service_account.Credentials.from_service_account_file', return_value=self.mock_credentials)
        patcher2 = patch('googleapiclient.discovery.build', return_value=self.mock_compute)

        self.mock_creds_patch = patcher1.start()
        self.mock_build_patch = patcher2.start()

        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)

        self.manager = GCPVirtualMachineManager(self.mock_config)

    @patch.object(GCPVirtualMachineManager, 'build_vm_config')
    @patch.object(GCPVirtualMachineManager, 'wait_operation_state', return_value=True)
    @patch.object(GCPVirtualMachineManager, 'list_zones_with_gpus', return_value=["us-central1-a"])
    @patch.object(GCPVirtualMachineManager, 'wait_instance_state')
    def test_create_instance(self, mock_wait_instance, mock_list_zones, mock_wait_op, mock_build_config):
        self.mock_compute.instances.return_value.insert.return_value.execute.return_value = {"name": "op-123"}
        mock_build_config.return_value = {"name": "test-instance"}
        self.manager.create_instance("test-instance")
        self.mock_compute.instances.return_value.insert.assert_called_once()

    @patch.object(GCPVirtualMachineManager, 'wait_operation_state', return_value=True)
    @patch.object(GCPVirtualMachineManager, 'find_instance_zone', return_value="us-central1-a")
    @patch.object(GCPVirtualMachineManager, 'wait_instance_state')
    def test_start_instance(self, mock_wait_instance, mock_find_zone, mock_wait_op):
        self.mock_compute.instances.return_value.start.return_value.execute.return_value = {"name": "op-456"}
        self.manager.start_instance("test-instance")
        self.mock_compute.instances.return_value.start.assert_called_once()

    @patch.object(GCPVirtualMachineManager, 'wait_operation_state', return_value=True)
    @patch.object(GCPVirtualMachineManager, 'find_instance_zone', return_value="us-central1-a")
    @patch.object(GCPVirtualMachineManager, 'wait_instance_state')
    def test_stop_instance(self, mock_wait_instance, mock_find_zone, mock_wait_op):
        self.mock_compute.instances.return_value.stop.return_value.execute.return_value = {"name": "op-789"}
        self.manager.stop_instance("test-instance")
        self.mock_compute.instances.return_value.stop.assert_called_once()

    @patch.object(GCPVirtualMachineManager, 'wait_operation_state', return_value=True)
    @patch.object(GCPVirtualMachineManager, 'wait_instance_state')
    @patch.object(GCPVirtualMachineManager, 'instance_exists', return_value=True)
    @patch.object(GCPVirtualMachineManager, 'find_instance_zone', return_value="us-central1-a")
    def test_delete_instance(self, mock_find_zone, mock_exists, mock_wait_op, mock_wait_instance):
        self.mock_compute.instances.return_value.delete.return_value.execute.return_value = {"name": "op-101"}
        self.manager.delete_instance("test-instance")
        self.mock_compute.instances.return_value.delete.assert_called_once()

    def test_instance_exists_true(self):
        self.mock_compute.instances.return_value.get.return_value.execute.return_value = {}
        with patch.object(self.manager, 'find_instance_zone', return_value="us-central1-a"):
            self.assertTrue(self.manager.instance_exists("test-instance"))

    def test_instance_exists_false(self):
        self.mock_compute.instances.return_value.get.return_value.execute.side_effect = Exception()
        with patch.object(self.manager, 'find_instance_zone', return_value=None):
            self.assertFalse(self.manager.instance_exists("test-instance"))

    def test_get_instance_external_ip(self):
        self.mock_compute.instances.return_value.get.return_value.execute.return_value = {
            "networkInterfaces": [{"accessConfigs": [{"natIP": "1.2.3.4"}]}]
        }
        ip = self.manager.get_instance_external_ip("us-central1-a", "test-instance")
        self.assertEqual(ip, "1.2.3.4")

    def test_list_instances(self):
        self.mock_compute.instances.return_value.aggregatedList.return_value.execute.return_value = {
            "items": {
                "zones/us-central1-a": {
                    "instances": [
                        {"name": "test-instance", "status": "RUNNING",
                         "machineType": "zones/us-central1-a/machineTypes/n1-standard-1",
                         "zone": "zones/us-central1-a"}
                    ]
                }
            }
        }
        self.manager.list_instances()

    def test_find_instance_zone(self):
        self.mock_compute.instances.return_value.aggregatedList.return_value.execute.return_value = {
            "items": {
                "zones/us-central1-a": {
                    "instances": [{"name": "test-instance", "zone": "zones/us-central1-a"}]
                }
            }
        }
        zone = self.manager.find_instance_zone("test-instance")
        self.assertEqual(zone, "us-central1-a")


if __name__ == '__main__':
    unittest.main()
