from googleapiclient import discovery
import paramiko
import time
from google.oauth2 import service_account
from jb_llm_logger import logger
from google.cloud import compute_v1
import os
import requests
import socket
from googleapiclient.errors import HttpError

PROJECT = "jb-llm-plugin"
INSTANCE_NAME = "ollama-python-vm"
SSH_KEY_FILE_PUB = "sa-keys/jb-llm-plugin-ssh.pub"
SECRET_SSH_FILE = "sa-keys/jb-llm-plugin-ssh"
SA_GCP_KEY_FILE = "sa-keys/jb-llm-plugin-sa.json"

def create_vm_with_gpu(project_id, instance_name, retry_interval=5):
    credentials = service_account.Credentials.from_service_account_file(SA_GCP_KEY_FILE)
    compute = discovery.build('compute', 'v1', credentials=credentials)
    zones_with_gpu = sorted(list_zones_with_gpus(project_id, 'nvidia-tesla-t4'), key=priority)
    success_gpu_vm_zone = ''
    for gpu_zone in zones_with_gpu:
        vm_config = create_vm_config(instance_name, gpu_zone, restart_on_failure=False, ssh_pub_key_file=SSH_KEY_FILE_PUB)
        try:
            operation = compute.instances().insert(
                project=project_id,
                zone=gpu_zone,
                body=vm_config
            ).execute()
            logger.info(f"Instance creation started: {operation['name']}")
            wait_for_operation(compute,PROJECT,gpu_zone,operation['name'])
            logger.info(f"Instance created. Waiting for become operational.")
            success_gpu_vm_zone = gpu_zone
            break
        except Exception as vm_excpept:
            logger.warning(f"Unable to create VM in '{gpu_zone}': {vm_excpept}")
        time.sleep(retry_interval)
    return success_gpu_vm_zone

def create_vm_config(instance_name, zone, cores_num=1, hdd_size=10, gpu_enabled=False, restart_on_failure=True,
                     ssh_pub_key_file=None):
    config = {
        'name': instance_name,
        'machineType': f"zones/{zone}/machineTypes/n1-standard-{cores_num}",
        'disks': [{
            'boot': True,
            'autoDelete': True,
            'initializeParams': {
                'sourceImage': 'projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts',
                'diskSizeGb': f"{hdd_size}"
            }
        }],
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [{'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}]
        }],
        'scheduling': {'onHostMaintenance': 'TERMINATE', 'automaticRestart': restart_on_failure},
        'tags': {'items': ['ollama-server']},
    }
    if gpu_enabled:
        config['guestAccelerators'] = [{
            'acceleratorType': f'zones/{zone}/acceleratorTypes/nvidia-tesla-t4',
            'acceleratorCount': 1
        }]
        config['metadata'] = {
            'items': [{'key': 'install-nvidia-driver', 'value': 'true'}]
        }
    if os.path.isfile(ssh_pub_key_file):
        ssh_item = {
            'key': 'ssh-keys',
            'value': 'jbllm:' + open(ssh_pub_key_file).read()
        }
        if 'metadata' in config:
            config['metadata']['items'].append(ssh_item)
        else:
            config['metadata'] = {'items': [ssh_item]}
    return config

def priority(zone_name):
    if zone_name.startswith('europe'):
        return 0
    elif zone_name.startswith('us'):
        return 1
    elif zone_name.startswith('asia'):
        return 3
    else:
        return 2

def run_ssh_commands(host_ip, username='jbllm'):
    is_ssh_port_open(host_ip)
    commands = [
        "sudo DEBIAN_FRONTEND=noninteractive apt-get update -y && sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -yq",
        "curl https://ollama.com/install.sh | sh",
        "sudo sed -i '/^Environment/ i Environment=\"OLLAMA_HOST=0.0.0.0\"' /etc/systemd/system/ollama.service",
        "sudo systemctl daemon-reload",
        "sudo systemctl restart ollama",
        "ollama --version",
        "uname -a",
    ]
    # paramiko.util.log_to_file("paramiko.log")
    key = paramiko.RSAKey.from_private_key_file(SECRET_SSH_FILE)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect(hostname=host_ip, username=username, pkey=key)
    ssh = connect_with_retries(host_ip,username, key)
    wait_for_shell_ready(ssh)
    for cmd in commands:
        logger.info(f"Running: {cmd}")
        execute_ssh(ssh, cmd)
        # stdin, stdout, stderr = ssh.exec_command(cmd)
        # time.sleep(2)
        # logger.info(stdout.read().decode())
        # logger.info(stderr.read().decode())
    ssh.close()

