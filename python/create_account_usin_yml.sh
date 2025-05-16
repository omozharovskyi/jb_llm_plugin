gcloud iam roles create JBLLMComputeOperator \
  --project=jb-llm-plugin \
  --file=custom_compute_operator.yaml

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

