# LLM VM Manager (MVP Implementation)

A command-line tool for managing Google Cloud Platform virtual machines for running Large Language Models (LLMs) with Ollama. This is the MVP (Minimum Viable Product) implementation of the JetBrains Plugin for On-Demand Cloud-Based LLM Integration project.

## Overview

This project provides a simple way to create, manage, and use GPU-accelerated virtual machines on Google Cloud Platform for running LLM inference with Ollama. It automates the process of:
Currently tested worflow with only one (default named) VM in cloud.

1. Creating VMs with GPU support
2. Installing and configuring Ollama
3. Pulling LLM models
4. Managing the VM lifecycle (start, stop, delete)
5. Setting up firewall rules for secure access

## Prerequisites

Before using this tool, you need:

1. A Google Cloud Platform account with billing enabled
   - See [create_gcp_account_readme.md](doc/create_gcp_account_readme.md) for detailed instructions
   - You'll need a Google Account and a Google payments profile linked to a valid credit/debit card
   - The guide includes steps for creating a GCP account and setting up a Cloud Billing account
   - Video tutorials are available in the document for visual guidance
2. GPU quota in your GCP project
   - See [request_gpu_manual.md](doc/request_gpu_readme.md) for instructions on requesting GPU quota
   - By default, new GCP accounts have a GPU quota of 0, so you'll need to request an increase
   - The request process involves filling out a form with justification for your GPU needs
   - Approval typically takes 24-48 hours
3. Python 3.8 or higher
4. SSH keys for connecting to the VMs
   - You can generate SSH keys using: `ssh-keygen -t rsa -f ./sa-keys/jb-llm-plugin-ssh -C jbllm`
   - Alternatively, you can use the Python script in [doc/scrypts/create_ssh_rsa_key.py](doc/scrypts/create_ssh_rsa_key.py)
   - To connect to your VM: `ssh -i ./sa-keys/jb-llm-plugin-ssh jbllm@VM_IP_ADDRESS`

## Installation

1. Clone this repository
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your GCP credentials:
   - Create a service account with the necessary permissions
   - Download the service account key as JSON
   - Place the key in the `sa-keys` directory

## Configuration

Edit the `config.toml` file to customize your setup:

