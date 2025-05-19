from google.oauth2 import service_account
from googleapiclient import discovery
from jb_llm_logger import logger

SA_GCP_KEY_FILE = "sa-keys/jb-llm-plugin-sa.json"
PROJECT = "jb-llm-plugin"

credentials = service_account.Credentials.from_service_account_file(SA_GCP_KEY_FILE)
compute = discovery.build('compute', 'v1', credentials=credentials)

def list_instances():
    result = compute.instances().aggregatedList(project=PROJECT).execute()
    instances = []
    for zone, response in result['items'].items():
        if 'instances' in response:
            for instance in response['instances']:
                instances.append(instance)
    if not instances:
        logger.info("No instances found.")
        return
    logger.info(f"Instances in project '{PROJECT}':\n")
    for instance in instances:
        name = instance["name"]
        status = instance["status"]  # RUNNING / TERMINATED / STOPPING
        instance_zone = instance["zone"].split('/')[-1]
        machine_type = instance["machineType"].split("/")[-1]
        logger.info(f"{name} | {status} | type: {machine_type} | zone: {instance_zone}")

if __name__ == "__main__":
    list_instances()
