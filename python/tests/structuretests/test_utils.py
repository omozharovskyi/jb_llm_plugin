import unittest
from unittest.mock import patch, MagicMock, call
import sys
import logging
import argparse
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
import utils


class TestUtils(unittest.TestCase):
    """Test cases for utility functions in utils.py."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock ConfigLoader for testing
        self.mock_config = MagicMock(spec=ConfigLoader)
        self.mock_config.get.return_value = "test_value"
        self.mock_config.get_section.return_value = {"key": "value"}

    @patch('argparse.ArgumentParser.parse_args')
    def test_parse_arguments_default(self, mock_parse_args):
        """Test parse_arguments with default arguments."""
        # Set up mock return value for parse_args
        mock_args = MagicMock()
        mock_args.config_file = "config.toml"
        mock_args.verbose = 0
        mock_args.command = None
        mock_parse_args.return_value = mock_args

        # Call the function
        parser, args = utils.parse_arguments()

        # Verify the results
        self.assertIsInstance(parser, argparse.ArgumentParser)
        self.assertEqual(args.config_file, "config.toml")
        self.assertEqual(args.verbose, 0)
        self.assertIsNone(args.command)

    @patch('argparse.ArgumentParser.parse_args')
    def test_parse_arguments_create_command(self, mock_parse_args):
        """Test parse_arguments with 'create' command."""
        # Set up mock return value for parse_args
        mock_args = MagicMock()
        mock_args.config_file = "config.toml"
        mock_args.verbose = 1
        mock_args.command = "create"
        mock_args.name = "test-vm"
        mock_args.model = "llama2"
        mock_parse_args.return_value = mock_args

        # Call the function
        parser, args = utils.parse_arguments()

        # Verify the results
        self.assertIsInstance(parser, argparse.ArgumentParser)
        self.assertEqual(args.config_file, "config.toml")
        self.assertEqual(args.verbose, 1)
        self.assertEqual(args.command, "create")
        self.assertEqual(args.name, "test-vm")
        self.assertEqual(args.model, "llama2")

    @patch('utils.ConfigLoader')
    def test_load_configuration_success(self, mock_config_loader):
        """Test load_configuration when file exists."""
        # Set up mock return value for ConfigLoader
        mock_config_loader.return_value = self.mock_config

        # Call the function
        config = utils.load_configuration("config.toml")

        # Verify the results
        mock_config_loader.assert_called_once_with("config.toml")
        self.assertEqual(config, self.mock_config)

    @patch('utils.ConfigLoader')
    @patch('utils.logger')
    @patch('sys.exit')
    def test_load_configuration_file_not_found(self, mock_exit, mock_logger, mock_config_loader):
        """Test load_configuration when file does not exist."""
        # Set up mock to raise FileNotFoundError
        mock_config_loader.side_effect = FileNotFoundError("File not found")

        # Call the function
        utils.load_configuration("non_existent.toml")

        # Verify the results
        mock_config_loader.assert_called_once_with("non_existent.toml")
        mock_logger.error.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch('utils.logger')
    def test_setup_logging_default(self, mock_logger):
        """Test setup_logging with default verbosity."""
        # Set up mock config
        self.mock_config.get.return_value = "INFO"
        self.mock_config.config_file = "/test_path/to/config.yaml"

        # Call the function
        utils.setup_logging(0, self.mock_config)

        # Verify the results
        self.mock_config.get.assert_called_once_with("log_level", "INFO")
        mock_logger.setLevel.assert_called_once_with(logging.INFO)
        mock_logger.debug.assert_has_calls([
            call(f"Log level set to INFO"),
            call(f"Using configuration file: {self.mock_config.config_file}")
        ])

    @patch('utils.logger')
    def test_setup_logging_verbose(self, mock_logger):
        """Test setup_logging with increased verbosity."""
        # Call the function with verbose=1
        self.mock_config.config_file = "/path/to/config.yaml"
        utils.setup_logging(1, self.mock_config)

        # Verify the results
        mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
        mock_logger.debug.assert_has_calls([
            call(f"Log level set to DEBUG"),
            call(f"Using configuration file: {self.mock_config.config_file}")
        ])

    @patch('utils.logger')
    def test_execute_command_no_command(self, mock_logger):
        """Test execute_command with no command specified."""
        # Set up mocks
        mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        mock_args = MagicMock()
        mock_args.command = None
        mock_parser = MagicMock(spec=argparse.ArgumentParser)

        # Call the function with sys.exit patched to avoid test exit
        with patch('sys.exit') as mock_exit:
            utils.execute_command(None, mock_vm_manager, mock_args, mock_parser)

            # Verify the results
            mock_logger.error.assert_called_once_with("No command specified")
            mock_parser.print_help.assert_called_once()
            mock_exit.assert_called_once_with(1)

    @patch('utils.create_vm')
    def test_execute_command_create(self, mock_create_vm):
        """Test execute_command with 'create' command."""
        # Set up mocks
        mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        mock_args = MagicMock()
        mock_args.command = "create"
        mock_parser = MagicMock(spec=argparse.ArgumentParser)

        # Call the function
        utils.execute_command("create", mock_vm_manager, mock_args, mock_parser)

        # Verify the results
        mock_create_vm.assert_called_once_with(mock_vm_manager, mock_args)

    @patch('utils.start_vm')
    def test_execute_command_start(self, mock_start_vm):
        """Test execute_command with 'start' command."""
        # Set up mocks
        mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        mock_args = MagicMock()
        mock_args.command = "start"
        mock_parser = MagicMock(spec=argparse.ArgumentParser)

        # Call the function
        utils.execute_command("start", mock_vm_manager, mock_args, mock_parser)

        # Verify the results
        mock_start_vm.assert_called_once_with(mock_vm_manager, mock_args)

    @patch('utils.stop_vm')
    def test_execute_command_stop(self, mock_stop_vm):
        """Test execute_command with 'stop' command."""
        # Set up mocks
        mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        mock_args = MagicMock()
        mock_args.command = "stop"
        mock_parser = MagicMock(spec=argparse.ArgumentParser)

        # Call the function
        utils.execute_command("stop", mock_vm_manager, mock_args, mock_parser)

        # Verify the results
        mock_stop_vm.assert_called_once_with(mock_vm_manager, mock_args)

    @patch('utils.delete_vm')
    def test_execute_command_delete(self, mock_delete_vm):
        """Test execute_command with 'delete' command."""
        # Set up mocks
        mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        mock_args = MagicMock()
        mock_args.command = "delete"
        mock_parser = MagicMock(spec=argparse.ArgumentParser)

        # Call the function
        utils.execute_command("delete", mock_vm_manager, mock_args, mock_parser)

        # Verify the results
        mock_delete_vm.assert_called_once_with(mock_vm_manager, mock_args)

    @patch('utils.list_vms')
    def test_execute_command_list(self, mock_list_vms):
        """Test execute_command with 'list' command."""
        # Set up mocks
        mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        mock_args = MagicMock()
        mock_args.command = "list"
        mock_parser = MagicMock(spec=argparse.ArgumentParser)

        # Call the function
        utils.execute_command("list", mock_vm_manager, mock_args, mock_parser)

        # Verify the results
        mock_list_vms.assert_called_once_with(mock_vm_manager, mock_args)

    @patch('utils.logger')
    def test_execute_command_unknown(self, mock_logger):
        """Test execute_command with unknown command."""
        # Set up mocks
        mock_vm_manager = MagicMock(spec=GCPVirtualMachineManager)
        mock_args = MagicMock()
        mock_args.command = "unknown"
        mock_parser = MagicMock(spec=argparse.ArgumentParser)

        # Call the function with sys.exit patched to avoid test exit
        with patch('sys.exit') as mock_exit:
            utils.execute_command("unknown", mock_vm_manager, mock_args, mock_parser)

            # Verify the results
            mock_logger.error.assert_called_once_with("Unknown command: unknown")
            mock_parser.print_help.assert_called_once()
            mock_exit.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()