def execute_ssh(ssh_object, ssh_command, max_wait_seconds: int = 300):
    start_time = time.time()
    stdin, stdout, stderr = ssh_object.exec_command(ssh_command)
    channel = stdout.channel
    while not channel.exit_status_ready():
        if time.time() - start_time > max_wait_seconds:
            raise TimeoutError(f"Timed out waiting for SSH command to complete: {ssh_command}")
        # if channel.recv_ready():
        #     logger.info(channel.recv(1024).decode().rstrip('\n'))
            # logger.info(channel.recv(1024).decode())
        time.sleep(1)
    stdout_output = stdout.read().decode()
    stderr_output = stderr.read().decode()
    exit_status = channel.recv_exit_status()
    if stdout_output.strip():
        logger.info(stdout_output.strip())
    if stderr_output.strip():
        logger.error(stderr_output.strip())
    logger.info(f"Exit code: {exit_status}")

def connect_with_retries(host_ip, username, key, retries=5, delay=10, timeout=30):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"[{attempt}/{retries}] Connecting to {host_ip}...")
            ssh.connect(
                hostname=host_ip,
                username=username,
                pkey=key,
                timeout=timeout,
                allow_agent=False,
                look_for_keys=False
            )
            logger.info("Connection successful.")
            return ssh
        except (paramiko.ssh_exception.NoValidConnectionsError,
                paramiko.ssh_exception.SSHException,
                socket.timeout,
                socket.error) as e:
            logger.info(f"Connection attempt {attempt} failed: {e}")
            if attempt < retries:
                logger.info(f"Retrying in {delay} seconds...\n")
                time.sleep(delay)
            else:
                logger.info("All connection attempts failed.")
                raise
    return None

def is_ssh_port_open(host, port=22, timeout=3, retries=10, delay=5):
    for i in range(retries):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            logger.info("Socket is not open. Will retry.")
        time.sleep(delay)
    raise

def wait_for_shell_ready(ssh, retries=10, delay=5):
    for i in range(retries):
        try:
            _, stdout, _ = ssh.exec_command("echo ok")
            if stdout.read().strip() == b"ok":
                return True
        except Exception:
            logger.info("Shell is not ready. Will retry.")
        time.sleep(delay)
    raise TimeoutError("Shell not ready after multiple attempts")

def start_ollama_and_load_model(host_ip, username='jbllm'):
    key = paramiko.RSAKey.from_private_key_file(SECRET_SSH_FILE)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host_ip, username=username, pkey=key)
    # commands = [
    #     "ollama pull codellama:7b-python",
    # ]
    commands = [ "ollama pull tinyllama"    ]
    for cmd in commands:
        logger.info(f"Executing: {cmd}")
        execute_ssh(ssh, cmd)
    ssh.close()

def check_llm_availability(llm_ip):
    try:
        req = requests.post(f"http://{llm_ip}:11434/api/generate", json={
            "model": "tinyllama",
            "prompt": "What is the capital of France?"
        }, timeout=30)
        # req.raise_for_status()
        logger.info(f"LLM Response:\n {req.status_code}\n{req.text}")
    except Exception as e:
        logger.info(f"Failed to connect to Ollama: {e}")

def get_instance_external_ip(project_id, zone, instance_name):
    credentials = service_account.Credentials.from_service_account_file(SA_GCP_KEY_FILE)
    compute = discovery.build('compute', 'v1', credentials=credentials)

    result = compute.instances().get(
        project=project_id,
        zone=zone,
        instance=instance_name
    ).execute()

    try:
        interfaces = result['networkInterfaces']
        access_configs = interfaces[0].get('accessConfigs', [])
        external_ip = access_configs[0].get('natIP') if access_configs else None
        return external_ip
    except (KeyError, IndexError):
        return None

def get_my_ip():
    my_ip = requests.get('https://api.ipify.org').text
    return my_ip

