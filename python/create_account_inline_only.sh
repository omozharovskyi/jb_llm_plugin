gcloud iam roles create JBLLMComputeOperator \
  --project=jb-llm-plugin \
  --title="Role to manage VM with LLM" \
  --description="Role represents permissions that required for managing GCP VM with LLM" \
  --permissions="\
compute.instances.create,\
compute.instances.delete,\
compute.instances.get,\
compute.instances.list,\
compute.instances.start,\
compute.instances.stop,\
compute.instances.setTags,\
compute.firewalls.create,\
compute.firewalls.delete,\
compute.firewalls.get,\
compute.firewalls.list,\
compute.firewalls.update,\
compute.zones.list,\
compute.machineTypes.list,\
compute.networks.list,\
compute.subnetworks.list,\
resourcemanager.projects.get,\
compute.disks.create,\
compute.subnetworks.use,\
compute.subnetworks.useExternalIp,\
compute.instances.setMetadata" \
  --stage="GA"

gcloud iam service-accounts create jb-llm-serviceaccount \
  --description="Service Account for managing VMs" \
  --display-name="Account to manage VM and related resources to run LLM in GCP"

gcloud projects add-iam-policy-binding jb-llm-plugin \
  --member="serviceAccount:jb-llm-serviceaccount@jb-llm-plugin.iam.gserviceaccount.com" \
  --role="projects/jb-llm-plugin/roles/JBLLMComputeOperator"

gcloud beta billing accounts add-iam-policy-binding 012345-6789AB-CDEF01 \
  --member="serviceAccount:jb-llm-serviceaccount@jb-llm-plugin.iam.gserviceaccount.com" \
  --role="roles/billing.viewer"

gcloud iam service-accounts keys create ~/sa-key.json \
  --iam-account=jb-llm-serviceaccount@jb-llm-plugin.iam.gserviceaccount.com

