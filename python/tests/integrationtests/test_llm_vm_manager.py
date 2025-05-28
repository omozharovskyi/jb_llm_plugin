"""
Integration tests for the LLM VM manager module.
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from python.llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from python.llm_vm_manager.config import ConfigLoader


class TestGCPVirtualMachineManager(unittest.TestCase):
    """
    Integration tests for the GCPVirtualMachineManager class.
    """
    
    def setUp(self):
        """
        Set up the test environment.
        Create mock objects and patch functions that would interact with external services.
        """
        # Create a mock config
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
            "gcp.service_account_file": "test-service-account-file",
            "ssh.ssh_secret_key": "test-ssh-secret-key",
            "ssh.user": "test-user",
            "llm_model": "test-model"
        }.get(key, default or "test_value")
        
        # Patch the service_account.Credentials.from_service_account_file function
        self.credentials_patch = patch('google.oauth2.service_account.Credentials.from_service_account_file')
        self.mock_credentials = self.credentials_patch.start()
        
        # Patch the discovery.build function
        self.discovery_build_patch = patch('googleapiclient.discovery.build')
        self.mock_discovery_build = self.discovery_build_patch.start()
        
        # Create mock compute service
        self.mock_compute = MagicMock()
        self.mock_discovery_build.return_value = self.mock_compute
        
        # Create mock instances, zones, and operations resources
        self.mock_instances = MagicMock()
        self.mock_zones = MagicMock()
        self.mock_operations = MagicMock()
        self.mock_firewalls = MagicMock()
        
        # Configure the mock compute service
        self.mock_compute.instances = self.mock_instances
        self.mock_compute.zones = self.mock_zones
        self.mock_compute.zoneOperations = self.mock_operations
        self.mock_compute.firewalls = self.mock_firewalls
        
        # Configure the mock instances resource
        self.mock_instances_insert = MagicMock()
        self.mock_instances_start = MagicMock()
        self.mock_instances_stop = MagicMock()
        self.mock_instances_delete = MagicMock()
        self.mock_instances_list = MagicMock()
        self.mock_instances_get = MagicMock()
        
        self.mock_instances.insert = MagicMock(return_value=self.mock_instances_insert)
        self.mock_instances.start = MagicMock(return_value=self.mock_instances_start)
        self.mock_instances.stop = MagicMock(return_value=self.mock_instances_stop)
        self.mock_instances.delete = MagicMock(return_value=self.mock_instances_delete)
        self.mock_instances.list = MagicMock(return_value=self.mock_instances_list)
        self.mock_instances.get = MagicMock(return_value=self.mock_instances_get)
        
        # Configure the mock operations resource
        self.mock_operations_get = MagicMock()
        self.mock_operations.get = MagicMock(return_value=self.mock_operations_get)
        
        # Configure the mock firewalls resource
        self.mock_firewalls_list = MagicMock()
        self.mock_firewalls_insert = MagicMock()
        self.mock_firewalls_update = MagicMock()
        
        self.mock_firewalls.list = MagicMock(return_value=self.mock_firewalls_list)
        self.mock_firewalls.insert = MagicMock(return_value=self.mock_firewalls_insert)
        self.mock_firewalls.update = MagicMock(return_value=self.mock_firewalls_update)
        
        # Configure the execute methods
        self.mock_instances_insert.execute = MagicMock(return_value={"name": "test-operation"})
        self.mock_instances_start.execute = MagicMock(return_value={"name": "test-operation"})
        self.mock_instances_stop.execute = MagicMock(return_value={"name": "test-operation"})
        self.mock_instances_delete.execute = MagicMock(return_value={"name": "test-operation"})
        self.mock_instances_list.execute = MagicMock(return_value={"items": []})
        self.mock_instances_get.execute = MagicMock(return_value={"status": "RUNNING", "networkInterfaces": [{"accessConfigs": [{"natIP": "1.2.3.4"}]}]})
        self.mock_operations_get.execute = MagicMock(return_value={"status": "DONE"})
        self.mock_firewalls_list.execute = MagicMock(return_value={"items": []})
        self.mock_firewalls_insert.execute = MagicMock(return_value={"name": "test-operation"})
        self.mock_firewalls_update.execute = MagicMock(return_value={"name": "test-operation"})
        
        # Patch the requests.get function for get_my_ip
        self.requests_get_patch = patch('requests.get')
        self.mock_requests_get = self.requests_get_patch.start()
        self.mock_requests_get.return_value.text = "1.2.3.4"
        
        # Patch the paramiko.RSAKey.from_private_key_file function
        self.rsa_key_patch = patch('paramiko.RSAKey.from_private_key_file')
        self.mock_rsa_key = self.rsa_key_patch.start()
        
        # Create the VM manager
        self.vm_manager = GCPVirtualMachineManager(self.mock_config)
        
        # Patch the wait_operation_state and wait_instance_state methods
        self.wait_operation_state_patch = patch.object(self.vm_manager, 'wait_operation_state')
        self.mock_wait_operation_state = self.wait_operation_state_patch.start()
        self.mock_wait_operation_state.return_value = True
        
        self.wait_instance_state_patch = patch.object(self.vm_manager, 'wait_instance_state')
        self.mock_wait_instance_state = self.wait_instance_state_patch.start()
        self.mock_wait_instance_state.return_value = True
    
    def tearDown(self):
        """
        Clean up after the test.
        Stop all patches to avoid affecting other tests.
        """
        # Stop all patches
        self.credentials_patch.stop()
        self.discovery_build_patch.stop()
        self.requests_get_patch.stop()
        self.rsa_key_patch.stop()
        self.wait_operation_state_patch.stop()
        self.wait_instance_state_patch.stop()
    
    def test_create_instance(self):
        """
        Test creating a VM instance.
        """
        # Call the create_instance method
        self.vm_manager.create_instance("test-instance")
        
        # Verify that the expected methods were called
        self.mock_instances.insert.assert_called_once()
        self.mock_instances_insert.execute.assert_called_once()
        self.mock_wait_operation_state.assert_called_once()
    
    def test_start_instance(self):
        """
        Test starting a VM instance.
        """
        # Call the start_instance method
        self.vm_manager.start_instance("test-instance")
        
        # Verify that the expected methods were called
        self.mock_instances.start.assert_called_once()
        self.mock_instances_start.execute.assert_called_once()
        self.mock_wait_operation_state.assert_called_once()
    
    def test_stop_instance(self):
        """
        Test stopping a VM instance.
        """
        # Call the stop_instance method
        self.vm_manager.stop_instance("test-instance")
        
        # Verify that the expected methods were called
        self.mock_instances.stop.assert_called_once()
        self.mock_instances_stop.execute.assert_called_once()
        self.mock_wait_operation_state.assert_called_once()
    
    def test_delete_instance(self):
        """
        Test deleting a VM instance.
        """
        # Call the delete_instance method
        self.vm_manager.delete_instance("test-instance")
        
        # Verify that the expected methods were called
        self.mock_instances.delete.assert_called_once()
        self.mock_instances_delete.execute.assert_called_once()
        self.mock_wait_operation_state.assert_called_once()
    
    def test_instance_exists_true(self):
        """
        Test checking if a VM instance exists when it does.
        """
        # Configure the mock instances_list.execute to return an instance
        self.mock_instances_list.execute.return_value = {
            "items": [{"name": "test-instance"}]
        }
        
        # Call the instance_exists method
        result = self.vm_manager.instance_exists("test-instance")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_instances.list.assert_called_once()
        self.mock_instances_list.execute.assert_called_once()
        self.assertTrue(result)
    
    def test_instance_exists_false(self):
        """
        Test checking if a VM instance exists when it doesn't.
        """
        # Configure the mock instances_list.execute to return no instances
        self.mock_instances_list.execute.return_value = {
            "items": []
        }
        
        # Call the instance_exists method
        result = self.vm_manager.instance_exists("test-instance")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_instances.list.assert_called_once()
        self.mock_instances_list.execute.assert_called_once()
        self.assertFalse(result)
    
    def test_list_instances(self):
        """
        Test listing VM instances.
        """
        # Configure the mock instances_list.execute to return some instances
        self.mock_instances_list.execute.return_value = {
            "items": [
                {"name": "instance-1", "status": "RUNNING"},
                {"name": "instance-2", "status": "TERMINATED"}
            ]
        }
        
        # Call the list_instances method
        self.vm_manager.list_instances()
        
        # Verify that the expected methods were called
        self.mock_instances.list.assert_called_once()
        self.mock_instances_list.execute.assert_called_once()
    
    def test_find_instance_zone(self):
        """
        Test finding the zone of a VM instance.
        """
        # Configure the mock instances_list.execute to return an instance in a specific zone
        self.mock_instances_list.execute.return_value = {
            "items": [
                {"name": "test-instance", "zone": "https://www.googleapis.com/compute/v1/projects/test-project/zones/test-zone"}
            ]
        }
        
        # Call the find_instance_zone method
        result = self.vm_manager.find_instance_zone("test-instance")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_instances.list.assert_called_once()
        self.mock_instances_list.execute.assert_called_once()
        self.assertEqual(result, "test-zone")
    
    def test_get_instance_external_ip(self):
        """
        Test getting the external IP of a VM instance.
        """
        # Call the get_instance_external_ip method
        result = self.vm_manager.get_instance_external_ip("test-zone", "test-instance")
        
        # Verify that the expected methods were called and the result is correct
        self.mock_instances.get.assert_called_once()
        self.mock_instances_get.execute.assert_called_once()
        self.assertEqual(result, "1.2.3.4")
    
    def test_get_my_ip(self):
        """
        Test getting the external IP of the local machine.
        """
        # Call the get_my_ip method
        result = self.vm_manager.get_my_ip()
        
        # Verify that the expected methods were called and the result is correct
        self.mock_requests_get.assert_called_once()
        self.assertEqual(result, "1.2.3.4")


if __name__ == '__main__':
    unittest.main()