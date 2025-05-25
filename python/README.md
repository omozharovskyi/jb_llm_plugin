# LLM VM Manager (MVP Implementation)

A command-line tool for managing Google Cloud Platform virtual machines for running Large Language Models (LLMs) with Ollama. This is the MVP (Minimum Viable Product) implementation of the JetBrains Plugin for On-Demand Cloud-Based LLM Integration project.

## Overview

This project provides a simple way to create, manage, and use GPU-accelerated virtual machines on Google Cloud Platform for running LLM inference with Ollama. It automates the process of:

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
llm_model = "tinyllama"  # Default LLM model to pull
retries = "10"
retry_interval = "10"
retry_timeout = "300"

[ssh]
user = "jbllm"  # SSH username
ssh_pub_key = "./sa-keys/jb-llm-plugin-ssh.pub"  # Path to SSH public key
ssh_secret_key = "./sa-keys/jb-llm-plugin-ssh"  # Path to SSH private key

[gcp]
project_name = "your-project-name"  # Your GCP project name
sa_gcp_key = "./sa-keys/your-service-account-key.json"  # Path to service account key
instance_name = "ollama-code-vm"  # Default VM instance name
machine_type = "n1-standard-1"  # VM machine type
image_family = "ubuntu-2204-lts"  # VM OS image
hdd_size = "10"  # Boot disk size in GB
gpu_accelerator = "nvidia-tesla-t4"  # GPU type
firewall_tag = "ollama-server"  # Firewall tag
zone_priority = "europe,us,*,asia"  # Zone priority for VM creation
firewall_rule_name = "allow-ollama-api-from-my-ip"  # Firewall rule name
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
- `memory_leak_detector.py`: Utilities for detecting memory leaks in tests

For more information about the integration tests, see [tests/integrationtests/README.md](tests/integrationtests/README.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENCE) file for details.
