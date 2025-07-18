import socket
import paramiko
import time
from jbllmvm.llm_vm_manager.jb_llm_logger import logger
import os
import platform
from typing import List, Optional, Tuple


class SSHClient(object):
    """
    A class for managing SSH connections and operations.
    This class provides methods for establishing SSH connections, executing commands,
    and managing SSH-related operations like checking port availability and
    removing hosts from known_hosts file.
    """

    def __init__(self) -> None:
        """
        Initialize the SSHClient.

        Initializes the SSH connection object to None. The connection will be
        established when ssh_connect is called.
        """
        self.ssh_connection = None
        self._host_ip = None
        self._username = None
        self._pkey = None

    def is_ssh_port_open(self, host: str, port: int = 22, timeout: int = 3, retries: int = 10, delay: int = 5) -> bool:
        """
        Check if an SSH port is open on a host.
        This method attempts to establish a socket connection to the specified host and port.
        If the connection fails, it retries a specified number of times with a delay between attempts.
        Args:
            host (str): The hostname or IP address to connect to.
            port (int, optional): The port number to connect to. Defaults to 22.
            timeout (int, optional): The timeout in seconds for the connection attempt. Defaults to 3.
            retries (int, optional): The number of connection attempts to make. Defaults to 10.
            delay (int, optional): The delay in seconds between connection attempts. Defaults to 5.
        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        for i in range(retries):
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except OSError:
                logger.debug("Socket is not open. Will retry.")
            time.sleep(delay)
        return False

    def wait_for_shell_ready(self, retries: int = 10, delay: int = 5) -> bool:
        """
        Wait for an SSH shell to be ready for command execution.
        This method attempts to execute a simple command on the SSH connection to verify
        that the shell is ready. If the command fails, it retries a specified number of times
        with a delay between attempts.
        Args:
            retries (int, optional): The number of attempts to make. Defaults to 10.
            delay (int, optional): The delay in seconds between attempts. Defaults to 5.
        Returns:
            bool: True if the shell is ready, False otherwise.
        """
        if not self.is_connected():
            logger.error("No active SSH connection. Call ssh_connect first.")
            return False

        for int_var in range(retries):
            try:
                _, stdout, _ = self.ssh_connection.exec_command("echo ok")
                if stdout.read().strip() == b"ok":
                    return True
            except Exception:
                logger.debug("Shell is not ready. Will retry.")
            time.sleep(delay)
        logger.debug("Shell not ready after multiple attempts")
        return False

    def ssh_connect(self, host_ip: str, username: str, key: paramiko.PKey, 
                retries: int = 5, delay: int = 10, timeout: int = 30) -> bool:
        """
        Establish an SSH connection to a remote host.
        This method attempts to establish an SSH connection to the specified host using
        the provided credentials. If the connection fails, it retries a specified number
        of times with a delay between attempts.
        Args:
            host_ip (str): The hostname or IP address to connect to.
            username (str): The username to authenticate with.
            key (paramiko.PKey): The private key to authenticate with.
            retries (int, optional): The number of connection attempts to make. Defaults to 5.
            delay (int, optional): The delay in seconds between connection attempts. Defaults to 10.
            timeout (int, optional): The timeout in seconds for the connection attempt. Defaults to 30.
        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        # Close any existing connection
        self._host_ip = host_ip
        self._username = username
        self._pkey = key
        if self.ssh_connection is not None:
            self.ssh_disconnect()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[{attempt}/{retries}] Connecting to {host_ip}...")
                ssh.connect(
                    hostname=host_ip,
                    username=username,
                    pkey=key,
                    timeout=timeout,
                    allow_agent=False,
                    look_for_keys=False
                )
                logger.info("Connection successful.")
                self.ssh_connection = ssh
                return True
            except (paramiko.ssh_exception.NoValidConnectionsError,
                    paramiko.ssh_exception.SSHException,
                    socket.timeout,
                    socket.error) as ssh_exp:
                logger.info(f"Connection attempt {attempt} failed: {ssh_exp}")
                if attempt < retries:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.info("All connection attempts failed.")
                    return False
        return False

    def is_connected(self) -> bool:
        """
        Check if there is an active SSH connection.
        Returns:
            bool: True if there is an active connection, False otherwise.
        """
        return self.ssh_connection is not None and self.ssh_connection.get_transport() is not None and self.ssh_connection.get_transport().is_active()

    def ssh_disconnect(self) -> None:
        """
        Close the current SSH connection.
        Returns:
            None
        """
        if self.ssh_connection is not None:
            self.ssh_connection.close()
            self.ssh_connection = None

    def ssh_execute(self, ssh_command: str, max_wait_seconds: int = 300,
                    return_output: bool = False) -> Optional[Tuple[str, str]]:
        """
        Execute a command over SSH and log the output.
        This method executes the specified command on the remote host via SSH,
        waits for it to complete, and logs the output. If the command does not
        complete within the specified timeout, it will be terminated.
        Args:
            ssh_command (str): The command to execute.
            max_wait_seconds (int, optional): The maximum time to wait for the command to complete in seconds. 
                                             Defaults to 300.
            return_output (bool): Determine whether to return output or not. Defaults to False.
        Returns:
            None
        """
        if not self.is_connected():
            logger.error("No active SSH connection. Call ssh_connect first.")
            return
        start_time = time.time()
        stdin, stdout, stderr = self.ssh_connection.exec_command(ssh_command)
        channel = stdout.channel
        while not channel.exit_status_ready():
            if time.time() - start_time > max_wait_seconds:
                logger.warning(f"Timed out waiting for SSH command to complete: {ssh_command}")
                break
            time.sleep(1)
        stdout_output = stdout.read().decode()
        stderr_output = stderr.read().decode()
        exit_status = channel.recv_exit_status()
        if stdout_output.strip():
            logger.info(stdout_output.strip())
        if stderr_output.strip():
            logger.error(stderr_output.strip())
        if exit_status:
            logger.info(f"Exit code: {exit_status}")
        if return_output:
            return stdout_output, stderr_output
        return None

    def remove_known_host(self, vm_ip: str) -> None:
        """
        Remove a host from the SSH known_hosts file.
        This method removes the specified host from the SSH known_hosts file
        to prevent SSH connection issues due to changed host keys.
        Args:
            vm_ip (str): The IP address or hostname of the host to remove.
        Returns:
            None
        """
        known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
        if platform.system() == "Windows":
            ssh_keygen = "ssh-keygen"  # expecting it in PATH but need to fix for further
        else:
            ssh_keygen = "ssh-keygen"
        command = f'"{ssh_keygen}" -f "{known_hosts_path}" -R {vm_ip}'
        os.system(command)

    def run_ssh_commands(self, commands: List[str]) -> bool:
        """
        Run multiple SSH commands in sequence.
        This method runs a list of commands on the remote host via SSH.
        It first checks if the shell is ready, and then executes each command in sequence.
        Args:
            commands (List[str]): A list of commands to execute.
        Returns:
            bool: True if all commands were executed successfully, False if the shell was not ready.
        """
        if not self.is_connected():
            logger.error("No active SSH connection. Call ssh_connect first.")
            return False
        for cmd in commands:
            if not self.is_connected():
                logger.info("Connection lost, attempting to reconnect...")
                if not self.ssh_connect(self._host_ip, self._username, self._pkey):
                    logger.error("Reconnection failed; aborting remaining commands.")
                    return False
            if not self.wait_for_shell_ready():
                logger.error("Shell not ready after reconnect; aborting.")
                return False
            logger.info(f"Running: {cmd}")
            self.ssh_execute(cmd)
            if 'reboot' in cmd:
                logger.info(f"Rebooting VM by: '{cmd}'. Will wait additionally 45 seconds before next command.")
                time.sleep(45)
        return True

    def ssh_poll_for_output(self, main_ssh_command: str, expected_substring: str, polling_interval: int = 30,
                            polling_timeout: int = 900, additional_ssh_command: str = None) -> bool:
        """
        Polls a remote command via SSH until the expected output is found or timeout occurs.
        Args:
            main_ssh_command (str): The command to execute repeatedly via SSH.
            expected_substring (str): The substring to search for in the command output.
            polling_interval (int): Time in seconds between polls.
            polling_timeout (int): Maximum time in seconds to wait before giving up.
            additional_ssh_command (str): The command to execute repeatedly via SSH, but optional, for logs only.
        Returns:
            bool: True if the expected substring is found, False if timeout is reached.
        """
        start_time = time.time()
        while time.time() - start_time < polling_timeout:
            result = self.ssh_execute(main_ssh_command, return_output=True)
            if result is None:
                logger.warning(f"SSH command did not return output. Will retry in {polling_interval} seconds.")
            if additional_ssh_command is not None:
                self.ssh_execute(additional_ssh_command)
            else:
                stdout_output, stderr_output = result
                combined_output = f"{stdout_output}\n{stderr_output}".lower()
                if expected_substring.lower() in combined_output:
                    logger.info("Expected substring found in output.")
                    return True
            logger.info(f"Expected substring not found. Waiting {polling_interval} seconds before retrying...")
            time.sleep(polling_interval)
        logger.warning("Polling timed out without finding the expected substring.")
        return False
