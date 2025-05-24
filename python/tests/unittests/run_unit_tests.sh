#!/bin/bash

# Change to the project root directory
cd "$(dirname "$0")/../../.." || exit 1

# Set PYTHONPATH to include the python directory
export PYTHONPATH="$PWD/python:$PYTHONPATH"

echo "Running all unittests in python/tests/unittests..."
python -m unittest discover -s python/tests/unittests -p "test_*.py" -v

# Store the exit code
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "\n\033[32mAll tests passed successfully!\033[0m"
else
    echo -e "\n\033[31mSome tests failed. Please check the output above for details.\033[0m"
fi

# Return the exit code from the unittest command
exit $exit_code
