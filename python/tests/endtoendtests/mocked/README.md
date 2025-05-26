# Mocked End-to-End Tests for LLM VM Manager

This directory contains mocked end-to-end tests for the LLM VM Manager application. These tests use mocks to simulate interactions with external services like GCP and Ollama, allowing for fast and reliable testing without requiring actual cloud resources.

## Test Categories

The tests are organized into the following categories:

1. **Smoke Tests** (`test_smoke.py`): Basic functionality tests that verify the application can run and perform simple operations.
2. **Sanity Tests** (`test_sanity.py`): Core functionality tests that verify the main features of the application work correctly.
3. **Functional Tests** (`test_functional.py`): Tests for specific features of the application.
4. **Integration Tests** (`test_integration.py`): Tests that verify different components of the application work together correctly.
5. **Negative Tests** (`test_negative.py`): Tests that verify the application handles error conditions correctly.
6. **Security Tests** (`test_security.py`): Tests that verify the application is secure and protects sensitive information.
7. **Regression Tests** (`test_regression.py`): Tests that verify new changes don't break existing functionality.

## Running the Tests

### Prerequisites

- Python 3.8 or higher
- pytest
- pytest-cov (optional, for coverage reports)

### Installation

```bash
pip install pytest pytest-cov
```

### Running All Tests

To run all the mocked end-to-end tests:

```bash
cd python/tests/endtoendtests
pytest mocked/
```

### Running Tests by Category

To run tests from a specific category:

```bash
pytest mocked/ -m smoke
pytest mocked/ -m sanity
pytest mocked/ -m functional
pytest mocked/ -m integration
pytest mocked/ -m negative
pytest mocked/ -m security
pytest mocked/ -m regression
```

### Running with Coverage

To run the tests with coverage reporting:

```bash
pytest mocked/ --cov=python
```

## Memory Leak Detection

All tests are decorated with `@detect_leaks` to detect memory leaks during test execution. This helps ensure that the application doesn't leak memory, which could cause issues in production.

## Test Fixtures

The tests use the following fixtures defined in `conftest.py`:

- `memory_leak_detector`: A fixture for memory leak detection.
- `mock_config`: A fixture for mocked configuration.
- `mock_ssh_client`: A fixture for mocked SSH client.
- `mock_vm_manager`: A fixture for mocked GCP VM manager.
- `mock_requests`: A fixture for mocked requests module.
- `mock_args`: A fixture for mocked command-line arguments.
- `mock_parser`: A fixture for mocked argument parser.

## Adding New Tests

When adding new tests, follow these guidelines:

1. Use the appropriate test category marker (`@pytest.mark.smoke`, `@pytest.mark.sanity`, etc.).
2. Use the `@detect_leaks` decorator to detect memory leaks.
3. Use the fixtures defined in `conftest.py` to mock external dependencies.
4. Follow the naming convention `test_<feature>_<scenario>`.
5. Include a docstring that describes the test, including the test ID from the test plan.

Example:

```python
@pytest.mark.functional
@detect_leaks
def test_create_vm_with_custom_name(mock_vm_manager, mock_args, memory_leak_detector):
    """
    Test F1: Create VM with Custom Name
    Create a VM with a custom name.
    The VM should be created with the specified name.
    """
    # Test implementation
```