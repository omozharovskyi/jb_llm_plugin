from google.oauth2 import service_account
from googleapiclient import discovery
from googleapiclient.errors import HttpError


SA_GCP_KEY_FILE = "sa-keys/jb-llm-plugin-sa.json"
PROJECT = "jb-llm-plugin"
INSTANCE_NAME = "ollama-python-vm"

credentials = service_account.Credentials.from_service_account_file(SA_GCP_KEY_FILE)
compute = discovery.build('compute', 'v1', credentials=credentials)

def instance_exists():
    try:
        compute.instances().get(
            project=PROJECT,
            zone=ZONE,
            instance=INSTANCE_NAME
        ).execute()
        return True
    except HttpError as e:
        if e.resp.status == 404:
            return False
        raise

def find_instance_zone(compute, project, instance_name):
    result = compute.instances().aggregatedList(project=project).execute()
    # STAGING | RUNNING
    for zone, response in result['items'].items():
        for instance in response.get('instances', []):
            if instance['name'] == instance_name:
                return instance['zone'].split('/')[-1]
    return None


def delete_instance():
    zone = find_instance_zone(compute, PROJECT, INSTANCE_NAME)
    # STOPPING
    if zone:
        response = compute.instances().delete(
            project=PROJECT,
            zone=zone,
            instance=INSTANCE_NAME
        ).execute()
        print(f"Delete VM: operation ID {response['name']}")
    else:
        print(f"Instance '{INSTANCE_NAME}' not found in zone '{zone}'")

if __name__ == "__main__":
    delete_instance()
