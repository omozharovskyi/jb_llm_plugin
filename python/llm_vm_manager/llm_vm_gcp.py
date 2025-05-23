from llm_vm_manager.llm_vm_base import LLMVirtualMachineManager
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.jb_llm_logger import logger
import os
from google.oauth2 import service_account
from googleapiclient import discovery
import time
from googleapiclient.errors import HttpError


class GCPVirtualMachineManager(LLMVirtualMachineManager):
    """
    A class for managing Google Cloud Platform virtual machines for LLM workloads.
    Provides functionality for creating, starting, stopping, and deleting VM instances,
    as well as configuring them for GPU acceleration.
    """

    def __init__(self, configuration: ConfigLoader):
        """
        Initialize the GCP Virtual Machine Manager.
        Args:
            configuration (ConfigLoader): Configuration object containing GCP credentials and settings.
        """
        super().__init__(configuration)
        self.credentials = service_account.Credentials.from_service_account_file(
            self.llm_vm_manager_config.get("gcp.sa_gcp_key"))
        self.compute = discovery.build('compute', 'v1', credentials=self.credentials)
        self.project_id = self.llm_vm_manager_config.get("gcp.project_name")

    def create_instance(self, instance_name: str):
        """
        Create a new GCP virtual machine instance with GPU support.
        This method attempts to create a VM in available zones with GPU support,
        prioritizing zones based on the simple_priority method. If creation fails
        in one zone, it will try the next available zone.
        Args:
            instance_name (str): The name for the new VM instance.
        Returns:
            None
        """
        zones_with_gpu = sorted(self.list_zones_with_gpus('nvidia-tesla-t4'), key=self.simple_priority)
        # zones_with_gpu = sorted(self.list_zones_with_gpus('nvidia-tesla-t4'),
        #                         key=self.priority_factory(['europe', 'us', '*', 'asia']))
        success_gpu_vm_zone = ''
        for gpu_zone in zones_with_gpu:
            logger.info(f"Creating VM for LLM '{instance_name}' in zone '{gpu_zone}'.")
            vm_config = self.build_vm_config(instance_name, gpu_zone, restart_on_failure=False,
                                         ssh_pub_key_file=self.llm_vm_manager_config.get("ssh.ssh_pub_key"))
            logger.debug(f"VM config: {vm_config}")
            operation = self.compute.instances().insert(project=self.project_id, zone=gpu_zone, body=vm_config
                                                        ).execute()
            logger.info(f"Instance creation started: {operation['name']}")
            if not self.wait_operation_state(gpu_zone, operation['name']):
                logger.info(f"Instance creation failed in '{gpu_zone}'. Will retry in next zone...")
                time.sleep(self.llm_vm_manager_config.get("retry_interval"))
                continue
            logger.info(f"Instance created. Waiting for become operational.")
            self.wait_instance_state(gpu_zone, instance_name, ['RUNNING'], ['STAGING'])
            success_gpu_vm_zone = gpu_zone
            break

    def start_instance(self, instance_name: str):
        """
        Start a stopped GCP virtual machine instance.
        This method finds the zone where the instance is located and starts it.
        It then waits for the operation to complete and for the instance to reach
        the RUNNING state.
        Args:
            instance_name (str): The name of the VM instance to start.
        Returns:
            None
        """
        logger.info(f"Starting VM '{instance_name}'.")
        zone = self.find_instance_zone(instance_name)
        response = self.compute.instances().start(project=self.project_id, zone=zone, instance=instance_name
                                                  ).execute()
        self.wait_operation_state(zone, response['name'], ['DONE'], ['RUNNING'],
                                  ['ERROR'])
        self.wait_instance_state(zone, instance_name, ['RUNNING'], ['STAGING'])
        logger.info("Done.")

    def stop_instance(self, instance_name: str):
        """
        Stop a running GCP virtual machine instance.
        This method finds the zone where the instance is located and stops it.
        It then waits for the operation to complete and for the instance to reach
        the TERMINATED state.
        Args:
            instance_name (str): The name of the VM instance to stop.
        Returns:
            None
        """
        logger.info(f"Stopping VM '{instance_name}'.")
        zone = self.find_instance_zone(instance_name)
        response = self.compute.instances().stop(project=self.project_id, zone=zone,instance=instance_name
                                                 ).execute()
        self.wait_operation_state(zone, response['name'], ['DONE'], ['RUNNING'],
                                  ['ERROR'])
        self.wait_instance_state(zone, instance_name, ['TERMINATED'], ['STOPPING'])
        logger.info("Done")

    def delete_instance(self, instance_name: str):
        """
        Delete a GCP virtual machine instance.
        This method checks if the instance exists, finds its zone, and then
        deletes it. It waits for the operation to complete and for the instance
        to be fully deleted.
        Args:
            instance_name (str): The name of the VM instance to delete.
        Returns:
            None
        """
        if not self.instance_exists(instance_name):
            logger.error(f"Instance '{instance_name}' not found.")
            return
        zone = self.find_instance_zone(instance_name)
        if zone:
            response = self.compute.instances().delete(project=self.project_id, zone=zone,  instance=instance_name
                                                       ).execute()
            self.wait_operation_state(zone, response['name'], ['DONE'], ['RUNNING'],
                                      ['ERROR'])
            self.wait_instance_state(zone, instance_name, ['DELETED'],
                                     ['STOPPING', 'TERMINATED'])
        else:
            logger.error(f"Instance '{instance_name}' not found in zone {zone}.")

    def instance_exists(self, instance_name: str):
        """
        Check if a GCP virtual machine instance exists.
        This method attempts to find the zone where the instance is located
        and then checks if the instance exists in that zone.
        Args:
            instance_name (str): The name of the VM instance to check.
        Returns:
            bool: True if the instance exists, False otherwise.
        """
        logger.debug(f"Checking if instance '{instance_name}' exists.")
        zone = self.find_instance_zone(instance_name)
        if zone:
            try:
                self.compute.instances().get(project=self.project_id, zone=zone, instance=instance_name
                                             ).execute()
                return True
            except HttpError as err_expt:
                if err_expt.resp.status == 404:
                    logger.debug(f"Instance '{instance_name}' not found in zone '{zone}'")
                    return False
                logger.error(f"Unexpected error upon retrieving instance information: {err_expt}")
                return False
        else:
            logger.debug(f"No zone found for instance '{instance_name}'")
            return False

    def list_instances(self):
        """
        List all GCP virtual machine instances in the project.
        This method retrieves all VM instances across all zones in the project
        and logs their details including name, status, machine type, and zone.
        Returns:
            None: Information is logged but not returned.
        """
        # STAGING | RUNNING | STOPPING | TERMINATED
        logger.debug(f"Listing instances under project '{self.project_id}'.")
        result = self.compute.instances().aggregatedList(project=self.project_id).execute()
        instances = []
        for zone, response in result['items'].items():
            if 'instances' in response:
                for instance in response['instances']:
                    instances.append(instance)
        if not instances:
            logger.info("No instances found.")
            return
        logger.info(f"Instances in project '{self.project_id}':\n")
        for instance in instances:
            name = instance["name"]
            status = instance["status"]  # STAGING | RUNNING | STOPPING | TERMINATED
            instance_zone = instance["zone"].split('/')[-1]
            machine_type = instance["machineType"].split("/")[-1]
            logger.info(f"{name} | {status} | type: {machine_type} | zone: {instance_zone}")

    def find_instance_zone(self, instance_name):
        """
        Find the zone where a GCP virtual machine instance is located.
        This method searches through all zones in the project to find the zone
        where the specified instance is located.
        Args:
            instance_name (str): The name of the VM instance to find.
        Returns:
            str or None: The zone name if the instance is found, None otherwise.
        """
        logger.debug(f"Finding zone for instance '{instance_name}'")
        result = self.compute.instances().aggregatedList(project=self.project_id).execute()
        for zone, response in result['items'].items():
            for instance in response.get('instances', []):
                if instance['name'] == instance_name:
                    logger.debug(f"Found zone '{zone}' for instance '{instance_name}'")
                    return instance['zone'].split('/')[-1]
        logger.debug(f"No zone for instance '{instance_name}' found")
        return None

    @staticmethod
    def build_vm_config(instance_name, zone, machine_type="n1-standard-1", image_family="ubuntu-2204-lts",
                        hdd_size=10, gpu_accelerator=None, restart_on_failure=True, ssh_pub_key_file=None,
                        firewall_tag="ollama-server"):
        """
        Build the configuration dictionary for a GCP virtual machine instance.
        This static method creates a configuration dictionary that can be used to create
        a new VM instance with the specified parameters.
        Args:
            instance_name (str): The name for the new VM instance.
            zone (str): The zone where the VM will be created.
            machine_type (str, optional): The machine type to use. Defaults to "n1-standard-1".
            image_family (str, optional): The OS image family to use. Defaults to "ubuntu-2204-lts".
            hdd_size (int, optional): The size of the boot disk in GB. Defaults to 10.
            gpu_accelerator (str, optional): The GPU accelerator type to attach. Defaults to None.
            restart_on_failure (bool, optional): Whether to restart the VM on failure. Defaults to True.
            ssh_pub_key_file (str, optional): Path to the SSH public key file. Defaults to None.
            firewall_tag (str, optional): The firewall tag to apply. Defaults to "ollama-server".
        Returns:
            dict: The VM configuration dictionary.
        """
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
        """
        Wait for a GCP virtual machine instance to reach a specific state.

        This method polls the instance status until it reaches one of the accepted states,
        times out, or enters an error state.
        Args:
            zone (str): The zone where the instance is located.
            instance_name (str): The name of the VM instance.
            accept_statuses (list): List of status strings that indicate success.
            keep_wait_statuses (list): List of status strings that indicate to keep waiting.
            error_statuses (list): List of status strings that indicate an error.
            timeout (int, optional): Maximum time to wait in seconds. Defaults to 300.
            interval (int, optional): Time between status checks in seconds. Defaults to 10.
        Returns:
            bool: True if the instance reached an accepted state, False otherwise.
        """
        logger.info(f"Waiting for '{instance_name}' to become '{accept_statuses}' during '{timeout}' seconds...")
        start = time.time()
        elapsed = 0
        while True:
            if (not self.instance_exists(instance_name)) and ('DELETED' in accept_statuses):
                logger.info(f"Instance '{instance_name}' was deleted.")
                return True
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
                            error_statuses, expected_done_errors=None, timeout=300, interval=5):
        """
        Wait for a GCP operation to complete.
        This method polls the operation status until it completes, times out, or enters an error state.
        It also handles expected errors that might occur during operation completion.
        Args:
            zone (str): The zone where the operation is running.
            operation_name (str): The name of the operation to wait for.
            accept_statuses (list): List of status strings that indicate success.
            keep_wait_statuses (list): List of status strings that indicate to keep waiting.
            error_statuses (list): List of status strings that indicate an error.
            expected_done_errors (list, optional): List of error codes that are expected and should be handled. Defaults to None.
            timeout (int, optional): Maximum time to wait in seconds. Defaults to 300.
            interval (int, optional): Time between status checks in seconds. Defaults to 5.

        Returns:
            bool: True if the operation completed successfully, False otherwise.
        """
        if expected_done_errors is None:
            expected_done_errors = []

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
        """
        List all GCP zones that have the specified GPU type available.
        This method queries the GCP API to find all zones where the specified
        GPU accelerator type is available for use.
        Args:
            gpu_name (str, optional): The name of the GPU accelerator to search for. 
                                      Defaults to "nvidia-tesla-t4".
        Returns:
            set: A set of zone names where the specified GPU is available.
        """
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
        """
        Get the external IP address of a GCP virtual machine instance.
        This method retrieves the external (public) IP address assigned to the
        specified VM instance.
        Args:
            zone (str): The zone where the instance is located.
            instance_name (str): The name of the VM instance.
        Returns:
            str or None: The external IP address if available, None otherwise.
        """
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
        """
        Create or update a firewall rule to allow access to Ollama API from a specific IP.
        This method creates or updates a GCP firewall rule that allows TCP traffic
        on port 11434 (Ollama API) from the specified IP address to instances with
        the specified firewall tag.
        Args:
            ip_address (str): The IP address to allow access from.
            firewall_rule_name (str, optional): The name for the firewall rule. 
                                               Defaults to "allow-ollama-api-from-my-ip".
            firewall_tag (str, optional): The target tag for instances to apply the rule to. 
                                         Defaults to "ollama-server".
        Returns:
            None
        Raises:
            HttpError: If there's an error creating or updating the firewall rule.
        """
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

    @staticmethod
    def priority_factory(zones_order):
        """
        Create a priority function for sorting zones based on a specified order.
        This factory method creates a function that can be used to sort zones
        based on a specified order of zone prefixes. Zones that match earlier
        prefixes in the list will be given higher priority.
        Args:
            zones_order (list): A list of zone prefixes in order of priority.
                               Can include a wildcard '*' to match any zone.
        Returns:
            function: A function that takes a zone name and returns its priority index.
        """
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

    @staticmethod
    def simple_priority(zone_name):
        """
        Assign a priority to a zone based on its geographic location.
        This method provides a simple priority scheme for zones based on their
        geographic location. The priority order is:
        1. Europe (highest priority)
        2. US
        3. Other regions
        4. Asia (lowest priority)
        Args:
            zone_name (str): The name of the zone to prioritize.
        Returns:
            int: A priority value (lower is higher priority).
        """
        if zone_name.startswith('europe'): return 0
        elif zone_name.startswith('us'): return 1
        elif zone_name.startswith('asia'): return 3
        else: return 2
