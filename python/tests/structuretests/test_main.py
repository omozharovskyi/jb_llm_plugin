import unittest
from unittest.mock import patch, MagicMock
import sys
import main


class TestMain(unittest.TestCase):
    """Test cases for the main module."""

    @patch('main.execute_command')
    @patch('main.GCPVirtualMachineManager')
    @patch('main.setup_logging')
    @patch('main.load_configuration')
    @patch('main.parse_arguments')
    def test_main_function(self, mock_parse_arguments, mock_load_configuration, 
                          mock_setup_logging, mock_gcp_vm_manager, mock_execute_command):
        """Test the main function with mocked dependencies."""
        # Setup mocks
        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.config_file = 'config.toml'
        mock_args.verbose = 0
        mock_args.command = 'create'
        mock_parse_arguments.return_value = (mock_parser, mock_args)
        
        mock_config = MagicMock()
        mock_load_configuration.return_value = mock_config
        
        mock_vm_manager = MagicMock()
        mock_gcp_vm_manager.return_value = mock_vm_manager
        
        # Call the main function
        main.main()
        
        # Verify all expected functions were called with correct arguments
        mock_parse_arguments.assert_called_once()
        mock_load_configuration.assert_called_once_with(mock_args.config_file)
        mock_setup_logging.assert_called_once_with(mock_args.verbose, mock_config)
        mock_gcp_vm_manager.assert_called_once_with(mock_config)
        mock_execute_command.assert_called_once_with(mock_args.command, mock_vm_manager, mock_args, mock_parser)


if __name__ == '__main__':
    unittest.main()