```toml
# Common setup
my_ip_url = "https://api.ipify.org"
log_level = "info"
llm_model = "tinyllama:latest"
# | Model Name                          | Description & Use Case                                                                             | Minimal Hardware Requirements                                |
# |-------------------------------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------|
# | `codellama:7b-code`                 | Base Code Llama (7B) for code completion & infilling                                               | 16GB RAM; CPU OK, GPU accelerates (8GB)            |
# | `codellama:7b-python`               | Code Llama 7B fine-tuned on Python code                                                            | 16GB RAM min; GPU recommended (8GB+)               |
# | `codellama:7b-instruct`             | Instruction-tuned Code Llama 7B suitable for runnable code generation with natural-language prompt | 16GB RAM min; GPU recommended (8GB+)               |
# | `codellama:13b-code/python/instruct`| Code Llama 13B variants for enhanced code understanding & generation                               | 32GB RAM; strong CPU/GPU (e.g., RTX 3080+)         |
# | `codellama:34b-code/python/instruct`| Larger 34B variant, best for deep code generation & complex tasks                                  | 64GB RAM; high-end GPU like A100 recommended       |
# | `codellama:70b-code/python/instruct`| Top-tier 70B variant optimized for advanced code synthesis                                         | 128GB RAM; server GPUs (A100 40/80GB) or multi-GPU |
# | `starcoder2`                        | Open-code model for many languages (3B,7B,15B)                                                     | 32GB RAM; GPU advisable for 7B+                    |
# | `qwen2.5-coder`                     | Code-specific Qwen2.5 family (0.5B–32B), excels at code generation and reasoning                   | 8GB RAM for small; 64GB RAM + GPU for 7B+          |
retries = "10"
retry_interval = "10"
retry_timeout = "300"

[ssh]
user = "jbllm"
ssh_pub_key = "./sa-keys/jb-llm-plugin-ssh.pub"
ssh_secret_key = "./sa-keys/jb-llm-plugin-ssh"

[gcp]
project_name = "jb-llm-plugin"
sa_gcp_key = "./sa-keys/jb-llm-plugin-sa.json"
instance_name = "ollama-code-vm"
machine_type = "n1-standard-1"
# `machine_type` parameter defines the virtual machine (VM) type to be used when provisioning compute resources
# in Google Cloud Platform (GCP), such as with Compute Engine, Cloud Run, or Cloud Functions (2nd gen).
# machine_type = "n1-standard-1"
# This specifies the following:
# - Series: `n1-standard`
# - vCPUs: 1
# - Memory: 3.75 GB
# - Type: General-purpose virtual machine
# - Approx. price: ~$0.0475 per hour (in `us-central1` region)
# Choosing the appropriate machine type affects both cost and performance.
# GCP provides several machine families optimized for different workloads: general purpose, compute optimized, memory optimized, and GPU accelerated.
# | Series  | Purpose                     | Min Configuration           | Max Configuration              | Memory/vCPU | USD vCPU/hr |
# |---------|-----------------------------|-----------------------------|--------------------------------|-------------|-------------|
# | `e2`    | Gen.-purp., cost-optimized  | `e2-micro` (0.25 vCPU)      | `e2-highmem-16` (16 vCPU)      | 1–8 GB      | ~$0.033     |
# | `n1`    | General-purpose (legacy)    | `n1-standard-1` (1 vCPU)    | `n1-standard-96` (96 vCPU)     | 3.75 GB     | ~$0.0475    |
# | `n2`    | General-purpose, newer gen  | `n2-standard-2` (2 vCPU)    | `n2-highmem-128` (128 vCPU)    | 4–8 GB      | ~$0.052     |
# | `n2d`   | AMD-based general-purpose   | `n2d-standard-2` (2 vCPU)   | `n2d-highmem-224` (224 vCPU)   | 4–8 GB      | ~$0.041     |
# | `c2`    | Compute-optimized (Intel)   | `c2-standard-4` (4 vCPU)    | `c2-standard-60` (60 vCPU)     | 4 GB        | ~$0.063     |
# | `c3`    | Comp.-optim. (Intel/AMD)    | `c3-standard-4` (4 vCPU)    | `c3-standard-176` (176 vCPU)   | 4 GB        | ~$0.069     |
# | `m1/m2` | Memory-optimized            | `m1-megamem-96` (96 vCPU)   | `m2-ultramem-208` (208 vCPU)   | upto 28.9 GB| ~$0.228     |
# | `a2`    | Accelerator-optimized (GPU) | `a2-highgpu-1g` (1vCPU+1GPU)| `a2-megagpu-16g` (96vCPU+16GPU)| 85–96 GB    | ~$0.113+GPU |
# | `t2a`   | ARM-based (Ampere Altra)    | `t2a-standard-1` (1 vCPU)   | `t2a-standard-48` (48 vCPU)    | 4 GB        | ~$0.021     |
image_family = "ubuntu-2204-lts"
hdd_size = "10" # for large model specify not less than 50 (Gb)
gpu_accelerator = "nvidia-tesla-t4"
# ============================================================================
# Available NVIDIA GPUs in GCP (as for 01.07.2025)
# ============================================================================
# | Model                                | USD/hour | Architecture | Purpose                                   |
# |--------------------------------------|----------|--------------|-------------------------------------------|
# | nvidia-tesla-t4                      | 0.35     | Turing       | ML inference, general GPU tasks           |
# | nvidia-t4-virtual-workstation        | 0.55     | Turing       | Graphics workloads, virtual workstation   |
# | nvidia-l4                            | 0.71     | Ada Lovelace | AI inference, video analytics             |
# | nvidia-tesla-p4                      | 0.60     | Pascal       | ML inference, video processing            |
# | nvidia-tesla-p4-virtual-workstation  | 0.80     | Pascal       | Graphics workstation, light rendering     |
# | nvidia-tesla-p100                    | 1.46     | Pascal       | Training ML models, HPC                   |
# | nvidia-tesla-p100-virtual-workstation| 1.66     | Pascal       | Graphics workstation, compute workloads   |
# | nvidia-tesla-v100                    | 2.48     | Volta        | Training ML, HPC, general purpose compute |
# | nvidia-tesla-h100-80gb               | 6.98     | Hopper       | State-of-the-art ML/AI, LLM training      |
# | nvidia-a100-40gb                     | 3.67     | Ampere       | Large model training, HPC                 |
# | nvidia-a100-80gb                     | 6.25     | Ampere       | Very large ML training, HPC               |
# ============================================================================
firewall_tag = "ollama-server"
zone_priority = "europe,us,*,asia"
firewall_rule_name = "allow-ollama-api-from-my-ip"
```

