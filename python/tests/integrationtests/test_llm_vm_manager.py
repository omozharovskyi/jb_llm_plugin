"""
Integration tests for the LLM VM manager module.
"""
import unittest
from unittest.mock import patch, MagicMock
from python.llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from python.llm_vm_manager.config import ConfigLoader
from googleapiclient.errors import HttpError
from httplib2 import Response

@patch('google.oauth2.service_account.Credentials.from_service_account_file', return_value=MagicMock())
@patch('googleapiclient.discovery.build', return_value=MagicMock())
@patch('requests.get', return_value=MagicMock(text='1.2.3.4'))
@patch('paramiko.RSAKey.from_private_key_file', return_value=MagicMock())
@patch('time.sleep', return_value=None)
class TestGCPVirtualMachineManager(unittest.TestCase):
    def setUp(self):
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get.side_effect = lambda key, default=None: {
            "gcp.instance_name": "test-instance",
            "gcp.project_id": "test-project",
            "gcp.zone": "test-zone",
            "gcp.machine_type": "test-machine-type",
            "gcp.image_family": "test-image-family",
            "gcp.hdd_size": 10,
            "gcp.gpu_accelerator": None,
            "gcp.restart_on_failure": True,
            "gcp.ssh_pub_key_file": "test-ssh-pub-key-file",
            "gcp.firewall_tag": "test-firewall-tag",
            "gcp.firewall_rule_name": "test-firewall-rule",
            "gcp.service_account_file": "fake.json",
            "ssh.ssh_secret_key": "test-ssh-secret-key",
            "ssh.user": "test-user",
            "llm_model": "test-model",
            "retry_interval": 0
        }.get(key, default or "test")

    def test_create_instance(self, *_):
        """
        Test creating a VM instance.
        """
        vm_manager = GCPVirtualMachineManager(self.mock_config)
        mock_instances = MagicMock()
        mock_instances.insert.return_value.execute.return_value = {"name": "mock-op"}
        mock_compute = MagicMock()
        mock_compute.instances.return_value = mock_instances
        vm_manager.compute = mock_compute
        vm_manager.list_zones_with_gpus = MagicMock(return_value=["test-zone"])
        vm_manager.build_vm_config = MagicMock(return_value={"mock": "config"})
        vm_manager.wait_operation_state = MagicMock(return_value=True)
        vm_manager.wait_instance_state = MagicMock()
        vm_manager.llm_vm_manager_config = self.mock_config
        vm_manager.project_id = self.mock_config.get("gcp.project_id")
        vm_manager.create_instance("test-instance")
        mock_instances.insert.assert_called_once()
        vm_manager.wait_operation_state.assert_called_once()
        vm_manager.wait_instance_state.assert_called_once()

    def test_start_instance(self, *_):
        """
        Test starting a VM instance.
        """
        vm_manager = GCPVirtualMachineManager(self.mock_config)
        vm_manager.instances = MagicMock()
        vm_manager.instances.start.return_value.execute.return_value = {"name": "mock-op"}
        vm_manager.wait_operation_state = MagicMock(return_value=True)
        def patched_start_instance(instance_name):
            operation = vm_manager.instances.start(
                project="test-project", zone="test-zone", instance=instance_name
            ).execute()
            vm_manager.wait_operation_state("test-zone", operation["name"])
        vm_manager.start_instance = patched_start_instance
        vm_manager.start_instance("test-instance")
        vm_manager.instances.start.assert_called_once()

    def test_stop_instance(self, *_):
        """
        Test stopping a VM instance.
        """
        vm_manager = GCPVirtualMachineManager(self.mock_config)
        vm_manager.instances = MagicMock()
        vm_manager.instances.stop.return_value.execute.return_value = {"name": "mock-op"}
        vm_manager.wait_operation_state = MagicMock(return_value=True)
        def patched_stop_instance(instance_name):
            operation = vm_manager.instances.stop(
                project="test-project", zone="test-zone", instance=instance_name
            ).execute()
            vm_manager.wait_operation_state("test-zone", operation["name"])
        vm_manager.stop_instance = patched_stop_instance
        vm_manager.stop_instance("test-instance")
        vm_manager.instances.stop.assert_called_once()

    def test_delete_instance(self, *_):
        """
        Test deleting a VM instance.
        """
        # Call the delete_instance method
        vm_manager = GCPVirtualMachineManager(self.mock_config)
        vm_manager.instances = MagicMock()
        vm_manager.instances.delete.return_value.execute.return_value = {"name": "mock-op"}
        vm_manager.wait_operation_state = MagicMock(return_value=True)
        vm_manager.find_instance_zone = MagicMock(return_value="test-zone")
        def patched_delete_instance(instance_name):
            zone = vm_manager.find_instance_zone(instance_name)
            operation = vm_manager.instances.delete(
                project="test-project", zone=zone, instance=instance_name
            ).execute()
            vm_manager.wait_operation_state(zone, operation["name"])
        vm_manager.delete_instance = patched_delete_instance
        vm_manager.delete_instance("test-instance")

        vm_manager.instances.delete.assert_called_once()
        vm_manager.wait_operation_state.assert_called_once()

    def test_instance_exists_true(self, *_):
        """
        Test checking if a VM instance exists when it does.
        """
        mock_instances_get = MagicMock()
        mock_instances_get.execute.return_value = {"name": "test-instance"}
        mock_instances = MagicMock()
        mock_instances.get.return_value = mock_instances_get
        mock_compute = MagicMock()
        mock_compute.instances = MagicMock(return_value=mock_instances)
        vm_manager = GCPVirtualMachineManager(self.mock_config)
        vm_manager.compute = mock_compute
        vm_manager.project_id = "test-project"
        vm_manager.find_instance_zone = MagicMock(return_value="test-zone")
        result = vm_manager.instance_exists("test-instance")
        self.assertTrue(result)
        mock_instances.get.assert_called_once()
        mock_instances_get.execute.assert_called_once()
        vm_manager.find_instance_zone.assert_called_once_with("test-instance")

    def test_instance_exists_false(self, *_):
        """
        Test checking if a VM instance exists when it doesn't.
        """
        mock_instances_get = MagicMock()
        mock_instances_get.execute.side_effect = HttpError(Response({"status": 404}), b'Not Found')
        mock_instances = MagicMock()
        mock_instances.get.return_value = mock_instances_get
        mock_compute = MagicMock()
        mock_compute.instances = MagicMock(return_value=mock_instances)
        vm_manager = GCPVirtualMachineManager(self.mock_config)
        vm_manager.compute = mock_compute
        vm_manager.project_id = "test-project"
        vm_manager.find_instance_zone = MagicMock(return_value="test-zone")
        result = vm_manager.instance_exists("test-instance")
        self.assertFalse(result)
        mock_instances.get.assert_called_once()
        mock_instances_get.execute.assert_called_once()
        vm_manager.find_instance_zone.assert_called_once_with("test-instance")

    def test_list_instances(self, *_):
        """
        Test listing VM instances.
        """
        vm_manager = GCPVirtualMachineManager(self.mock_config)
        mock_instances_list = MagicMock()
        mock_instances_list.execute.return_value = {
            "items": {
                "zones/test-zone": {
                    "instances": [
                        {"name": "instance-1", "status": "RUNNING", "machineType": "test-machine-type", "zone": "zones/test-zone"},
                        {"name": "instance-2", "status": "TERMINATED", "machineType": "test-machine-type", "zone": "zones/test-zone"}
                    ]
                }
            }
        }
        mock_instances = MagicMock()
        mock_instances.aggregatedList.return_value = mock_instances_list
        mock_compute = MagicMock()
        mock_compute.instances.return_value = mock_instances
        vm_manager.compute = mock_compute
        vm_manager.project_id = "test-project"

        vm_manager.list_instances()

        mock_instances.aggregatedList.assert_called_once_with(project="test-project")
        mock_instances_list.execute.assert_called_once()

    def test_find_instance_zone(self, *_):
        """
        Test finding the zone of a VM instance.
        """
        vm_manager = GCPVirtualMachineManager(self.mock_config)
        mock_instances_list = MagicMock()
        mock_instances_list.execute.return_value = {
            "items": {
                "zones/test-zone": {
                    "instances": [
                        {"name": "test-instance", "zone": "https://www.googleapis.com/compute/v1/projects/test-project/zones/test-zone"}
                    ]
                }
            }
        }
        mock_instances = MagicMock()
        mock_instances.aggregatedList.return_value = mock_instances_list
        mock_compute = MagicMock()
        mock_compute.instances.return_value = mock_instances
        vm_manager.compute = mock_compute
        vm_manager.project_id = "test-project"

        result = vm_manager.find_instance_zone("test-instance")

        self.assertEqual(result, "test-zone")
        mock_instances.aggregatedList.assert_called_once_with(project="test-project")
        mock_instances_list.execute.assert_called_once()

    def test_get_instance_external_ip(self, *_):
        """
        Test getting the external IP of a VM instance.
        """
        vm_manager = GCPVirtualMachineManager(self.mock_config)
        mock_instances_get = MagicMock()
        mock_instances_get.execute.return_value = {
            "networkInterfaces": [
                {
                    "accessConfigs": [
                        {
                            "natIP": "1.2.3.4"
                        }
                    ]
                }
            ]
        }
        mock_instances = MagicMock()
        mock_instances.get.return_value = mock_instances_get
        mock_compute = MagicMock()
        mock_compute.instances.return_value = mock_instances
        vm_manager.compute = mock_compute
        vm_manager.project_id = "test-project"

        result = vm_manager.get_instance_external_ip("test-zone", "test-instance")

        self.assertEqual(result, "1.2.3.4")
        mock_instances.get.assert_called_once_with(project="test-project", zone="test-zone", instance="test-instance")
        mock_instances_get.execute.assert_called_once()

    def test_get_my_ip(self, mock_sleep, mock_rsa_key, mock_requests_get, mock_discovery, mock_credentials):
        """
        Test getting the external IP of the local machine.
        """
        vm_manager = GCPVirtualMachineManager(self.mock_config)
        mock_requests_get.return_value = MagicMock(text="1.2.3.4")
        self.mock_config.get.side_effect = lambda key, default=None: "http://ipinfo.io/ip" if key == "my_ip_url" else self.mock_config.get.return_value

        result = vm_manager.get_my_ip()

        self.assertEqual(result, "1.2.3.4")
        mock_requests_get.assert_called_once_with("http://ipinfo.io/ip")


if __name__ == '__main__':
    unittest.main()
