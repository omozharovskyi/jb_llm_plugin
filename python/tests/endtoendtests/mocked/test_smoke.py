"""
Smoke tests for the LLM VM Manager application.
These tests verify that the basic functionality of the application works correctly.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the application modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

# from tests.memory_leak_detector import detect_leaks
from main import main


@pytest.mark.smoke
# @detect_leaks
def test_help_command(mock_vm_manager, mock_args, mock_parser):
    """
    Test S1: Help Command
    Run the application with the --help flag.
    The application should display help information.
    """
    # Set up the mock arguments
    mock_args.command = None

    # Mock sys.argv
    with patch('sys.argv', ['main.py', '--help']), \
         patch('utils.parse_arguments', return_value=(mock_parser, mock_args)), \
         patch('utils.load_configuration', return_value=mock_vm_manager.llm_vm_manager_config), \
         patch('utils.setup_logging'), \
         patch('utils.GCPVirtualMachineManager', return_value=mock_vm_manager), \
         patch('utils.execute_command'), \
         patch('sys.exit') as mock_exit:

        # Call the main function
        main()

        # Verify that the help was displayed
        mock_parser.print_help.assert_called_once()
        mock_exit.assert_called_once()


@pytest.mark.smoke
# @detect_leaks
def test_version_command(mock_vm_manager, mock_args, mock_parser):
    """
    Test S2: Version Command
    Run the application with the --version flag.
    The application should display version information.
    """
    # Set up the mock arguments
    mock_args.command = None

    # Mock sys.argv
    with patch('sys.argv', ['main.py', '--version']), \
         patch('utils.parse_arguments', return_value=(mock_parser, mock_args)), \
         patch('utils.load_configuration', return_value=mock_vm_manager.llm_vm_manager_config), \
         patch('utils.setup_logging'), \
         patch('utils.GCPVirtualMachineManager', return_value=mock_vm_manager), \
         patch('utils.execute_command'), \
         patch('sys.exit') as mock_exit:

        # Call the main function
        main()

        # Verify that the version was displayed
        # Note: We can't directly verify this since the version is printed by argparse
        # But we can verify that sys.exit was called
        mock_exit.assert_called_once()


@pytest.mark.smoke
# @detect_leaks
def test_list_command(mock_vm_manager, mock_args, mock_parser):
    """
    Test S3: List Command
    Run the application with the list command.
    The application should list all VM instances.
    """
    # Set up the mock arguments
    mock_args.command = "list"

    # Mock sys.argv
    with patch('sys.argv', ['main.py', 'list']), \
         patch('utils.parse_arguments', return_value=(mock_parser, mock_args)), \
         patch('utils.load_configuration', return_value=mock_vm_manager.llm_vm_manager_config), \
         patch('utils.setup_logging'), \
         patch('utils.GCPVirtualMachineManager', return_value=mock_vm_manager), \
         patch('utils.execute_command') as mock_execute:

        # Call the main function
        main()

        # Verify that the list command was executed
        mock_execute.assert_called_once_with("list", mock_vm_manager, mock_args, mock_parser)
