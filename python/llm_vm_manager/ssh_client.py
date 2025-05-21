import socket
import paramiko
import time
from llm_vm_manager.jb_llm_logger import logger

class SSHClient(object):

    def is_ssh_port_open(self, host, port=22, timeout=3, retries=10, delay=5) -> bool:
        for i in range(retries):
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except OSError:
                logger.debug("Socket is not open. Will retry.")
            time.sleep(delay)
        return False

    def wait_for_shell_ready(self, ssh, retries=10, delay=5):
        for int_var in range(retries):
            try:
                _, stdout, _ = ssh.exec_command("echo ok")
                if stdout.read().strip() == b"ok":
                    return True
            except Exception:
                logger.debug("Shell is not ready. Will retry.")
            time.sleep(delay)
        logger.debug("Shell not ready after multiple attempts")
        return False

    def ssh_connect(self, host_ip, username, key, retries=5, delay=10, timeout=30):
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
                return ssh
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
                    return None
        return None