def set_firewall_ollama_rule(project_id, ip_address):
    credentials = service_account.Credentials.from_service_account_file(SA_GCP_KEY_FILE)
    compute = discovery.build('compute', 'v1', credentials=credentials)
    firewall_rule_name = 'allow-ollama-api-from-my-ip'
    source_ip_range = ip_address + '/32'
    firewall_body = {
        "name": firewall_rule_name,
        "direction": "INGRESS",
        "allowed": [{
            "IPProtocol": "tcp",
            "ports": ["11434"]
        }],
        "sourceRanges": [source_ip_range],
        "targetTags": ["ollama-server"],  # use this tag to mark VM that require ollama open port
        "description": "Allow port 11434 from my IP"
    }
    try:
        existing_rule = compute.firewalls().get(project=project_id, firewall=firewall_rule_name).execute()
        logger.info("Firewall rule already exists, updating it.")
        response = compute.firewalls().update(
            project=project_id,
            firewall=firewall_rule_name,
            body=firewall_body
        ).execute()
    except HttpError as e:
        if e.resp.status == 404:
            logger.info("Firewall rule does not exist, creating it.")
            response = compute.firewalls().insert(project=project_id, body=firewall_body).execute()
        else:
            logger.error(f"Failed to create or update firewall rule: {e}")
            raise
    logger.info(f"Firewall rule set result: {response}")

def wait_for_instance_running(project_id, zone, instance_name, timeout=300, interval=10):
    credentials = service_account.Credentials.from_service_account_file(SA_GCP_KEY_FILE)
    compute = discovery.build('compute', 'v1', credentials=credentials)
    elapsed = 0
    while elapsed < timeout:
        result = compute.instances().get(
            project=project_id,
            zone=zone,
            instance=instance_name
        ).execute()
        status = result.get("status")
        logger.info(f"[{elapsed}s] Instance status: {status}")
        if status == "RUNNING":
            logger.info("Instance is running.")
            return True
        time.sleep(interval)
        elapsed += interval
    logger.info("Timeout waiting for instance to become RUNNING.")
    return False

def list_zones_with_gpus(project_id, gpu_name):
    credentials = service_account.Credentials.from_service_account_file(SA_GCP_KEY_FILE)
    client = compute_v1.AcceleratorTypesClient(credentials=credentials)
    request = compute_v1.AggregatedListAcceleratorTypesRequest(project=project_id)
    response = client.aggregated_list(request=request)
    zones_with_gpu = set()
    for zone, scoped_list in response:
        if scoped_list.accelerator_types:
            for acc in scoped_list.accelerator_types:
                if acc.name == gpu_name:
                    zones_with_gpu.add(zone.split('/')[-1])
    return zones_with_gpu

def wait_for_operation(compute, project, zone, operation_name, timeout=300, interval=1):
    logger.info(f"Waiting for '{operation_name}' to complete with timeout in '{timeout}' seconds...")
    start_time = time.time()
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation_name
        ).execute()
        logger.info(f"Current state: {result['status']}")
        if result['status'] == 'DONE':
            if 'error' in result:
                raise Exception(f"There was error upon completion: {result['error']}")
            logger.info("Done successfully.")
            return
        if time.time() - start_time > timeout:
            raise TimeoutError(f"After timeout of '{timeout}' seconds operation is still running.")
        time.sleep(interval)

def stop_instance(project_id, zone, instance_name):
    logger.info("Stopping instance...")
    credentials = service_account.Credentials.from_service_account_file(SA_GCP_KEY_FILE)
    compute = discovery.build('compute', 'v1', credentials=credentials)
    response = compute.instances().stop(
        project=project_id,
        zone=zone,
        instance=instance_name
    ).execute()
    wait_for_operation(compute, project_id, zone, response['name'], interval=15)

if __name__ == "__main__":
    my_ip = get_my_ip()
    set_firewall_ollama_rule(PROJECT, my_ip)
    vm_zone = create_vm_with_gpu(PROJECT,INSTANCE_NAME)
    if not vm_zone:
        exit(1)
    wait_for_instance_running(PROJECT, vm_zone, INSTANCE_NAME)
    # stop_instance(PROJECT, vm_zone, INSTANCE_NAME)
    vm_ip = get_instance_external_ip(PROJECT, vm_zone, INSTANCE_NAME)
    if not vm_ip:
        exit(1)
    os.system(f"ssh-keygen -f ~/.ssh/known_hosts -R {vm_ip}")
    run_ssh_commands(vm_ip)
    start_ollama_and_load_model(vm_ip)
    check_llm_availability(vm_ip)
    stop_instance(PROJECT, vm_zone, INSTANCE_NAME)