from google.oauth2 import service_account
from googleapiclient import discovery
from jb_llm_logger import logger

PROJECT = "jb-llm-plugin"
SA_GCP_KEY_FILE = "sa-keys/jb-llm-plugin-sa.json"
INSTANCE_NAME = "ollama-python-vm"

credentials = service_account.Credentials.from_service_account_file(SA_GCP_KEY_FILE)
compute = discovery.build('compute', 'v1', credentials=credentials)

def start_instance():
    zone = find_instance_zone(compute,PROJECT,INSTANCE_NAME)
    response = compute.instances().start(
        project=PROJECT,
        zone=zone,
        instance=INSTANCE_NAME
    ).execute()
    logger.info(f"Start VM: operation ID {response['name']}")

def find_instance_zone(compute, project, instance_name):
    result = compute.instances().aggregatedList(project=project).execute()
    # STAGING | RUNNING
    for zone, response in result['items'].items():
        for instance in response.get('instances', []):
            if instance['name'] == instance_name:
                return instance['zone'].split('/')[-1]
    return None


def stop_instance():
    zone = find_instance_zone(compute, PROJECT, INSTANCE_NAME)
    # STOPPING | TERMINATED
    response = compute.instances().stop(
        project=PROJECT,
        zone=zone,
        instance=INSTANCE_NAME
    ).execute()
    logger.info(f"Stop VM: operation ID {response['name']}")

if __name__ == "__main__":
    # start_instance()
    stop_instance()
