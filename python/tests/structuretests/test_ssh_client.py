import unittest
from unittest.mock import patch, MagicMock, call
import paramiko
import os
from llm_vm_manager.ssh_client import SSHClient


class TestSSHClient(unittest.TestCase):
    """Test cases for the SSHClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.ssh_client = SSHClient()
        self.test_host = "192.168.1.1"
        self.test_port = 22
        self.test_username = "testuser"
        # Mock key for testing
        self.mock_key = MagicMock(spec=paramiko.PKey)

    def tearDown(self):
        """Clean up after tests."""
        # Ensure SSH client is disconnected
        if hasattr(self, 'ssh_client') and self.ssh_client:
            self.ssh_client.ssh_disconnect()

    @patch('socket.create_connection')
    @patch('time.sleep')
    def test_is_ssh_port_open_success(self, mock_sleep, mock_create_connection):
        """Test is_ssh_port_open when port is open."""
        # Port is open on first try
        mock_create_connection.return_value = MagicMock()
        result = self.ssh_client.is_ssh_port_open(self.test_host, self.test_port)
        self.assertTrue(result)
        mock_create_connection.assert_called_once_with((self.test_host, self.test_port), timeout=3)
        mock_sleep.assert_not_called()

    @patch('socket.create_connection')
    @patch('time.sleep')
    def test_is_ssh_port_open_retry_success(self, mock_sleep, mock_create_connection):
        """Test is_ssh_port_open when port opens after retries."""
        # Port is closed on first try, open on second
        mock_create_connection.side_effect = [OSError(), MagicMock()]
        result = self.ssh_client.is_ssh_port_open(self.test_host, self.test_port, retries=2)
        self.assertTrue(result)
        self.assertEqual(mock_create_connection.call_count, 2)
        mock_sleep.assert_called_once_with(5)

    @patch('socket.create_connection')
    @patch('time.sleep')
    def test_is_ssh_port_open_failure(self, mock_sleep, mock_create_connection):
        """Test is_ssh_port_open when port remains closed."""
        # Port is always closed
        mock_create_connection.side_effect = OSError()
        result = self.ssh_client.is_ssh_port_open(self.test_host, self.test_port, retries=3)
        self.assertFalse(result)
        self.assertEqual(mock_create_connection.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch.object(SSHClient, 'is_connected')
    @patch('time.sleep')
    def test_wait_for_shell_ready_not_connected(self, mock_sleep, mock_is_connected):
        """Test wait_for_shell_ready when not connected."""
        mock_is_connected.return_value = False
        result = self.ssh_client.wait_for_shell_ready()
        self.assertFalse(result)
        mock_sleep.assert_not_called()

    @patch.object(SSHClient, 'is_connected')
    @patch('time.sleep')
    def test_wait_for_shell_ready_success(self, mock_sleep, mock_is_connected):
        """Test wait_for_shell_ready when shell is ready."""
        mock_is_connected.return_value = True
        # Mock exec_command to return a successful result
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"ok"
        self.ssh_client.ssh_connection = MagicMock()
        self.ssh_client.ssh_connection.exec_command.return_value = (None, mock_stdout, None)
        result = self.ssh_client.wait_for_shell_ready()
        self.assertTrue(result)
        self.ssh_client.ssh_connection.exec_command.assert_called_once_with("echo ok")
        mock_sleep.assert_not_called()

    @patch.object(SSHClient, 'is_connected')
    @patch('time.sleep')
    def test_wait_for_shell_ready_retry_success(self, mock_sleep, mock_is_connected):
        """Test wait_for_shell_ready when shell becomes ready after retries."""
        mock_is_connected.return_value = True
        # Mock exec_command to fail first, then succeed
        mock_stdout_fail = MagicMock()
        mock_stdout_fail.read.side_effect = Exception("Shell not ready")
        mock_stdout_success = MagicMock()
        mock_stdout_success.read.return_value = b"ok"
        self.ssh_client.ssh_connection = MagicMock()
        self.ssh_client.ssh_connection.exec_command.side_effect = [
            (None, mock_stdout_fail, None),
            (None, mock_stdout_success, None)
        ]
        result = self.ssh_client.wait_for_shell_ready(retries=2)
        self.assertTrue(result)
        self.assertEqual(self.ssh_client.ssh_connection.exec_command.call_count, 2)
        mock_sleep.assert_called_once_with(5)

    @patch('paramiko.SSHClient')
    def test_ssh_connect_success(self, mock_ssh_client_class):
        """Test ssh_connect when connection is successful."""
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        result = self.ssh_client.ssh_connect(self.test_host, self.test_username, self.mock_key)
        self.assertTrue(result)
        mock_ssh_client.set_missing_host_key_policy.assert_called_once()
        mock_ssh_client.connect.assert_called_once_with(
            hostname=self.test_host,
            username=self.test_username,
            pkey=self.mock_key,
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )
        self.assertEqual(self.ssh_client.ssh_connection, mock_ssh_client)

    @patch('paramiko.SSHClient')
    @patch('time.sleep')
    def test_ssh_connect_retry_success(self, mock_sleep, mock_ssh_client_class):
        """Test ssh_connect when connection succeeds after retries."""
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        # Connection fails first, then succeeds
        mock_ssh_client.connect.side_effect = [
            paramiko.ssh_exception.SSHException("Connection failed"),
            None  # Success
        ]
        result = self.ssh_client.ssh_connect(self.test_host, self.test_username, self.mock_key, retries=2)
        self.assertTrue(result)
        self.assertEqual(mock_ssh_client.connect.call_count, 2)
        mock_sleep.assert_called_once_with(10)
        self.assertEqual(self.ssh_client.ssh_connection, mock_ssh_client)

    @patch('paramiko.SSHClient')
    @patch('time.sleep')
    def test_ssh_connect_failure(self, mock_sleep, mock_ssh_client_class):
        """Test ssh_connect when connection always fails."""
        mock_ssh_client = MagicMock()
        mock_ssh_client_class.return_value = mock_ssh_client
        # Connection always fails
        mock_ssh_client.connect.side_effect = paramiko.ssh_exception.SSHException("Connection failed")
        result = self.ssh_client.ssh_connect(self.test_host, self.test_username, self.mock_key, retries=2)
        self.assertFalse(result)
        self.assertEqual(mock_ssh_client.connect.call_count, 2)
        mock_sleep.assert_called_once_with(10)

    def test_is_connected_no_connection(self):
        """Test is_connected when there is no connection."""
        self.ssh_client.ssh_connection = None
        self.assertFalse(self.ssh_client.is_connected())

    def test_is_connected_with_active_connection(self):
        """Test is_connected when there is an active connection."""
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = True
        self.ssh_client.ssh_connection = MagicMock()
        self.ssh_client.ssh_connection.get_transport.return_value = mock_transport
        self.assertTrue(self.ssh_client.is_connected())

    def test_is_connected_with_inactive_connection(self):
        """Test is_connected when there is an inactive connection."""
        mock_transport = MagicMock()
        mock_transport.is_active.return_value = False
        self.ssh_client.ssh_connection = MagicMock()
        self.ssh_client.ssh_connection.get_transport.return_value = mock_transport
        self.assertFalse(self.ssh_client.is_connected())

    def test_ssh_disconnect(self):
        """Test ssh_disconnect."""
        mock_connection = MagicMock()
        self.ssh_client.ssh_connection = mock_connection
        self.ssh_client.ssh_disconnect()
        mock_connection.close.assert_called_once()
        self.assertIsNone(self.ssh_client.ssh_connection)

    def test_ssh_disconnect_no_connection(self):
        """Test ssh_disconnect when there is no connection."""
        self.ssh_client.ssh_connection = None
        # Should not raise an exception
        self.ssh_client.ssh_disconnect()

    @patch.object(SSHClient, 'is_connected')
    def test_ssh_execute_not_connected(self, mock_is_connected):
        """Test ssh_execute when not connected."""
        mock_is_connected.return_value = False
        self.ssh_client.ssh_execute("test command")
        # No further actions should be taken
        mock_is_connected.assert_called_once()

    @patch.object(SSHClient, 'is_connected')
    @patch('time.time')
    @patch('time.sleep')
    def test_ssh_execute_success(self, mock_sleep, mock_time, mock_is_connected):
        """Test ssh_execute when command executes successfully."""
        mock_is_connected.return_value = True
        mock_time.side_effect = [0, 1, 2]  # Start time, check time
        mock_stdin = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"Command output"
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_channel = MagicMock()
        mock_channel.exit_status_ready.side_effect = [False, True]
        mock_channel.recv_exit_status.return_value = 0
        mock_stdout.channel = mock_channel
        self.ssh_client.ssh_connection = MagicMock()
        self.ssh_client.ssh_connection.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        self.ssh_client.ssh_execute("test command")
        self.ssh_client.ssh_connection.exec_command.assert_called_once_with("test command")
        mock_stdout.read.assert_called_once()
        mock_stderr.read.assert_called_once()
        mock_channel.recv_exit_status.assert_called_once()

    @patch('os.system')
    def test_remove_known_host(self, mock_system):
        """Test remove_known_host."""
        # Mock platform.system to return a consistent value
        with patch('platform.system', return_value='Linux'):
            self.ssh_client.remove_known_host(self.test_host)
            # Check that os.system was called with the correct command
            expected_cmd = f'"ssh-keygen" -f "{os.path.expanduser("~/.ssh/known_hosts")}" -R {self.test_host}'
            mock_system.assert_called_once_with(expected_cmd)

    @patch.object(SSHClient, 'is_connected')
    def test_run_ssh_commands_not_connected(self, mock_is_connected):
        """Test run_ssh_commands when not connected."""
        mock_is_connected.return_value = False
        result = self.ssh_client.run_ssh_commands(["command1", "command2"])
        self.assertFalse(result)
        mock_is_connected.assert_called_once()

    @patch.object(SSHClient, 'is_connected')
    @patch.object(SSHClient, 'wait_for_shell_ready')
    def test_run_ssh_commands_shell_not_ready(self, mock_wait_for_shell_ready, mock_is_connected):
        """Test run_ssh_commands when shell is not ready."""
        mock_is_connected.return_value = True
        mock_wait_for_shell_ready.return_value = False
        result = self.ssh_client.run_ssh_commands(["command1", "command2"])
        self.assertFalse(result)
        mock_is_connected.assert_called_once()
        mock_wait_for_shell_ready.assert_called_once()

    @patch.object(SSHClient, 'is_connected')
    @patch.object(SSHClient, 'wait_for_shell_ready')
    @patch.object(SSHClient, 'ssh_execute')
    def test_run_ssh_commands_success(self, mock_ssh_execute, mock_wait_for_shell_ready, mock_is_connected):
        """Test run_ssh_commands when commands execute successfully."""
        mock_is_connected.return_value = True
        mock_wait_for_shell_ready.return_value = True
        commands = ["command1", "command2"]
        result = self.ssh_client.run_ssh_commands(commands)
        self.assertTrue(result)
        mock_is_connected.assert_called_once()
        mock_wait_for_shell_ready.assert_called_once()
        mock_ssh_execute.assert_has_calls([call("command1"), call("command2")])
        self.assertEqual(mock_ssh_execute.call_count, 2)


if __name__ == '__main__':
    unittest.main()
