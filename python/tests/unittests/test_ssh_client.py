import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import socket
import paramiko
import time
import os
import platform
from io import BytesIO

from llm_vm_manager.ssh_client import SSHClient


class TestSSHClient(unittest.TestCase):
    """Test cases for SSHClient class."""

    def setUp(self):
        """Set up test environment before each test."""
        self.ssh_client = SSHClient()

    def tearDown(self):
        """Clean up after each test."""
        if self.ssh_client.ssh_connection is not None:
            self.ssh_client.ssh_disconnect()

    def test_init(self):
        """Test initialization of SSHClient."""
        self.assertIsNone(self.ssh_client.ssh_connection)

    @patch('socket.create_connection')
    @patch('time.sleep')
    @patch('llm_vm_manager.ssh_client.logger')
    def test_is_ssh_port_open_success(self, mock_logger, mock_sleep, mock_create_connection):
        """Test is_ssh_port_open method when connection is successful."""
        # Set up the mock to return a connection
        mock_create_connection.return_value = MagicMock()

        # Call is_ssh_port_open
        result = self.ssh_client.is_ssh_port_open('test-host', 22, 3, 10, 5)

        # Verify the result and calls
        self.assertTrue(result)
        mock_create_connection.assert_called_once_with(('test-host', 22), timeout=3)
        mock_sleep.assert_not_called()

    @patch('socket.create_connection')
    @patch('time.sleep')
    @patch('llm_vm_manager.ssh_client.logger')
    def test_is_ssh_port_open_failure(self, mock_logger, mock_sleep, mock_create_connection):
        """Test is_ssh_port_open method when connection fails."""
        # Set up the mock to raise an exception
        mock_create_connection.side_effect = OSError("Connection refused")

        # Call is_ssh_port_open with fewer retries for faster test
        result = self.ssh_client.is_ssh_port_open('test-host', 22, 3, 2, 0)

        # Verify the result and calls
        self.assertFalse(result)
        self.assertEqual(mock_create_connection.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('llm_vm_manager.ssh_client.logger')
    def test_wait_for_shell_ready_no_connection(self, mock_logger):
        """Test wait_for_shell_ready method when there is no active connection."""
        # Call wait_for_shell_ready
        result = self.ssh_client.wait_for_shell_ready()

        # Verify the result and calls
        self.assertFalse(result)
        mock_logger.error.assert_called_once_with("No active SSH connection. Call ssh_connect first.")

    @patch('llm_vm_manager.ssh_client.logger')
    def test_wait_for_shell_ready_success(self, mock_logger):
        """Test wait_for_shell_ready method when shell is ready."""
        # Set up mock SSH connection
        mock_ssh = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"ok"
        mock_ssh.exec_command.return_value = (None, mock_stdout, None)

        # Set the mock connection
        self.ssh_client.ssh_connection = mock_ssh

        # Mock is_connected to return True
        self.ssh_client.is_connected = MagicMock(return_value=True)

        # Call wait_for_shell_ready
        result = self.ssh_client.wait_for_shell_ready(retries=1, delay=0)

        # Verify the result and calls
        self.assertTrue(result)
        mock_ssh.exec_command.assert_called_once_with("echo ok")

    @patch('time.sleep')
    @patch('llm_vm_manager.ssh_client.logger')
    def test_wait_for_shell_ready_failure(self, mock_logger, mock_sleep):
        """Test wait_for_shell_ready method when shell is not ready."""
        # Set up mock SSH connection
        mock_ssh = MagicMock()
        mock_ssh.exec_command.side_effect = Exception("Shell not ready")

        # Set the mock connection
        self.ssh_client.ssh_connection = mock_ssh

        # Mock is_connected to return True
        self.ssh_client.is_connected = MagicMock(return_value=True)

        # Call wait_for_shell_ready with fewer retries for faster test
        result = self.ssh_client.wait_for_shell_ready(retries=2, delay=0)

        # Verify the result and calls
        self.assertFalse(result)
        self.assertEqual(mock_ssh.exec_command.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('paramiko.SSHClient')
    @patch('time.sleep')
    @patch('llm_vm_manager.ssh_client.logger')
    def test_ssh_connect_success(self, mock_logger, mock_sleep, mock_ssh_client):
        """Test ssh_connect method when connection is successful."""
        # Set up mock SSH client
        mock_ssh = MagicMock()
        mock_ssh_client.return_value = mock_ssh

        # Mock key
        mock_key = MagicMock(spec=paramiko.PKey)

        # Call ssh_connect
        result = self.ssh_client.ssh_connect('test-host', 'test-user', mock_key)

        # Verify the result and calls
        self.assertTrue(result)
        self.assertEqual(self.ssh_client.ssh_connection, mock_ssh)
        mock_ssh.set_missing_host_key_policy.assert_called_once()
        mock_ssh.connect.assert_called_once_with(
            hostname='test-host',
            username='test-user',
            pkey=mock_key,
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )

    @patch('paramiko.SSHClient')
    @patch('time.sleep')
    @patch('llm_vm_manager.ssh_client.logger')
    def test_ssh_connect_failure(self, mock_logger, mock_sleep, mock_ssh_client):
        """Test ssh_connect method when connection fails."""
        # Set up mock SSH client
        mock_ssh = MagicMock()
        mock_ssh_client.return_value = mock_ssh
        mock_ssh.connect.side_effect = paramiko.ssh_exception.SSHException("Connection failed")

        # Mock key
        mock_key = MagicMock(spec=paramiko.PKey)

        # Call ssh_connect with fewer retries for faster test
        result = self.ssh_client.ssh_connect('test-host', 'test-user', mock_key, retries=2, delay=0)

        # Verify the result and calls
        self.assertFalse(result)
        self.assertEqual(mock_ssh.connect.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    def test_is_connected_true(self):
        """Test is_connected method when there is an active connection."""
        # Set up mock SSH connection
        mock_ssh = MagicMock()
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        mock_ssh.get_transport.return_value = mock_transport

        # Set the mock connection
        self.ssh_client.ssh_connection = mock_ssh

        # Call is_connected
        result = self.ssh_client.is_connected()

        # Verify the result
        self.assertTrue(result)

    def test_is_connected_false_no_connection(self):
        """Test is_connected method when there is no connection."""
        # Ensure no connection
        self.ssh_client.ssh_connection = None

        # Call is_connected
        result = self.ssh_client.is_connected()

        # Verify the result
        self.assertFalse(result)

    def test_is_connected_false_inactive(self):
        """Test is_connected method when connection is inactive."""
        # Set up mock SSH connection with inactive transport
        mock_ssh = MagicMock()
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = False
        mock_ssh.get_transport.return_value = mock_transport

        # Set the mock connection
        self.ssh_client.ssh_connection = mock_ssh

        # Call is_connected
        result = self.ssh_client.is_connected()

        # Verify the result
        self.assertFalse(result)

    def test_ssh_disconnect(self):
        """Test ssh_disconnect method."""
        # Set up mock SSH connection
        mock_ssh = MagicMock()

        # Set the mock connection
        self.ssh_client.ssh_connection = mock_ssh

        # Call ssh_disconnect
        self.ssh_client.ssh_disconnect()

        # Verify the calls and state
        mock_ssh.close.assert_called_once()
        self.assertIsNone(self.ssh_client.ssh_connection)

    def test_ssh_disconnect_no_connection(self):
        """Test ssh_disconnect method when there is no connection."""
        # Ensure no connection
        self.ssh_client.ssh_connection = None

        # Call ssh_disconnect
        self.ssh_client.ssh_disconnect()

        # Verify no exception was raised
        self.assertIsNone(self.ssh_client.ssh_connection)

    @patch('time.time')
    @patch('time.sleep')
    @patch('llm_vm_manager.ssh_client.logger')
    def test_ssh_execute_success(self, mock_logger, mock_sleep, mock_time):
        """Test ssh_execute method with successful command execution."""
        # Set up mock SSH connection
        mock_ssh = MagicMock()
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_channel = MagicMock()

        # Configure mocks
        mock_stdout.channel = mock_channel
        mock_stdout.read.return_value = b"Command output"
        mock_stderr.read.return_value = b""
        mock_channel.recv_exit_status.return_value = 0
        mock_channel.exit_status_ready.side_effect = [False, True]
        mock_ssh.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)

        # Set the mock connection
        self.ssh_client.ssh_connection = mock_ssh

        # Mock is_connected to return True
        self.ssh_client.is_connected = MagicMock(return_value=True)

        # Mock time.time to simulate elapsed time
        mock_time.side_effect = [0, 10]

        # Call ssh_execute
        self.ssh_client.ssh_execute("test command")

        # Verify the calls
        mock_ssh.exec_command.assert_called_once_with("test command")
        mock_logger.info.assert_called_with("Command output")

    @patch('llm_vm_manager.ssh_client.logger')
    def test_ssh_execute_no_connection(self, mock_logger):
        """Test ssh_execute method when there is no active connection."""
        # Mock is_connected to return False
        self.ssh_client.is_connected = MagicMock(return_value=False)

        # Call ssh_execute
        self.ssh_client.ssh_execute("test command")

        # Verify the calls
        mock_logger.error.assert_called_once_with("No active SSH connection. Call ssh_connect first.")

    @patch('os.system')
    @patch('os.path.expanduser')
    @patch('platform.system')
    def test_remove_known_host_linux(self, mock_platform_system, mock_expanduser, mock_os_system):
        """Test remove_known_host method on Linux."""
        # Mock platform.system to return 'Linux'
        mock_platform_system.return_value = 'Linux'
        # Mock expanduser to return a predictable path
        mock_expanduser.return_value = "/home/user/.ssh/known_hosts"

        # Call remove_known_host
        self.ssh_client.remove_known_host('test-host')

        # Verify the calls
        expected_command = '"ssh-keygen" -f "/home/user/.ssh/known_hosts" -R test-host'
        mock_os_system.assert_called_once_with(expected_command)

    @patch('os.system')
    @patch('os.path.expanduser')
    @patch('platform.system')
    def test_remove_known_host_windows(self, mock_platform_system, mock_expanduser, mock_os_system):
        """Test remove_known_host method on Windows."""
        # Mock platform.system to return 'Windows'
        mock_platform_system.return_value = 'Windows'
        # Mock expanduser to return a predictable path
        mock_expanduser.return_value = "/home/user/.ssh/known_hosts"

        # Call remove_known_host
        self.ssh_client.remove_known_host('test-host')

        # Verify the calls
        expected_command = '"ssh-keygen" -f "/home/user/.ssh/known_hosts" -R test-host'
        mock_os_system.assert_called_once_with(expected_command)

    @patch('llm_vm_manager.ssh_client.logger')
    def test_run_ssh_commands_success(self, mock_logger):
        """Test run_ssh_commands method with successful command execution."""
        # Mock dependencies
        self.ssh_client.is_connected = MagicMock(return_value=True)
        self.ssh_client.wait_for_shell_ready = MagicMock(return_value=True)
        self.ssh_client.ssh_execute = MagicMock()

        # Call run_ssh_commands
        result = self.ssh_client.run_ssh_commands(["cmd1", "cmd2"])

        # Verify the result and calls
        self.assertTrue(result)
        self.ssh_client.wait_for_shell_ready.assert_called_once()
        self.assertEqual(self.ssh_client.ssh_execute.call_count, 2)
        self.ssh_client.ssh_execute.assert_has_calls([call("cmd1"), call("cmd2")])

    @patch('llm_vm_manager.ssh_client.logger')
    def test_run_ssh_commands_no_connection(self, mock_logger):
        """Test run_ssh_commands method when there is no active connection."""
        # Mock is_connected to return False
        self.ssh_client.is_connected = MagicMock(return_value=False)

        # Call run_ssh_commands
        result = self.ssh_client.run_ssh_commands(["cmd1", "cmd2"])

        # Verify the result and calls
        self.assertFalse(result)
        mock_logger.error.assert_called_once_with("No active SSH connection. Call ssh_connect first.")

    @patch('llm_vm_manager.ssh_client.logger')
    def test_run_ssh_commands_shell_not_ready(self, mock_logger):
        """Test run_ssh_commands method when shell is not ready."""
        # Mock dependencies
        self.ssh_client.is_connected = MagicMock(return_value=True)
        self.ssh_client.wait_for_shell_ready = MagicMock(return_value=False)

        # Call run_ssh_commands
        result = self.ssh_client.run_ssh_commands(["cmd1", "cmd2"])

        # Verify the result and calls
        self.assertFalse(result)
        self.ssh_client.wait_for_shell_ready.assert_called_once()
        mock_logger.error.assert_called_once_with("Shell not ready yet.")



if __name__ == '__main__':
    unittest.main()
