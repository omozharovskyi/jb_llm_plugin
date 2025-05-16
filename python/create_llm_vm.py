from googleapiclient import discovery
import paramiko
import time
from google.oauth2 import service_account
from jb_llm_logger import logger
from google.cloud import compute_v1

PROJECT = "jb-llm-plugin"
ZONE = "europe-west4-a"
INSTANCE_NAME = "ollama-python-vm"

def create_vm_with_gpu():
    credentials = service_account.Credentials.from_service_account_file("sa-keys/jb-llm-plugin-sa.json")
    compute = discovery.build('compute', 'v1', credentials=credentials)
    config = {
        'name': INSTANCE_NAME,
        'machineType': f"zones/{ZONE}/machineTypes/n1-standard-4",
        'disks': [{
            'boot': True,
            'autoDelete': True,
            'initializeParams': {
                'sourceImage': 'projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts',
                'diskSizeGb': '30'
            }
        }],
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [{'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}]
        }],
        'scheduling': {'onHostMaintenance': 'TERMINATE', 'automaticRestart': False},
        'guestAccelerators': [{
            'acceleratorType': f'zones/{ZONE}/acceleratorTypes/nvidia-tesla-t4',
            'acceleratorCount': 1
        }],
        'metadata': {
            'items': [{'key': 'install-nvidia-driver', 'value': 'true'}]
        },
        'tags': {'items': ['http-server', 'https-server']},
    }
    operation = compute.instances().insert(
        project=PROJECT,
        zone=ZONE,
        body=config
    ).execute()
    logger.info(f"Instance creation started: {operation['name']}")
    wait_for_operation(compute,PROJECT,ZONE,operation['name'])

def run_ssh_commands(host_ip, username='ubuntu'):
    commands = [
        "sudo apt update -y && sudo apt upgrade -y",
        "nvidia-smi",
        "curl https://ollama.com/install.sh | sh",
        "ollama --version"
    ]
    key = paramiko.RSAKey.from_private_key_file("/path/to/private/key")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host_ip, username=username, pkey=key)
    for cmd in commands:
        print(f"Running: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        time.sleep(2)
        print(stdout.read().decode())
        print(stderr.read().decode())
    ssh.close()

def start_ollama_and_load_model(host_ip, username='ubuntu'):
    key = paramiko.RSAKey.from_private_key_file("/path/to/private/key")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host_ip, username=username, pkey=key)
    commands = [
        "ollama pull codellama:7b-python",
        "ollama run codellama:7b-python"
    ]
    for cmd in commands:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        time.sleep(10)
        print(stdout.read().decode())
        print(stderr.read().decode())
    ssh.close()

def get_instance_external_ip(project_id, zone, instance_name):
    from googleapiclient.discovery import build
    from oauth2client.client import GoogleCredentials

    credentials = GoogleCredentials.get_application_default()
    compute = build('compute', 'v1', credentials=credentials)

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

def wait_for_instance_running(project_id, zone, instance_name, timeout=300, interval=10):
    credentials = service_account.Credentials.from_service_account_file(
        "sa-keys/jb-llm-plugin-sa.json"
    )
    compute = discovery.build('compute', 'v1', credentials=credentials)

    elapsed = 0
    while elapsed < timeout:
        result = compute.instances().get(
            project=project_id,
            zone=zone,
            instance=instance_name
        ).execute()

        status = result.get("status")
        print(f"[{elapsed}s] Instance status: {status}")
        if status == "RUNNING":
            print("Instance is running.")
            return True

        time.sleep(interval)
        elapsed += interval

    print("Timeout waiting for instance to become RUNNING.")
    return False

def list_zones_with_gpus(project_id, gpu_name):
    credentials = service_account.Credentials.from_service_account_file("sa-keys/jb-llm-plugin-sa.json")
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



def wait_for_operation(compute, project, zone, operation_name, timeout=300):
    logger.info(f"Waiting for '{operation_name}' to complete with timeout in '{timeout}' seconds...")
    start_time = time.time()
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation_name
        ).execute()
        if result['status'] == 'DONE':
            if 'error' in result:
                raise Exception(f"There was error upon completion: {result['error']}")
            logger.info("Done successfully.")
            return
        if time.time() - start_time > timeout:
            raise TimeoutError(f"After timeout of '{timeout}' seconds operation is still runnung.")
        time.sleep(1)

if __name__ == "__main__":
    # create_vm_with_gpu()
    gpu_list = list_zones_with_gpus(PROJECT, 'nvidia-tesla-t4')
    logger.info(gpu_list)