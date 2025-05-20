from llm_vm_manager.llm_vm_base import LLMVirtualMachineManager
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.jb_llm_logger import logger
import os
from google.oauth2 import service_account
from googleapiclient import discovery
import time


class GCPVirtualMachineManager(LLMVirtualMachineManager):
    def __init__(self, configuration: ConfigLoader):
        super().__init__(configuration)
        self.credentials = service_account.Credentials.from_service_account_file(
            self.llm_vm_manager_config.get("gcp.sa_gcp_key"))
        self.compute = discovery.build('compute', 'v1', credentials=self.credentials)
        # self.client = compute_v1.InstancesClient()

    def create_instance(self, name: str):
        print(f"[GCP] Creating VM '{name}' in {self.zone} under project {self.project_id}")
        # Тут має бути логіка з використанням compute_v1.Instance()

    def start_instance(self, name: str):
        print(f"[GCP] Starting VM '{name}'")
        # Тут має бути логіка з client.start()
        # if status == "RUNNING":

    def stop_instance(self, name: str):
        print(f"[GCP] Stopping VM '{name}'")
        # Тут має бути логіка з client.stop()

    def delete_instance(self, name: str):
        print(f"[GCP] Deleting VM '{name}'")
        # Тут має бути логіка з client.delete()

    def list_instances(self):
        pass

    def build_vm_config(self, instance_name, zone, machine_type="n1-standard-1", image_family="ubuntu-2204-lts",
                        hdd_size=10, gpu_accelerator=None, restart_on_failure=True, ssh_pub_key_file=None,
                        firewall_tag=None):
        vm_config = {
            'name': instance_name,
            'machineType': f"zones/{zone}/machineTypes/{machine_type}",
            'disks': [{
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': f"projects/ubuntu-os-cloud/global/images/family/{image_family}",
                    'diskSizeGb': f"{hdd_size}"
                }
            }],
            'networkInterfaces': [{
                'network': 'global/networks/default',
                'accessConfigs': [{'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}]
            }],
            'scheduling': {'onHostMaintenance': 'TERMINATE', 'automaticRestart': restart_on_failure},
        }
        if firewall_tag:
            vm_config['tags'] = {'items': ['ollama-server']}
        if gpu_accelerator:
            vm_config['guestAccelerators'] = [{
                'acceleratorType': f'zones/{zone}/acceleratorTypes/{gpu_accelerator}',
                'acceleratorCount': 1
            }]
            vm_config['metadata'] = {
                'items': [{'key': 'install-nvidia-driver', 'value': 'true'}]
            }
        if os.path.isfile(ssh_pub_key_file):
            ssh_item = {
                'key': 'ssh-keys',
                'value': 'jbllm:' + open(ssh_pub_key_file).read()
            }
            if 'metadata' in vm_config:
                vm_config['metadata']['items'].append(ssh_item)
            else:
                vm_config['metadata'] = {'items': [ssh_item]}
        return vm_config

    def wait_instance_state(self, project_id, zone, instance_name, accept_statuses, keep_wait_statuses,
                            error_statuses, timeout=300, interval=10):
        start = time.time()
        elapsed = 0
        while True:
            result = self.compute.instances().get(project=project_id, zone=zone, instance=instance_name).execute()
            status = result.get("status")
            if status in accept_statuses:
                logger.info(f"Instance is in '{status}' state.")
                return True
            if status in keep_wait_statuses:
                logger.info(f"{elapsed} seconds passed. Instance still in '{status}' state."
                            f"Will wait for {timeout-elapsed} seconds more.")
            if status in error_statuses:
                logger.info(f"Instance is in expected '{status}' state. Will not continue.")
                return False
            elapsed = time.time() - start
            if elapsed >= timeout:
                logger.info(f"Timeout waiting for instance to become any of {accept_statuses} states.")
                return False
            time.sleep(interval)
