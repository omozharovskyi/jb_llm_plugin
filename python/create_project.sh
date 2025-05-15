gcloud projects create jb-llm-plugin \
  --name="JetBrains AI Plugin Add-on" \
  --set-as-default

gcloud config set project jb-llm-plugin

gcloud beta billing accounts list

gcloud beta billing projects link jb-llm-plugin \
  --billing-account=YOUR_BILLING_ACCOUNT_ID

gcloud services enable \
  compute.googleapis.com \
  cloudresourcemanager.googleapis.com \
  servicemanagement.googleapis.com \
  iam.googleapis.com \
  cloudbilling.googleapis.com \
  --project="jb-llm-plugin"
