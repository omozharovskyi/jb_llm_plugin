# Acceptance Testing Plan for LLM VM Manager (MVP Implementation)

This document outlines the acceptance testing plan for the LLM VM Manager application, which is the MVP (Minimum Viable Product) implementation of the JetBrains Plugin for On-Demand Cloud-Based LLM Integration project. Acceptance testing is conducted to ensure that the application meets the business requirements and is ready for production use. This plan covers both current functionality and potential future enhancements.

## Purpose

The purpose of acceptance testing is to:
1. Verify that the application meets the business requirements
2. Ensure that the application is usable from an end-user perspective
3. Validate that the application works correctly in real-world scenarios
4. Identify any issues that might affect user acceptance

## Test Environment

### Hardware Requirements
- Computer with internet connection
- Sufficient RAM and CPU for running Python applications

### Software Requirements
- Python 3.8 or higher
- Required Python packages (paramiko, requests, google.oauth2, googleapiclient, tomllib)
- SSH key generation tools

### External Services
- Google Cloud Platform account with billing enabled
- GPU quota in the GCP project
- Internet access to download Ollama and LLM models

### Configuration
- Valid config.toml file
- Valid SSH keys
- Valid GCP service account key

## Acceptance Test Scenarios

### User Story 1: Setting Up the Environment
**As a** data scientist or ML engineer  
**I want to** set up the LLM VM Manager environment  
**So that** I can start using it to manage VMs for LLM inference

#### Scenario 1.1: Installation and Configuration
1. Clone the repository
2. Install required dependencies
3. Generate SSH keys
4. Create a GCP service account and download the key
5. Configure the config.toml file
6. Verify that the application can be run with the help command

**Expected Result:** The application is installed and configured correctly, and the help command displays usage information.

#### Scenario 1.2: Configuration Validation
1. Intentionally provide an invalid configuration (e.g., missing SSH key)
2. Run any command
3. Verify that the application provides a clear error message

**Expected Result:** The application detects the invalid configuration and provides a helpful error message.

### User Story 2: Creating and Managing VMs
**As a** data scientist or ML engineer  
**I want to** create and manage VMs for running LLM inference  
**So that** I can use LLMs without maintaining local infrastructure

#### Scenario 2.1: Creating a VM with Default Settings
1. Run the create command without additional parameters
2. Wait for the VM to be created
3. Verify that the VM is created with the default name from the config
4. Verify that Ollama is installed and the default model is pulled

**Expected Result:** A VM is created with the default settings, Ollama is installed, and the default model is pulled.

#### Scenario 2.2: Creating a VM with Custom Settings
1. Run the create command with a custom name and model
2. Wait for the VM to be created
3. Verify that the VM is created with the specified name
4. Verify that Ollama is installed and the specified model is pulled

**Expected Result:** A VM is created with the custom settings, Ollama is installed, and the specified model is pulled.

#### Scenario 2.3: Starting a VM
1. Create a VM if one doesn't exist
2. Stop the VM if it's running
3. Run the start command
4. Verify that the VM starts
5. Verify that Ollama is accessible

**Expected Result:** The VM starts and Ollama is accessible.

#### Scenario 2.4: Stopping a VM
1. Create a VM if one doesn't exist
2. Start the VM if it's not running
3. Run the stop command
4. Verify that the VM stops

**Expected Result:** The VM stops.

#### Scenario 2.5: Deleting a VM
1. Create a VM if one doesn't exist
2. Run the delete command
3. Verify that the VM is deleted

**Expected Result:** The VM is deleted.

#### Scenario 2.6: Listing VMs
1. Create one or more VMs
2. Run the list command
3. Verify that all created VMs are listed

**Expected Result:** All created VMs are listed.

### User Story 3: Using Ollama for LLM Inference
**As a** data scientist or ML engineer  
**I want to** use Ollama for LLM inference on a remote VM  
**So that** I can run LLM models without local GPU resources

#### Scenario 3.1: Accessing Ollama API
1. Create a VM if one doesn't exist
2. Start the VM if it's not running
3. Verify that the Ollama API is accessible at http://<VM_IP>:11434
4. Make a simple API request to Ollama

**Expected Result:** The Ollama API is accessible and responds to requests.

#### Scenario 3.2: Running LLM Inference
1. Create a VM if one doesn't exist
2. Start the VM if it's not running
3. Use the Ollama API to run inference with the default model
4. Verify that the model returns a response

