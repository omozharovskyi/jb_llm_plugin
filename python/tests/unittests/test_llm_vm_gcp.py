import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import time
from google.oauth2 import service_account
from googleapiclient import discovery
from googleapiclient.errors import HttpError

from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from llm_vm_manager.config import ConfigLoader


class TestGCPVirtualMachineManager(unittest.TestCase):
    """Test cases for GCPVirtualMachineManager class."""

    @patch('llm_vm_manager.llm_vm_gcp.service_account.Credentials.from_service_account_file')
    @patch('llm_vm_manager.llm_vm_gcp.discovery.build')
    def setUp(self, mock_discovery_build, mock_credentials):
        """Set up test environment before each test."""
        # Mock configuration
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get.side_effect = self._mock_config_get

        # Mock credentials and compute API
        self.mock_credentials = mock_credentials.return_value
        self.mock_compute = MagicMock()
        mock_discovery_build.return_value = self.mock_compute

        # Create instance of GCPVirtualMachineManager
        self.vm_manager = GCPVirtualMachineManager(self.mock_config)

        # Set project_id for testing
        self.vm_manager.project_id = 'test-project'

    def _mock_config_get(self, key):
        """Mock configuration get method."""
        config_values = {
            'gcp.sa_gcp_key': '/path/to/key.json',
            'gcp.project_name': 'test-project',
            'ssh.ssh_pub_key': '/path/to/ssh.pub',
            'retry_interval': 5
        }
        return config_values.get(key, None)

    def test_init(self):
        """Test initialization of GCPVirtualMachineManager."""
        self.assertEqual(self.vm_manager.project_id, 'test-project')
        self.assertEqual(self.vm_manager.compute, self.mock_compute)

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_create_instance(self, mock_logger):
        """Test create_instance method."""
        # Mock list_zones_with_gpus to return test zones
        self.vm_manager.list_zones_with_gpus = MagicMock(return_value={'us-central1-a', 'europe-west4-a'})

        # Mock build_vm_config
        self.vm_manager.build_vm_config = MagicMock(return_value={'name': 'test-instance'})

        # Mock wait_operation_state and wait_instance_state
        self.vm_manager.wait_operation_state = MagicMock(return_value=True)
        self.vm_manager.wait_instance_state = MagicMock(return_value=True)

        # Mock compute.instances().insert().execute()
        mock_insert = MagicMock()
        mock_insert.execute.return_value = {'name': 'operation-1'}
        self.mock_compute.instances().insert.return_value = mock_insert

        # Call create_instance
        self.vm_manager.create_instance('test-instance')

        # Verify calls
        self.vm_manager.list_zones_with_gpus.assert_called_once_with('nvidia-tesla-t4')
        self.mock_compute.instances().insert.assert_called_once()
        self.vm_manager.wait_operation_state.assert_called_once()
        self.vm_manager.wait_instance_state.assert_called_once()

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_start_instance(self, mock_logger):
        """Test start_instance method."""
        # Mock find_instance_zone
        self.vm_manager.find_instance_zone = MagicMock(return_value='us-central1-a')

        # Mock wait_operation_state and wait_instance_state
        self.vm_manager.wait_operation_state = MagicMock(return_value=True)
        self.vm_manager.wait_instance_state = MagicMock(return_value=True)

        # Mock compute.instances().start().execute()
        mock_start = MagicMock()
        mock_start.execute.return_value = {'name': 'operation-1'}
        self.mock_compute.instances().start.return_value = mock_start

        # Call start_instance
        self.vm_manager.start_instance('test-instance')

        # Verify calls
        self.vm_manager.find_instance_zone.assert_called_once_with('test-instance')
        self.mock_compute.instances().start.assert_called_once()
        self.vm_manager.wait_operation_state.assert_called_once()
        self.vm_manager.wait_instance_state.assert_called_once()

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_stop_instance(self, mock_logger):
        """Test stop_instance method."""
        # Mock find_instance_zone
        self.vm_manager.find_instance_zone = MagicMock(return_value='us-central1-a')

        # Mock wait_operation_state and wait_instance_state
        self.vm_manager.wait_operation_state = MagicMock(return_value=True)
        self.vm_manager.wait_instance_state = MagicMock(return_value=True)

        # Mock compute.instances().stop().execute()
        mock_stop = MagicMock()
        mock_stop.execute.return_value = {'name': 'operation-1'}
        self.mock_compute.instances().stop.return_value = mock_stop

        # Call stop_instance
        self.vm_manager.stop_instance('test-instance')

        # Verify calls
        self.vm_manager.find_instance_zone.assert_called_once_with('test-instance')
        self.mock_compute.instances().stop.assert_called_once()
        self.vm_manager.wait_operation_state.assert_called_once()
        self.vm_manager.wait_instance_state.assert_called_once()

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_delete_instance_exists(self, mock_logger):
        """Test delete_instance method when instance exists."""
        # Mock instance_exists and find_instance_zone
        self.vm_manager.instance_exists = MagicMock(return_value=True)
        self.vm_manager.find_instance_zone = MagicMock(return_value='us-central1-a')

        # Mock wait_operation_state and wait_instance_state
        self.vm_manager.wait_operation_state = MagicMock(return_value=True)
        self.vm_manager.wait_instance_state = MagicMock(return_value=True)

        # Mock compute.instances().delete().execute()
        mock_delete = MagicMock()
        mock_delete.execute.return_value = {'name': 'operation-1'}
        self.mock_compute.instances().delete.return_value = mock_delete

        # Call delete_instance
        self.vm_manager.delete_instance('test-instance')

        # Verify calls
        self.vm_manager.instance_exists.assert_called_once_with('test-instance')
        self.vm_manager.find_instance_zone.assert_called_once_with('test-instance')
        self.mock_compute.instances().delete.assert_called_once()
        self.vm_manager.wait_operation_state.assert_called_once()
        self.vm_manager.wait_instance_state.assert_called_once()

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_delete_instance_not_exists(self, mock_logger):
        """Test delete_instance method when instance does not exist."""
        # Mock instance_exists
        self.vm_manager.instance_exists = MagicMock(return_value=False)

        # Call delete_instance
        self.vm_manager.delete_instance('test-instance')

        # Verify calls
        self.vm_manager.instance_exists.assert_called_once_with('test-instance')
        mock_logger.error.assert_called_once()

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_instance_exists_true(self, mock_logger):
        """Test instance_exists method when instance exists."""
        # Mock find_instance_zone
        self.vm_manager.find_instance_zone = MagicMock(return_value='us-central1-a')

        # Mock compute.instances().get().execute()
        mock_get = MagicMock()
        mock_get.execute.return_value = {'name': 'test-instance', 'status': 'RUNNING'}
        self.mock_compute.instances().get.return_value = mock_get

        # Call instance_exists
        result = self.vm_manager.instance_exists('test-instance')

        # Verify calls and result
        self.vm_manager.find_instance_zone.assert_called_once_with('test-instance')
        self.mock_compute.instances().get.assert_called_once()
        self.assertTrue(result)

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_instance_exists_http_error(self, mock_logger):
        """Test instance_exists method when HttpError occurs."""
        # Mock find_instance_zone
        self.vm_manager.find_instance_zone = MagicMock(return_value='us-central1-a')

        # Mock compute.instances().get().execute() to raise HttpError
        mock_get = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 404
        mock_get.execute.side_effect = HttpError(mock_response, b'Not found')
        self.mock_compute.instances().get.return_value = mock_get

        # Call instance_exists
        result = self.vm_manager.instance_exists('test-instance')

        # Verify calls and result
        self.vm_manager.find_instance_zone.assert_called_once_with('test-instance')
        self.mock_compute.instances().get.assert_called_once()
        self.assertFalse(result)

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_list_instances(self, mock_logger):
        """Test list_instances method."""
        # Mock compute.instances().aggregatedList().execute()
        mock_list = MagicMock()
        mock_list.execute.return_value = {
            'items': {
                'zones/us-central1-a': {
                    'instances': [
                        {
                            'name': 'test-instance-1',
                            'status': 'RUNNING',
                            'zone': 'projects/test-project/zones/us-central1-a',
                            'machineType': 'projects/test-project/zones/us-central1-a/machineTypes/n1-standard-1'
                        }
                    ]
                },
                'zones/europe-west4-a': {
                    'instances': [
                        {
                            'name': 'test-instance-2',
                            'status': 'TERMINATED',
                            'zone': 'projects/test-project/zones/europe-west4-a',
                            'machineType': 'projects/test-project/zones/europe-west4-a/machineTypes/n1-standard-2'
                        }
                    ]
                }
            }
        }
        self.mock_compute.instances().aggregatedList.return_value = mock_list

        # Call list_instances
        self.vm_manager.list_instances()

        # Verify calls
        self.mock_compute.instances().aggregatedList.assert_called_once_with(project='test-project')
        self.assertEqual(mock_logger.info.call_count, 3)  # Header + 2 instances

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_find_instance_zone(self, mock_logger):
        """Test find_instance_zone method."""
        # Mock compute.instances().aggregatedList().execute()
        mock_list = MagicMock()
        mock_list.execute.return_value = {
            'items': {
                'zones/us-central1-a': {
                    'instances': [
                        {
                            'name': 'test-instance',
                            'zone': 'projects/test-project/zones/us-central1-a'
                        }
                    ]
                },
                'zones/europe-west4-a': {
                    'instances': []
                }
            }
        }
        self.mock_compute.instances().aggregatedList.return_value = mock_list

        # Call find_instance_zone
        result = self.vm_manager.find_instance_zone('test-instance')

        # Verify calls and result
        self.mock_compute.instances().aggregatedList.assert_called_once_with(project='test-project')
        self.assertEqual(result, 'us-central1-a')

    @patch('os.path.isfile')
    def test_build_vm_config(self, mock_isfile):
        """Test build_vm_config static method."""
        # Set default behavior for isfile
        mock_isfile.return_value = False

        # Test with default parameters
        config = GCPVirtualMachineManager.build_vm_config('test-instance', 'us-central1-a')

        # Verify basic config structure
        self.assertEqual(config['name'], 'test-instance')
        self.assertEqual(config['machineType'], 'zones/us-central1-a/machineTypes/n1-standard-1')
        self.assertEqual(len(config['disks']), 1)
        self.assertEqual(len(config['networkInterfaces']), 1)
        self.assertEqual(config['tags']['items'], ['ollama-server'])

        # Test with GPU accelerator
        config = GCPVirtualMachineManager.build_vm_config(
            'test-instance', 'us-central1-a', gpu_accelerator='nvidia-tesla-t4'
        )

        # Verify GPU config
        self.assertEqual(config['guestAccelerators'][0]['acceleratorType'], 
                        'zones/us-central1-a/acceleratorTypes/nvidia-tesla-t4')
        self.assertEqual(config['metadata']['items'][0]['key'], 'install-nvidia-driver')

        # Test with SSH key
        mock_isfile.return_value = True
        with patch('builtins.open', mock_open(read_data='ssh-rsa AAAAB3NzaC1yc2E...')):
            config = GCPVirtualMachineManager.build_vm_config(
                'test-instance', 'us-central1-a', ssh_pub_key_file='/path/to/ssh.pub'
            )

            # Verify SSH key config
            self.assertEqual(config['metadata']['items'][0]['key'], 'ssh-keys')
            self.assertTrue(config['metadata']['items'][0]['value'].startswith('jbllm:ssh-rsa'))

    @patch('llm_vm_manager.llm_vm_gcp.time.time')
    @patch('llm_vm_manager.llm_vm_gcp.time.sleep')
    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_wait_instance_state_success(self, mock_logger, mock_sleep, mock_time):
        """Test wait_instance_state method with successful state change."""
        # Mock time.time to simulate elapsed time
        mock_time.side_effect = [0, 10, 20]

        # Mock instance_exists
        self.vm_manager.instance_exists = MagicMock(return_value=True)

        # Mock compute.instances().get().execute()
        mock_get = MagicMock()
        mock_get.execute.return_value = {'status': 'RUNNING'}
        self.mock_compute.instances().get.return_value = mock_get

        # Call wait_instance_state
        result = self.vm_manager.wait_instance_state(
            'us-central1-a', 'test-instance', 
            ['RUNNING'], ['STAGING'], ['ERROR']
        )

        # Verify calls and result
        self.vm_manager.instance_exists.assert_called_once()
        self.mock_compute.instances().get.assert_called_once()
        self.assertTrue(result)

    @patch('llm_vm_manager.llm_vm_gcp.time.time')
    @patch('llm_vm_manager.llm_vm_gcp.time.sleep')
    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_wait_operation_state_success(self, mock_logger, mock_sleep, mock_time):
        """Test wait_operation_state method with successful completion."""
        # Mock time.time to simulate elapsed time
        mock_time.side_effect = [0, 10, 20]

        # Mock compute.zoneOperations().get().execute()
        mock_get = MagicMock()
        mock_get.execute.return_value = {'status': 'DONE'}
        self.mock_compute.zoneOperations().get.return_value = mock_get

        # Call wait_operation_state
        result = self.vm_manager.wait_operation_state(
            'us-central1-a', 'operation-1', 
            ['DONE'], ['RUNNING'], ['ERROR']
        )

        # Verify calls and result
        self.mock_compute.zoneOperations().get.assert_called_once()
        self.assertTrue(result)

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_list_zones_with_gpus(self, mock_logger):
        """Test list_zones_with_gpus method."""
        # Mock compute.acceleratorTypes().aggregatedList().execute()
        mock_list = MagicMock()
        mock_list.execute.return_value = {
            'items': {
                'zones/us-central1-a': {
                    'acceleratorTypes': [
                        {'name': 'nvidia-tesla-t4'}
                    ]
                },
                'zones/europe-west4-a': {
                    'acceleratorTypes': [
                        {'name': 'nvidia-tesla-t4'},
                        {'name': 'nvidia-tesla-v100'}
                    ]
                },
                'zones/asia-east1-a': {
                    'acceleratorTypes': [
                        {'name': 'nvidia-tesla-p100'}
                    ]
                }
            }
        }
        self.mock_compute.acceleratorTypes().aggregatedList.return_value = mock_list

        # Mock compute.acceleratorTypes().aggregatedList_next()
        self.mock_compute.acceleratorTypes().aggregatedList_next.return_value = None

        # Call list_zones_with_gpus
        result = self.vm_manager.list_zones_with_gpus('nvidia-tesla-t4')

        # Verify calls and result
        self.mock_compute.acceleratorTypes().aggregatedList.assert_called_once_with(project='test-project')
        self.assertEqual(result, {'us-central1-a', 'europe-west4-a'})

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_get_instance_external_ip(self, mock_logger):
        """Test get_instance_external_ip method."""
        # Mock compute.instances().get().execute()
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            'networkInterfaces': [
                {
                    'accessConfigs': [
                        {'natIP': '35.123.456.789'}
                    ]
                }
            ]
        }
        self.mock_compute.instances().get.return_value = mock_get

        # Call get_instance_external_ip
        result = self.vm_manager.get_instance_external_ip('us-central1-a', 'test-instance')

        # Verify calls and result
        self.mock_compute.instances().get.assert_called_once()
        self.assertEqual(result, '35.123.456.789')

    @patch('llm_vm_manager.llm_vm_gcp.logger')
    def test_set_firewall_ollama_rule_create(self, mock_logger):
        """Test set_firewall_ollama_rule method when rule doesn't exist."""
        # Mock compute.firewalls().get().execute() to raise HttpError
        mock_get = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 404
        mock_get.execute.side_effect = HttpError(mock_response, b'Not found')
        self.mock_compute.firewalls().get.return_value = mock_get

        # Mock compute.firewalls().insert().execute()
        mock_insert = MagicMock()
        mock_insert.execute.return_value = {'name': 'allow-ollama-api-from-my-ip'}
        self.mock_compute.firewalls().insert.return_value = mock_insert

        # Call set_firewall_ollama_rule
        self.vm_manager.set_firewall_ollama_rule('192.168.1.1')

        # Verify calls
        self.mock_compute.firewalls().get.assert_called_once()
        self.mock_compute.firewalls().insert.assert_called_once()

    def test_priority_factory(self):
        """Test priority_factory static method."""
        # Create priority function
        priority_func = GCPVirtualMachineManager.priority_factory(['europe', 'us', '*', 'asia'])

        # Test priority for different zones
        self.assertEqual(priority_func('europe-west4-a'), 0)
        self.assertEqual(priority_func('us-central1-a'), 1)
        self.assertEqual(priority_func('asia-east1-a'), 3)
        self.assertEqual(priority_func('australia-southeast1-a'), 2)  # Matches wildcard

    def test_simple_priority(self):
        """Test simple_priority static method."""
        # Test priority for different zones
        self.assertEqual(GCPVirtualMachineManager.simple_priority('europe-west4-a'), 0)
        self.assertEqual(GCPVirtualMachineManager.simple_priority('us-central1-a'), 1)
        self.assertEqual(GCPVirtualMachineManager.simple_priority('asia-east1-a'), 3)
        self.assertEqual(GCPVirtualMachineManager.simple_priority('australia-southeast1-a'), 2)


if __name__ == '__main__':
    unittest.main()
