#!/usr/bin/env python3
"""
Script to run the mocked end-to-end tests for the LLM VM Manager application.
This script executes all the tests and generates a report of the results.
"""
import os
import sys
import subprocess
import argparse
from datetime import datetime

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run mocked end-to-end tests for LLM VM Manager")
    parser.add_argument("--category", "-c", choices=["smoke", "sanity", "functional", "integration", 
                                                    "negative", "security", "regression", "all"],
                        default="all", help="Test category to run (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    return parser.parse_args()

def run_tests(category="all", verbose=False, coverage=False):
    """Run the specified tests and return the result."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Change to the python directory
    os.chdir(os.path.join(script_dir, "../../.."))

    # Build the pytest command
    cmd = ["python", "-m", "pytest", "tests/endtoendtests/mocked/"]

    # Add category filter if not "all"
    if category != "all":
        cmd.extend(["-m", category])

    # Add verbose flag if requested
    if verbose:
        cmd.append("-v")

    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=python", "--cov-report=term"])

    # Run the tests
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    return result

def generate_report(result, category, coverage):
    """Generate a report of the test results."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""
=================================================================
                MOCKED END-TO-END TESTS REPORT
=================================================================
Date: {timestamp}
Category: {category}
Coverage: {'Yes' if coverage else 'No'}

-----------------------------------------------------------------
                        TEST RESULTS
-----------------------------------------------------------------
{result.stdout}

-----------------------------------------------------------------
                        ERROR OUTPUT
-----------------------------------------------------------------
{result.stderr if result.stderr else 'No errors'}

-----------------------------------------------------------------
                        SUMMARY
-----------------------------------------------------------------
Return Code: {result.returncode}
Status: {'PASSED' if result.returncode == 0 else 'FAILED'}
=================================================================
"""

    # Write the report to a file
    report_file = f"test_report_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, "w") as f:
        f.write(report)

    print(f"Report written to {report_file}")

    return report, report_file

def main():
    """Main entry point."""
    args = parse_arguments()

    print(f"Running {args.category} tests...")
    result = run_tests(args.category, args.verbose, args.coverage)

    report, report_file = generate_report(result, args.category, args.coverage)

    # Print a summary to the console
    print("\nTest Execution Summary:")
    print(f"Category: {args.category}")
    print(f"Status: {'PASSED' if result.returncode == 0 else 'FAILED'}")
    print(f"Report: {report_file}")

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
