# End-to-End Testing Plan for LLM VM Manager (MVP Implementation)

This document outlines a comprehensive end-to-end testing plan for the LLM VM Manager application, which is the MVP (Minimum Viable Product) implementation of the JetBrains Plugin for On-Demand Cloud-Based LLM Integration project. The plan covers all possible test cases, including negative scenarios, and categorizes them by priority and purpose.

## Dependencies

The LLM VM Manager application has the following dependencies:

1. **Python Libraries**:
   - paramiko: For SSH connections
   - requests: For HTTP requests
   - google.oauth2: For Google OAuth2 authentication
   - googleapiclient: For Google API client
   - tomllib: For TOML file parsing

2. **External Services**:
   - Google Cloud Platform (GCP): For VM management
   - Ollama: For running LLM models

3. **Configuration**:
   - config.toml: Contains settings for the application
   - SSH keys: For connecting to VMs
   - GCP service account key: For authenticating with GCP

## Test Categories

### Smoke Tests

Smoke tests verify that the basic functionality of the application works correctly. These tests should be run first to ensure that the application is stable enough for further testing.

| ID | Test Case       | Priority | Description                                 | Expected Result                                    | Possible to automate                                       | Automation Status | Mocked/Live    |
|----|-----------------|----------|---------------------------------------------|----------------------------------------------------|------------------------------------------------------------|-------------------|----------------|
| S1 | Help Command    | High     | Run the application with the --help flag    | The application should display help information    | Yes - Simple CLI command execution and output verification | Not automated     | Mocked + Live  |
| S2 | Version Command | High     | Run the application with the --version flag | The application should display version information | Yes - Simple CLI command execution and output verification | Not automated     | Mocked + Live  |
| S3 | List Command    | High     | Run the application with the list command   | The application should list all VM instances       | Yes - CLI command execution with mocked GCP responses      | Not automated     | Mocked         |

### Sanity Tests

Sanity tests verify that the core functionality of the application works correctly. These tests should be run after smoke tests to ensure that the application's core features are working as expected.

| ID  | Test Case         | Priority | Description                   | Expected Result                         | Possible to automate                                     | Automation Status | Mocked/Live    |
|-----|-------------------|----------|-------------------------------|-----------------------------------------|----------------------------------------------------------|-------------------|----------------|
| SN1 | Create VM         | High     | Create a new VM instance      | The VM should be created successfully   | Yes - Using GCP API mocks or real GCP test project       | Not automated     | Mocked + Live  |
| SN2 | Start VM          | High     | Start an existing VM instance | The VM should start successfully        | Yes - Using GCP API mocks or real GCP test project       | Not automated     | Mocked + Live  |
| SN3 | Stop VM           | High     | Stop a running VM instance    | The VM should stop successfully         | Yes - Using GCP API mocks or real GCP test project       | Not automated     | Mocked + Live  |
| SN4 | Delete VM         | High     | Delete a VM instance          | The VM should be deleted successfully   | Yes - Using GCP API mocks or real GCP test project       | Not automated     | Mocked + Live  |
| SN5 | Ollama Setup      | High     | Set up Ollama on a VM         | Ollama should be set up successfully    | Yes - Using SSH mocks and command execution verification | Not automated     | Mocked + Live  |
| SN6 | Ollama Model Pull | High     | Pull an LLM model to Ollama   | The model should be pulled successfully | Yes - Using SSH and API mocks to simulate model pulling  | Not automated     | Mocked + Live  |

### Functional Tests

Functional tests verify that specific features of the application work correctly. These tests should be run after sanity tests to ensure that all features are working as expected.