**Expected Result:** The model returns a valid response.

### User Story 4: Error Handling and Recovery
**As a** data scientist or ML engineer  
**I want to** have robust error handling and recovery mechanisms  
**So that** I can troubleshoot issues and recover from failures

#### Scenario 4.1: Handling Network Failures
1. Simulate a network failure during VM creation
2. Verify that the application handles the failure gracefully
3. Verify that the application provides a clear error message

**Expected Result:** The application handles the network failure gracefully and provides a clear error message.

#### Scenario 4.2: Handling GCP API Failures
1. Simulate a GCP API failure
2. Verify that the application handles the failure gracefully
3. Verify that the application provides a clear error message

**Expected Result:** The application handles the GCP API failure gracefully and provides a clear error message.

#### Scenario 4.3: Handling SSH Connection Failures
1. Simulate an SSH connection failure
2. Verify that the application handles the failure gracefully
3. Verify that the application provides a clear error message

**Expected Result:** The application handles the SSH connection failure gracefully and provides a clear error message.

## Future Enhancement Acceptance Tests

### User Story 5: Multi-VM Management
**As a** data scientist or ML engineer  
**I want to** manage multiple VMs with different models  
**So that** I can run different LLMs for different purposes

#### Scenario 5.1: Creating Multiple VMs
1. Run the create command with different names and models multiple times
2. Verify that multiple VMs are created with different names
3. Verify that each VM has the specified model

**Expected Result:** Multiple VMs are created with different names and models.

#### Scenario 5.2: Managing Multiple VMs
1. Create multiple VMs
2. Start, stop, and delete specific VMs by name
3. Verify that the operations affect only the specified VMs

**Expected Result:** Operations on specific VMs do not affect other VMs.

### User Story 6: Cost Management
**As a** data scientist or ML engineer  
**I want to** monitor and manage the cost of running VMs  
**So that** I can stay within budget

#### Scenario 6.1: Cost Estimation
1. Run a hypothetical cost estimation command
2. Verify that the application provides an estimate of the cost of running the VM

**Expected Result:** The application provides a cost estimate.

#### Scenario 6.2: Cost Alerts
1. Configure a cost threshold
2. Run VMs until the cost approaches the threshold
3. Verify that the application provides an alert

**Expected Result:** The application provides a cost alert when the threshold is approached.

### User Story 7: Performance Monitoring
**As a** data scientist or ML engineer  
**I want to** monitor the performance of my VMs and LLM models  
**So that** I can optimize resource usage and response times

#### Scenario 7.1: VM Performance Monitoring
1. Run a hypothetical performance monitoring command
2. Verify that the application provides information about VM performance

**Expected Result:** The application provides VM performance information.

#### Scenario 7.2: LLM Performance Monitoring
1. Run a hypothetical LLM performance monitoring command
2. Verify that the application provides information about LLM performance

**Expected Result:** The application provides LLM performance information.

### User Story 8: Integration with Other Cloud Providers
**As a** data scientist or ML engineer  
**I want to** use the application with other cloud providers  
**So that** I can choose the most cost-effective or feature-rich provider

#### Scenario 8.1: AWS Integration
1. Configure the application for AWS
2. Run the create command
3. Verify that a VM is created on AWS

**Expected Result:** A VM is created on AWS.

#### Scenario 8.2: Azure Integration
1. Configure the application for Azure
2. Run the create command
3. Verify that a VM is created on Azure

**Expected Result:** A VM is created on Azure.

## Test Execution

### Test Data
- Valid and invalid configuration files
- Valid and invalid SSH keys
- Valid and invalid GCP service account keys
- Various VM names and model names

### Test Schedule
1. Environment setup tests
2. VM management tests
3. Ollama usage tests
4. Error handling tests
5. Future enhancement tests (when implemented)

### Test Reporting
- Document all test results
- Report any failures or issues
- Track performance metrics
- Provide recommendations for improvements

## Acceptance Criteria

The application will be considered ready for production use when:
1. All current functionality acceptance tests pass
2. No critical or high-severity issues are found
3. The application meets all business requirements
4. The application is usable from an end-user perspective

Future enhancements will be evaluated separately when implemented.

## Conclusion

This acceptance testing plan provides a comprehensive approach to validating the LLM VM Manager application from an end-user perspective. By following this plan, we can ensure that the application meets the business requirements and is ready for production use.