## Usage

### Creating a VM with Ollama

```bash
python main.py create [--name VM_NAME] [--model MODEL_NAME]
```

This will:
1. Create a new VM with GPU support
2. Install and configure Ollama
3. Pull the specified LLM model
4. Set up a firewall rule to allow access to the Ollama API

### Starting a VM

```bash
python main.py start [--name VM_NAME]
```

### Stopping a VM

```bash
python main.py stop [--name VM_NAME]
```

### Deleting a VM

```bash
python main.py delete [--name VM_NAME]
```

### Listing VMs

```bash
python main.py list
```

### Getting Help

```bash
python main.py --help
```

## Project Structure

- `main.py`: Main entry point for the application
- `utils.py`: Utility functions for parsing arguments, loading configuration, etc.
- `vm_operations.py`: Functions for VM operations (create, start, stop, delete, list)
- `ollama_utils.py`: Functions for setting up Ollama and checking its availability
- `llm_vm_manager/`: Package containing VM management functionality
  - `llm_vm_base.py`: Base class for VM managers
  - `llm_vm_gcp.py`: GCP-specific VM manager implementation
  - `ssh_base.py`: Base class for SSH clients
  - `ssh_client.py`: SSH client implementation
  - `config.py`: Configuration loader
  - `jb_llm_logger.py`: Logging utilities
- `tests/`: Test suite
  - `unittests/`: Unit tests
  - `integrationtests/`: Integration tests
  - `structuretests/`: Structure tests
  - `endtoendtests/`: end-to-end tests
  - `memory_leak_detector.py`: Utilities for detecting memory leaks in tests

## Troubleshooting

### GPU Quota Issues

If you encounter the error "Quota 'GPUS_ALL_REGIONS' exceeded", you need to request a GPU quota increase:

1. Go to the [GCP Quotas page](https://console.cloud.google.com/iam-admin/quotas)
2. Filter for "GPU" and select "GPUS (all regions)"
3. Click "Edit Quotas" and request an increase (typically 1 is sufficient for testing)
4. Provide a justification for your request
5. Submit and wait for approval (typically 24-48 hours)

See [request_gpu_manual.md](doc/request_gpu_readme.md) for detailed step-by-step instructions.

### SSH Connection Issues

If you have trouble connecting to the VM via SSH:
1. Make sure your SSH keys are correctly generated and configured
2. Check that the VM is running (`python main.py list`)
3. Verify that your firewall rules allow SSH access
4. Try connecting manually: `ssh -i ./sa-keys/jb-llm-plugin-ssh jbllm@VM_IP_ADDRESS`
5. If you're still having issues, regenerate your SSH keys and update the VM's metadata

## Utility Scripts

The project includes several utility scripts in the `doc/scrypts` directory that can help with setting up and managing your GCP environment:

- `create_account_inline_only.sh` and `create_account_usin_yml.sh`: Scripts for creating GCP accounts
- `create_project.sh`: Script for creating a new GCP project
- `delete_project.sh`: Script for deleting a GCP project
- `create_ssh_rsa_key.py`: Python script for generating SSH keys programmatically
- `setup_gcp_env.py`: Script for setting up the GCP environment
- `custom_compute_operator.yaml`: YAML configuration for compute resources

These scripts can be useful for automating various aspects of the setup process.

## Testing

The project includes a comprehensive test suite in the `tests` directory:

- `unittests`: Unit tests for individual components
- `integrationtests`: Tests for interactions between components
- `structuretests`: Tests for code structure and organization

## License

This project is licensed under the MIT License - see the [LICENSE](LICENCE) file for details.