| ID | Test Case                   | Priority | Description                            | Expected Result                                                   | Possible to automate                                       | Automation Status | Mocked/Live    |
|----|-----------------------------|----------|----------------------------------------|-------------------------------------------------------------------|------------------------------------------------------------|-------------------|----------------|
| F1 | Create VM with Custom Name  | Medium   | Create a VM with a custom name         | The VM should be created with the specified name                  | Yes - Using GCP API mocks with name parameter verification | Not automated     | Mocked         |
| F2 | Create VM with Custom Model | Medium   | Create a VM and pull a custom model    | The VM should be created and the specified model should be pulled | Yes - Using GCP API and Ollama API mocks                   | Not automated     | Mocked         |
| F3 | Start VM with Custom Name   | Medium   | Start a VM with a custom name          | The VM with the specified name should start                       | Yes - Using GCP API mocks with name parameter verification | Not automated     | Mocked         |
| F4 | Stop VM with Custom Name    | Medium   | Stop a VM with a custom name           | The VM with the specified name should stop                        | Yes - Using GCP API mocks with name parameter verification | Not automated     | Mocked         |
| F5 | Delete VM with Custom Name  | Medium   | Delete a VM with a custom name         | The VM with the specified name should be deleted                  | Yes - Using GCP API mocks with name parameter verification | Not automated     | Mocked         |
| F6 | Firewall Rule Creation      | Medium   | Create a firewall rule for Ollama API  | The firewall rule should be created successfully                  | Yes - Using GCP API mocks for firewall rules               | Not automated     | Mocked         |
| F7 | SSH Connection              | Medium   | Connect to a VM via SSH                | The SSH connection should be established successfully             | Yes - Using paramiko mocks or test SSH server              | Not automated     | Mocked + Live  |
| F8 | Ollama API Availability     | Medium   | Check if Ollama API is available       | The Ollama API should be accessible                               | Yes - Using requests mocks or test Ollama server           | Not automated     | Mocked         |
| F9 | Ollama Model Availability   | Medium   | Check if a specific model is available | The specified model should be available                           | Yes - Using Ollama API mocks for model availability        | Not automated     | Mocked         |

### Integration Tests

Integration tests verify that different components of the application work together correctly. These tests should be run after functional tests to ensure that all components are integrated properly.

| ID | Test Case                              | Priority | Description                                                    | Expected Result                                                                         | Possible to automate                                      | Automation Status | Mocked/Live    |
|----|----------------------------------------|----------|----------------------------------------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------------------|-------------------|----------------|
| I1 | Create and Start VM                    | Medium   | Create a VM and then start it                                  | The VM should be created and started successfully                                       | Yes - Using GCP API mocks for both operations in sequence | Not automated     | Mocked + Live  |
| I2 | Start and Stop VM                      | Medium   | Start a VM and then stop it                                    | The VM should be started and stopped successfully                                       | Yes - Using GCP API mocks for both operations in sequence | Not automated     | Mocked + Live  |
| I3 | Create, Start, and Delete VM           | Medium   | Create a VM, start it, and then delete it                      | The VM should be created, started, and deleted successfully                             | Yes - Using GCP API mocks for all operations in sequence  | Not automated     | Mocked + Live  |
| I4 | Create VM and Check Ollama             | Medium   | Create a VM and check if Ollama is available                   | The VM should be created and Ollama should be available                                 | Yes - Using GCP API and Ollama API mocks                  | Not automated     | Mocked + Live  |
| I5 | Create VM, Pull Model, and Check Model | Medium   | Create a VM, pull a model, and check if the model is available | The VM should be created, the model should be pulled, and the model should be available | Yes - Using GCP API, SSH, and Ollama API mocks            | Not automated     | Mocked + Live  |

### Negative Tests

Negative tests verify that the application handles error conditions correctly. These tests should be run to ensure that the application is robust and can handle unexpected situations.

