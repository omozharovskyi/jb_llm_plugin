# Integration Tests

This directory contains integration tests for the project. These tests verify that different components of the system work together correctly.

## Running the Tests

The integration tests can be run using the `run_integration_tests.sh` script:

```bash
./run_integration_tests.sh
```

By default, this will run all integration tests with memory usage monitoring.

## Memory Leak Detection

The script also supports running tests with memory leak detection to identify potential memory leaks:

```bash
./run_integration_tests.sh --leak-detection
```

You can adjust the memory leak threshold (in KB) using the `--threshold` option:

```bash
./run_integration_tests.sh --leak-detection --threshold 200
```

## Available Options

- `--leak-detection`: Run tests with memory leak detection
- `--threshold N`: Set memory leak threshold in KB (default: 100)
- `--help`: Show help message

## Memory Management

The integration tests have been designed to prevent memory exhaustion by:

1. Setting resource limits using `ulimit` to cap virtual memory and stack size
2. Monitoring memory usage during test execution
3. Forcing garbage collection after each test
4. Providing memory leak detection capabilities

## Test Files

The following test files are included:

- `test_main.py`: Tests for the main module
- `test_vm_operations.py`: Tests for VM operations
- `test_llm_vm_manager.py`: Tests for the LLM VM manager
- `test_ollama_utils.py`: Tests for Ollama utilities

## Memory Leak Detection Tools

For more advanced memory leak detection, you can use the `run_tests_with_leak_detection.py` script directly:

```bash
python -m python.tests.integrationtests.run_tests_with_leak_detection
```

This script uses Python's `tracemalloc` module to track memory allocations and identify potential leaks.

You can also run a specific test module:

```bash
python -m python.tests.integrationtests.run_tests_with_leak_detection --module python.tests.integrationtests.test_main
```

## Memory Leak Detector Module

The project includes a `memory_leak_detector.py` module that provides utilities for detecting memory leaks in tests:

- `MemoryLeakDetector`: A context manager for detecting memory leaks
- `detect_leaks`: A decorator for detecting memory leaks in functions
- `memory_usage_decorator`: A decorator for tracking memory usage of functions

These utilities can be used in individual test files to track memory usage and detect leaks.