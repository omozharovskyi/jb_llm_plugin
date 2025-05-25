import time
import base64
from googleapiclient.discovery import build
from oauth2client.client import GoogleCredentials

PROJECT_ID = "your-project-id"
SERVICE_ACCOUNT_ID = "ollama-vm-sa"
SERVICE_ACCOUNT_DISPLAY_NAME = "Service Account for Ollama VM"
KEY_OUTPUT_PATH = "ollama-vm-key.json"
REQUIRED_APIS = [
    "compute.googleapis.com",
    "iam.googleapis.com",
    "serviceusage.googleapis.com"
]
ROLES = [
    "roles/compute.admin",
    "roles/iam.serviceAccountUser",
    "roles/storage.admin"
]

credentials = GoogleCredentials.get_application_default()


def enable_apis():
    print("Enabling required APIs...")
    service = build('serviceusage', 'v1', credentials=credentials)
    for api in REQUIRED_APIS:
        name = f'projects/{PROJECT_ID}/services/{api}'
        try:
            service.services().enable(name=name).execute()
            print(f"Enabled API: {api}")
            time.sleep(1)
        except Exception as e:
            print(f"Error enabling {api}: {e}")


def create_service_account():
    print("Creating service account...")
    iam = build('iam', 'v1', credentials=credentials)
    sa_body = {
        "accountId": SERVICE_ACCOUNT_ID,
        "serviceAccount": {
            "displayName": SERVICE_ACCOUNT_DISPLAY_NAME
        }
    }
    try:
        request = iam.projects().serviceAccounts().create(
            name=f'projects/{PROJECT_ID}',
            body=sa_body
        )
        response = request.execute()
        email = response['email']
        print(f"Created service account: {email}")
        return email
    except Exception as e:
        if "already exists" in str(e):
            print("Service account already exists, continuing...")
            return f"{SERVICE_ACCOUNT_ID}@{PROJECT_ID}.iam.gserviceaccount.com"
        raise


def assign_roles(service_account_email):
    print("Assigning IAM roles...")
    crm = build("cloudresourcemanager", "v1", credentials=credentials)
    policy = crm.projects().getIamPolicy(resource=PROJECT_ID, body={}).execute()

    bindings = policy.get("bindings", [])
    for role in ROLES:
        member = f"serviceAccount:{service_account_email}"
        # Check if role already exists
        existing = next((b for b in bindings if b["role"] == role), None)
        if existing:
            if member not in existing["members"]:
                existing["members"].append(member)
        else:
            bindings.append({
                "role": role,
                "members": [member]
            })

    policy["bindings"] = bindings
    crm.projects().setIamPolicy(
        resource=PROJECT_ID,
        body={"policy": policy}
    ).execute()
    print(f"Assigned roles to {service_account_email}")


def generate_key(service_account_email):
    print("⏳ Generating service account key...")
    iam = build("iam", "v1", credentials=credentials)
    key = iam.projects().serviceAccounts().keys().create(
        name=f"projects/{PROJECT_ID}/serviceAccounts/{service_account_email}",
        body={"privateKeyType": "TYPE_GOOGLE_CREDENTIALS_FILE"}
    ).execute()

    key_data = key["privateKeyData"]
    with open(KEY_OUTPUT_PATH, "wb") as f:
        f.write(base64.b64decode(key_data))
    print(f"Key saved to {KEY_OUTPUT_PATH}")


if __name__ == "__main__":
    enable_apis()
    sa_email = create_service_account()
    assign_roles(sa_email)
    generate_key(sa_email)