| ID   | Test Case                   | Priority | Description                                            | Expected Result                                                  | Possible to automate                                        | Automation Status | Mocked/Live |
|------|-----------------------------|----------|--------------------------------------------------------|------------------------------------------------------------------|-------------------------------------------------------------|-------------------|-------------|
| N1   | Create Existing VM          | Medium   | Try to create a VM that already exists                 | The application should display a warning and not create a new VM | Yes - Using GCP API mocks to simulate existing VM           | Not automated     | Mocked      |
| N2   | Start Non-existent VM       | Medium   | Try to start a VM that doesn't exist                   | The application should display an error message                  | Yes - Using GCP API mocks to simulate non-existent VM       | Not automated     | Mocked      |
| N3   | Stop Non-existent VM        | Medium   | Try to stop a VM that doesn't exist                    | The application should display an error message                  | Yes - Using GCP API mocks to simulate non-existent VM       | Not automated     | Mocked      |
| N4   | Delete Non-existent VM      | Medium   | Try to delete a VM that doesn't exist                  | The application should display an error message                  | Yes - Using GCP API mocks to simulate non-existent VM       | Not automated     | Mocked      |
| N5   | Invalid Configuration       | Medium   | Run the application with an invalid configuration file | The application should display an error message                  | Yes - Using invalid config file and checking error handling | Not automated     | Mocked      |
| N6   | Missing SSH Key             | Medium   | Run the application with a missing SSH key             | The application should display an error message                  | Yes - Using file system mocks to simulate missing key       | Not automated     | Mocked      |
| N7   | Missing GCP Key             | Medium   | Run the application with a missing GCP key             | The application should display an error message                  | Yes - Using file system mocks to simulate missing key       | Not automated     | Mocked      |
| N8   | Invalid GCP Project         | Medium   | Run the application with an invalid GCP project        | The application should display an error message                  | Yes - Using GCP API mocks to simulate invalid project       | Not automated     | Mocked      |
| N9   | Invalid VM Name             | Medium   | Run the application with an invalid VM name            | The application should display an error message                  | Yes - Using input validation tests with invalid names       | Not automated     | Mocked      |
| N10  | Invalid Model Name          | Medium   | Run the application with an invalid model name         | The application should display an error message                  | Yes - Using input validation tests with invalid model names | Not automated     | Mocked      |
| N11  | Network Failure             | Medium   | Simulate a network failure during VM creation          | The application should handle the failure gracefully             | Yes - Using network mocks to simulate connection failures   | Not automated     | Mocked      |
| N12  | GCP API Failure             | Medium   | Simulate a GCP API failure                             | The application should handle the failure gracefully             | Yes - Using GCP API mocks to simulate API errors            | Not automated     | Mocked      |
| N13  | SSH Connection Failure      | Medium   | Simulate an SSH connection failure                     | The application should handle the failure gracefully             | Yes - Using SSH mocks to simulate connection failures       | Not automated     | Mocked      |
| N14  | Ollama Installation Failure | Medium   | Simulate an Ollama installation failure                | The application should handle the failure gracefully             | Yes - Using SSH mocks to simulate installation failures     | Not automated     | Mocked      |
| N15  | Model Pull Failure          | Medium   | Simulate a model pull failure                          | The application should handle the failure gracefully             | Yes - Using Ollama API mocks to simulate pull failures      | Not automated     | Mocked      |

### Performance Tests

Performance tests verify that the application performs well under various conditions. These tests should be run to ensure that the application is efficient and responsive.

| ID | Test Case            | Priority | Description                                  | Expected Result                                         | Possible to automate                                          | Automation Status | Mocked/Live |
|----|----------------------|----------|----------------------------------------------|---------------------------------------------------------|---------------------------------------------------------------|-------------------|-------------|
| P1 | VM Creation Time     | Low      | Measure the time it takes to create a VM     | The VM should be created within a reasonable time       | Yes - Using timing decorators and real or mocked GCP API      | Not automated     | Live        |
| P2 | VM Start Time        | Low      | Measure the time it takes to start a VM      | The VM should start within a reasonable time            | Yes - Using timing decorators and real or mocked GCP API      | Not automated     | Live        |
| P3 | VM Stop Time         | Low      | Measure the time it takes to stop a VM       | The VM should stop within a reasonable time             | Yes - Using timing decorators and real or mocked GCP API      | Not automated     | Live        |
| P4 | VM Deletion Time     | Low      | Measure the time it takes to delete a VM     | The VM should be deleted within a reasonable time       | Yes - Using timing decorators and real or mocked GCP API      | Not automated     | Live        |
| P5 | Ollama Setup Time    | Low      | Measure the time it takes to set up Ollama   | Ollama should be set up within a reasonable time        | Yes - Using timing decorators and real or mocked SSH commands | Not automated     | Live        |
| P6 | Model Pull Time      | Low      | Measure the time it takes to pull a model    | The model should be pulled within a reasonable time     | Yes - Using timing decorators and real or mocked Ollama API   | Not automated     | Live        |
| P7 | Multiple VM Creation | Low      | Create multiple VMs and measure the time     | Multiple VMs should be created within a reasonable time | Yes - Using timing decorators and parallel execution tests    | Not automated     | Live        |

### Security Tests

