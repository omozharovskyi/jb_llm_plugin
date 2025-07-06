#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")/../../.." || exit 1

# Set PYTHONPATH to include the python directory
export PYTHONPATH="$PWD/python:$PYTHONPATH"

# Set resource limits to prevent memory exhaustion
# Limit virtual memory to 2GB
ulimit -v 2097152
# Limit stack size to 8MB
ulimit -s 8192

# Parse command line arguments
LEAK_DETECTION=false
THRESHOLD=100

while [[ $# -gt 0 ]]; do
    case $1 in
        --leak-detection)
            LEAK_DETECTION=true
            shift
            ;;
        --threshold)
            THRESHOLD="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --leak-detection    Run tests with memory leak detection"
            echo "  --threshold N       Set memory leak threshold in KB (default: 100)"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to run a test with memory monitoring
run_test_with_monitoring() {
    local test_module=$1
    local test_name=$(basename "$test_module")

    echo "Running $test_name..."

    # Create a temporary file to store memory usage
    local mem_log=$(mktemp)

    # Run the test with memory_profiler if available
    if command -v python3 -m memory_profiler &> /dev/null; then
        python3 -m memory_profiler -o "$mem_log" -m unittest "$test_module"
        local exit_code=$?
    else
        # If memory_profiler is not available, use time to get basic memory stats
        /usr/bin/time -v python -m unittest "$test_module" 2> "$mem_log"
        local exit_code=$?
    fi

    # Check if the test passed
    if [ $exit_code -ne 0 ]; then
        echo -e "\n\033[31mTest file $test_name failed. Stopping tests.\033[0m"
        echo -e "Memory usage information saved to $mem_log"
        exit 1
    fi

    # Display memory usage summary
    echo -e "\nMemory usage summary for $test_name:"
    if command -v python3 -m memory_profiler &> /dev/null; then
        tail -n 10 "$mem_log"
    else
        grep -E "Maximum resident set size|Major|Minor|Swaps" "$mem_log"
    fi

    # Clean up
    rm -f "$mem_log"

    # Force garbage collection
    python -c "import gc; gc.collect()"

    # Sleep briefly to allow system to stabilize
    sleep 1
}

# Run all integration tests
echo "Running integration tests..."

if [ "$LEAK_DETECTION" = true ]; then
    # Run tests with memory leak detection
    echo "Running tests with memory leak detection (threshold: ${THRESHOLD}KB)..."
    python -m python.tests.integrationtests.run_tests_with_leak_detection --threshold "$THRESHOLD"
    exit_code=$?

    if [ $exit_code -ne 0 ]; then
        echo -e "\n\033[31mSome tests failed or have memory leaks. See above for details.\033[0m"
        exit 1
    else
        echo -e "\n\033[32mAll integration tests passed successfully with no memory leaks detected!\033[0m"
        exit 0
    fi
else
    # Run each test with monitoring
    run_test_with_monitoring python.tests.integrationtests.test_main
    run_test_with_monitoring python.tests.integrationtests.test_vm_operations
    run_test_with_monitoring python.tests.integrationtests.test_llm_vm_manager
    run_test_with_monitoring python.tests.integrationtests.test_ollama_utils

    echo -e "\n\033[32mAll integration tests passed successfully!\033[0m"
    exit 0
fi
