import paramiko
import requests
from jbllmvm.llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from jbllmvm.llm_vm_manager.jb_llm_logger import logger
import time
import json

def setup_ollama(vm_manager: GCPVirtualMachineManager, zone: str, instance_name: str, llm_model: str) -> bool:
    """
    Set up Ollama on the VM and pull the specified LLM model.
    Args:
        vm_manager: The VM manager instance
        zone: The zone where the VM is located
        instance_name: The name of the VM
        llm_model: The name of the LLM model to pull
    Returns:
        bool: True if setup was successful, False otherwise
    """
    # Get the VM's external IP
    vm_ip = vm_manager.get_instance_external_ip(zone, instance_name)
    if not vm_ip:
        logger.error(f"Could not get external IP for instance {instance_name}")
        return False
    # Remove the VM from known hosts to prevent SSH issues
    vm_manager.ssh_client.remove_known_host(vm_ip)
    # Load SSH key
    ssh_key_path = vm_manager.llm_vm_manager_config.get("ssh.ssh_secret_key")
    ssh_user = vm_manager.llm_vm_manager_config.get("ssh.user")
    try:
        key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    except Exception as ssh_expt:
        logger.error(f"Failed to load SSH key: {ssh_expt}")
        return False
    # Connect to the VM
    if not vm_manager.ssh_client.ssh_connect(vm_ip, ssh_user, key):
        logger.error(f"Failed to connect to {vm_ip}")
        return False
    # Install and configure Ollama
    commands = vm_manager.llm_vm_manager_config.get("execute_commands.commands", [])
    commands = [cmd_line.replace("<<llm_model>>", llm_model) for cmd_line in commands]
    if not vm_manager.ssh_client.run_ssh_commands(commands):
        logger.error("Failed to set up Ollama")
        vm_manager.ssh_client.ssh_disconnect()
        return False
    # Disconnect from the VM
    vm_manager.ssh_client.ssh_disconnect()
    # Set up firewall rule to allow access to Ollama API
    my_ip = vm_manager.get_my_ip()
    firewall_rule_name = vm_manager.llm_vm_manager_config.get("gcp.firewall_rule_name")
    firewall_tag = vm_manager.llm_vm_manager_config.get("gcp.firewall_tag")
    vm_manager.set_firewall_ollama_rule(my_ip, firewall_rule_name, firewall_tag)
    return True


def check_ollama_availability(vm_ip: str, llm_model: str, retries: int = 7, retry_interval: int = 30) -> bool:
    """
    Check if Ollama is available and the specified model is loaded.
    Args:
        vm_ip: The IP address of the VM
        llm_model: The name of the LLM model to check
        retries: The number of retries to attempt before giving up
        retry_interval: The interval in seconds between retries
    Returns:
        bool: True if Ollama is available and the model is loaded, False otherwise
    """
    for attempt in range(1, retries + 1):
        logger.info(f"[{attempt}/{retries}]: Checking LLM model availability via Ollama API...")
        try:
            # Check if Ollama API is accessible
            response = requests.get(f"http://{vm_ip}:11434/api/tags", timeout=5)
            if response.status_code != 200:
                logger.error(f"Ollama API returned error: {response.status_code}")
                return False
            # Check if the model is available
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            if llm_model in model_names:
                logger.info(f"Model '{llm_model}' is available")
                # return True
            else:
                logger.warning(f"Model '{llm_model}' is not available. Available models: {model_names}")
                return False
            logger.info(f"Model '{llm_model}' found. Testing if it can respond...")
            # Try basic chat completion
            chat_response = requests.post(f"http://{vm_ip}:11434/api/chat",
                json={"model": llm_model, "messages": [{"role": "user", "content": "Hello"}]}, timeout=15, stream=True)
            if chat_response.status_code != 200:
                logger.error(f"Chat API returned status {chat_response.status_code}: {chat_response.text}")
                return False
            if not read_llm_response(chat_response):
                return False
            # logger.info(f"Chat API returned OK (HTTP:{chat_response.status_code}): {chat_response.text}")
            return True
        except requests.RequestException as conn_err:
            logger.error(f"Failed to connect to Ollama at {vm_ip}: {conn_err}")
        if attempt < retries:
            logger.info(f"Waiting {retry_interval} second before next attempt...")
            time.sleep(retry_interval)
        else:
            logger.error(f"All retries {retries} failed. Error upon checking model {llm_model} availability.")
    return False

def read_llm_response(chat_response: requests.Response) -> bool:
    """
    Reads and parses a streamed JSON response from Ollama's /api/chat endpoint.
    Args:
        chat_response (requests.Response): The response object returned from the streamed POST request.
    Returns:
        bool: True if the response was parsed successfully and no error occurred. False if an error was detected
              in the streamed content or parsing failed.
    """
    full_text = ""
    final_meta = {}
    for line in chat_response.iter_lines():
        if not line:
            continue
        try:
            msg = json.loads(line.decode("utf-8"))
            if "error" in msg:
                logger.error(f"LLM API returned error: {msg['error']}")
                return False
            content = msg.get("message", {}).get("content", "")
            full_text += content
            if msg.get("done", False):
                final_meta = {
                    "done_reason": msg.get("done_reason"),
                    "total_duration_sec": round(msg.get("total_duration", 0) / 1_000_000_000, 4),
                    "eval_count": msg.get("eval_count"),
                    "eval_duration_sec": round(msg.get("eval_duration", 0) / 1_000_000_000, 4),
                    "load_duration_sec": round(msg.get("load_duration", 0) / 1_000_000_000, 4),
                    "prompt_eval_count": msg.get("prompt_eval_count"),
                    "prompt_eval_duration_sec": round(msg.get("prompt_eval_duration", 0) / 1_000_000_000, 4)
                }
        except json.JSONDecodeError as e:
            logger.warning(f"Skipping malformed JSON line: {line}")
    if not full_text:
        logger.warning("LLM API returned no content.")
    else:
        lines = [line for line in full_text.splitlines() if line.strip()]
        if len(lines) <= 4:
            preview_text = "\n".join(lines)
        else:
            preview_text = "\n".join([lines[0], lines[1], "...", lines[-2], lines[-1]])
        logger.info(f"LLM API response text:\n{preview_text}")
    logger.info(f"Meta info: {json.dumps(final_meta, indent=2)}")
    return True