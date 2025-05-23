from llm_vm_manager.llm_vm_base import LLMVirtualMachineManager
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.jb_llm_logger import logger
import os
from google.oauth2 import service_account
from googleapiclient import discovery
import time
from googleapiclient.errors import HttpError


class GCPVirtualMachineManager(LLMVirtualMachineManager):
    def __init__(self, configuration: ConfigLoader):
        super().__init__(configuration)
        self.credentials = service_account.Credentials.from_service_account_file(
            self.llm_vm_manager_config.get("gcp.sa_gcp_key"))
        self.compute = discovery.build('compute', 'v1', credentials=self.credentials)
        self.project_id = self.llm_vm_manager_config.get("gcp.project_name")

    def create_instance(self, name: str):
        print(f"[GCP] Creating VM '{name}' in {self.zone} under project {self.project_id}")
        # zone_priority_list = self.llm_vm_manage_config.get("zone_priority").split(',')
        # Тут має бути логіка з використанням compute_v1.Instance()
        os.system(f"ssh-keygen -f ~/.ssh/known_hosts -R {vm_ip}")

    def start_instance(self, instance_name: str):
        logger.info(f"Starting VM '{instance_name}'.")
        zone = self.find_instance_zone(instance_name)
        response = self.compute.instances().start(project=self.project_id, zone=zone, instance=instance_name
                                                  ).execute()
        self.wait_operation_state(zone, response['name'], ['DONE'], ['RUNNING'],
                                  ['ERROR'])
        self.wait_instance_state(zone, instance_name, ['RUNNING'], ['STAGING'])
        logger.info("Done.")

    def stop_instance(self, instance_name: str):
        logger.info(f"Stopping VM '{instance_name}'.")
        zone = self.find_instance_zone(instance_name)
        response = self.compute.instances().stop(project=self.project_id, zone=zone,instance=instance_name
                                                 ).execute()
        self.wait_operation_state(zone, response['name'], ['DONE'], ['RUNNING'],
                                  ['ERROR'])
        self.wait_instance_state(zone, instance_name, ['TERMINATED'], ['STOPPING'])
        logger.info("Done")

    def delete_instance(self, name: str):
        print(f"[GCP] Deleting VM '{name}'")
        # Тут має бути логіка з client.delete()

    def list_instances(self):
        # STAGING (starting) | RUNNING | STOPPING | TERMINATED
        pass

    def find_instance_zone(self, instance_name):
        logger.debug(f"Finding zone for instance '{instance_name}'")
        result = self.compute.instances().aggregatedList(project=self.project_id).execute()
        for zone, response in result['items'].items():
            for instance in response.get('instances', []):
                if instance['name'] == instance_name:
                    logger.debug(f"Found zone '{zone}' for instance '{instance_name}'")
                    return instance['zone'].split('/')[-1]
        logger.debug(f"No zone for instance '{instance_name}' found")
        return None

    def build_vm_config(self, instance_name, zone, machine_type="n1-standard-1", image_family="ubuntu-2204-lts",
                        hdd_size=10, gpu_accelerator=None, restart_on_failure=True, ssh_pub_key_file=None,
                        firewall_tag="ollama-server"):
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
            vm_config['tags'] = {'items': [firewall_tag]}
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

    def wait_instance_state(self, zone, instance_name, accept_statuses, keep_wait_statuses,
                            error_statuses, timeout=300, interval=10):
        logger.info(f"Waiting for '{instance_name}' to become '{accept_statuses}' during '{timeout}' seconds...")
        start = time.time()
        elapsed = 0
        while True:
            result = self.compute.instances().get(project=self.project_id, zone=zone, instance=instance_name).execute()
            status = result.get("status")
            if status in accept_statuses:
                logger.info(f"Instance is in '{status}' state.")
                return True
            if status in keep_wait_statuses:
                logger.info(f"{elapsed} seconds passed. Instance still in '{status}' state."
                            f"Will wait for {timeout-elapsed} seconds more.")
            if status in error_statuses:
                logger.info(f"Instance is in unexpected '{status}' state. Will not continue.")
                return False
            elapsed = time.time() - start
            if elapsed >= timeout:
                logger.info(f"Timeout waiting for instance to become any of {accept_statuses} states.")
                return False
            time.sleep(interval)

    def wait_operation_state(self, zone, operation_name, accept_statuses, keep_wait_statuses,
                            error_statuses, expected_done_errors, timeout=300, interval=5):
        logger.info(f"Waiting for '{operation_name}' to complete with timeout in '{timeout}' seconds...")
        start = time.time()
        elapsed = 0
        while True:
            result = self.compute.zoneOperations().get(project=self.project_id, zone=zone, operation=operation_name
                                                  ).execute()
            status = result.get("status")
            if status in keep_wait_statuses:
                logger.info(f"Current state: {result['status']}")
                logger.info(f"{elapsed} seconds passed. Instance still in '{status}' state."
                            f"Will wait for {timeout - elapsed} seconds more.")
            if status in accept_statuses:
                if 'error' in result:
                    error_code = result['error']['errors'][0].get('code', 'UNKNOWN_CODE')
                    error_message = result['error']['errors'][0].get('message', 'No message provided')
                    if error_code in expected_done_errors:
                        logger.warning(f"Got '{error_code}' upon instance creation. Will try out next retry.")
                        return False
                    else:
                        logger.error(f"Complited with unexpected error code '{error_code}': '{error_message}' ")
                        logger.debug(f"There was unexpected error upon completion: {result['error']}")
                        return False
                logger.info("Done successfully.")
                return True
            if status in error_statuses:
                logger.error(f"Instance is in unexpected '{status}' state. Will not continue.")
                return False
            elapsed = time.time() - start
            if elapsed >= timeout:
                logger.info(f"Timeout waiting for instance to become any of {accept_statuses} states.")
                return False
            time.sleep(interval)

    def list_zones_with_gpus(self, gpu_name="nvidia-tesla-t4"):
        request = self.compute.acceleratorTypes().aggregatedList(project=self.project_id)
        zones_with_gpu = set()
        while request is not None:
            response = request.execute()
            for zone, scoped_list in response.get("items", {}).items():
                accelerator_types = scoped_list.get("acceleratorTypes", [])
                for acc in accelerator_types:
                    if acc["name"] == gpu_name:
                        zone_name = zone.split("/")[-1]
                        zones_with_gpu.add(zone_name)
            request = self.compute.acceleratorTypes().aggregatedList_next(previous_request=request,
                                                                     previous_response=response)
        return zones_with_gpu

    def get_instance_external_ip(self, zone, instance_name):
        result = self.compute.instances().get(project=self.project_id, zone=zone, instance=instance_name).execute()
        try:
            interfaces = result['networkInterfaces']
            access_configs = interfaces[0].get('accessConfigs', [])
            external_ip = access_configs[0].get('natIP') if access_configs else None
            return external_ip
        except (KeyError, IndexError):
            return None

    def set_firewall_ollama_rule(self, ip_address, firewall_rule_name="allow-ollama-api-from-my-ip",
                                 firewall_tag="ollama-server"):
        source_ip_range = ip_address + '/32'
        firewall_body = {
            "name": firewall_rule_name,
            "direction": "INGRESS",
            "allowed": [{
                "IPProtocol": "tcp",
                "ports": ["11434"]
            }],
            "sourceRanges": [source_ip_range],
            "targetTags": [firewall_tag],
            "description": "Allow port 11434 (Ollama LLM) from my IP"
        }
        try:
            existing_rule = self.compute.firewalls().get(project=self.project_id, firewall=firewall_rule_name).execute()
            logger.info("Firewall rule already exists, updating it.")
            response = self.compute.firewalls().update(
                project=self.project_id, firewall=firewall_rule_name, body=firewall_body
            ).execute()
        except HttpError as exp_err:
            if exp_err.resp.status == 404:
                logger.info("Firewall rule does not exist, creating it.")
                response = self.compute.firewalls().insert(project=self.project_id, body=firewall_body).execute()
            else:
                logger.error(f"Failed to create or update firewall rule: {exp_err}")
                raise
        logger.info(f"Firewall rule set result: {response}")

    def priority_factory(self, zones_order):
        def priority(zone_name):
            matched_index = None
            wildcard_index = None
            for index, zone_prefix in enumerate(zones_order):
                if zone_prefix == '*':
                    wildcard_index = index
                    continue
                if zone_name.startswith(zone_prefix):
                    matched_index = index
                    break
            if matched_index is not None:
                return matched_index
            if wildcard_index is not None:
                return wildcard_index
            return len(zones_order)
        return priority

    def simple_priority(self, zone_name):
        if zone_name.startswith('europe'): return 0
        elif zone_name.startswith('us'): return 1
        elif zone_name.startswith('asia'): return 3
        else: return 2