Security tests verify that the application is secure and protects sensitive information. These tests should be run to ensure that the application follows security best practices.

| ID  | Test Case                   | Priority | Description                              | Expected Result                                                    | Possible to automate                                                | Automation Status | Mocked/Live    |
|-----|-----------------------------|----------|------------------------------------------|--------------------------------------------------------------------|---------------------------------------------------------------------|-------------------|----------------|
| SE1 | SSH Key Protection          | High     | Verify that SSH keys are protected       | SSH keys should be stored securely and not exposed                 | Partially - Can check file permissions but not all security aspects | Not automated     | Mocked         |
| SE2 | GCP Key Protection          | High     | Verify that GCP keys are protected       | GCP keys should be stored securely and not exposed                 | Partially - Can check file permissions but not all security aspects | Not automated     | Mocked         |
| SE3 | Firewall Rule Effectiveness | High     | Verify that firewall rules are effective | Only authorized IPs should be able to access the Ollama API        | Yes - Using network scanning tools or GCP API verification          | Not automated     | Mocked + Live  |
| SE4 | Secure SSH Connection       | High     | Verify that SSH connections are secure   | SSH connections should use encryption and key-based authentication | Yes - Using paramiko security settings verification                 | Not automated     | Mocked + Live  |
| SE5 | Secure API Communication    | High     | Verify that API communication is secure  | API communication should use HTTPS                                 | Yes - Using requests library with SSL verification                  | Not automated     | Mocked         |

### Regression Tests

Regression tests verify that new changes don't break existing functionality. These tests should be run after making changes to the application to ensure that everything still works as expected.

| ID | Test Case               | Priority | Description                                                    | Expected Result                                                 | Possible to automate                                             | Automation Status | Mocked/Live    |
|----|-------------------------|----------|----------------------------------------------------------------|-----------------------------------------------------------------|------------------------------------------------------------------|-------------------|----------------|
| R1 | Full Workflow           | High     | Run a full workflow (create, start, stop, delete)              | All operations should complete successfully                     | Yes - Using GCP API mocks for all operations in sequence         | Not automated     | Mocked + Live  |
| R2 | Configuration Changes   | Medium   | Change configuration settings and verify that they take effect | The application should use the new configuration settings       | Yes - Using different config files and verifying behavior        | Not automated     | Mocked         |
| R3 | Different VM Types      | Medium   | Create VMs with different machine types                        | VMs with different machine types should be created successfully | Yes - Using GCP API mocks with different machine type parameters | Not automated     | Mocked         |
| R4 | Different GPU Types     | Medium   | Create VMs with different GPU types                            | VMs with different GPU types should be created successfully     | Yes - Using GCP API mocks with different GPU type parameters     | Not automated     | Mocked         |
| R5 | Different OS Images     | Medium   | Create VMs with different OS images                            | VMs with different OS images should be created successfully     | Yes - Using GCP API mocks with different OS image parameters     | Not automated     | Mocked         |
| R6 | Different LLM Models    | Medium   | Pull different LLM models                                      | Different LLM models should be pulled successfully              | Yes - Using Ollama API mocks for different models                | Not automated     | Mocked         |

## Test Execution Strategy

1. **Preparation**:
   - Set up a test GCP project
   - Create test SSH keys
   - Create a test configuration file

2. **Execution Order**:
   1. Smoke Tests
   2. Sanity Tests
   3. Functional Tests
   4. Integration Tests
   5. Negative Tests
   6. Performance Tests
   7. Security Tests
   8. Regression Tests

3. **Reporting**:
   - Document test results
   - Report any failures or issues
   - Track performance metrics

## Automation Considerations

1. **Test Framework**:
   - Use pytest for test automation
   - Create fixtures for common setup and teardown operations
   - Use parameterization for testing with different inputs

2. **Mocking**:
   - Mock GCP API calls for faster and more reliable testing
   - Mock SSH connections for testing SSH-related functionality
   - Mock Ollama API for testing Ollama-related functionality

3. **CI/CD Integration**:
   - Integrate tests with CI/CD pipeline
   - Run smoke and sanity tests on every commit
   - Run all tests before releases

## Conclusion

This end-to-end testing plan provides a comprehensive approach to testing the LLM VM Manager application. By following this plan, we can ensure that the application is stable, functional, and reliable.
