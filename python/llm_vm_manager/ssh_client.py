import socket
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