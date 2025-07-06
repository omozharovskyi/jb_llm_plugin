import logging
import argparse
import sys
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from llm_vm_manager.jb_llm_logger import logger
from vm_operations import create_vm, start_vm, stop_vm, delete_vm, list_vms

# Version information
__version__ = "1.0.0"


def parse_arguments():
    """
    Set up and parse command-line arguments.
    Returns:
        tuple: A tuple containing (parser, args) where:
            - parser (argparse.ArgumentParser): The argument parser
            - args (argparse.Namespace): The parsed command-line arguments
    """
    parser = argparse.ArgumentParser(description="Manage LLM VMs for running Large Language Models")
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}',
                        help='Show program version and exit')
    parser.add_argument('--config', dest='config_file', default='config.toml', 
                        help='Path to the configuration file (default: config.toml)')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Increase verbosity')
    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=True)
    # Create VM command
    create_parser = subparsers.add_parser("create", help="Create a new VM instance, set up Ollama, and pull a model")
    create_parser.add_argument("--name", required=False, 
                              help="Name of the VM instance (default: from config)")
    create_parser.add_argument("--model", required=False, 
                             help="Name of the LLM model to pull (default: from config)")
    # Start VM command
    start_parser = subparsers.add_parser("start", help="Start an existing VM instance")
    start_parser.add_argument("--name", required=False, 
                             help="Name of the VM instance (default: from config)")
    # Stop VM command
    stop_parser = subparsers.add_parser("stop", help="Stop a running VM instance")
    stop_parser.add_argument("--name", required=False, 
                            help="Name of the VM instance (default: from config)")
    # Delete VM command
    delete_parser = subparsers.add_parser("delete", help="Delete a VM instance")
    delete_parser.add_argument("--name", required=False, 
                              help="Name of the VM instance (default: from config)")
    # List VMs command
    list_parser = subparsers.add_parser("list", help="List all VM instances")
    args = parser.parse_args()
    return parser, args

def load_configuration(config_file):
    """
    Load configuration from the specified file.
    Args:
        config_file (str): Path to the configuration file
    Returns:
        ConfigLoader: The loaded configuration
    Raises:
        SystemExit: If the configuration file is not found
    """
    try:
        return ConfigLoader(config_file)
    except FileNotFoundError:
        logger.error(f"Configuration file '{config_file}' not found")
        sys.exit(1)

def setup_logging(verbose, config, config_file: str):
    """
    Set up logging based on verbosity and configuration.
    Args:
        verbose (int): Verbosity level from command-line arguments
        config (ConfigLoader): Loaded configuration
        config_file (str): Path to configuration file used
    """
    log_levels = {
        0: logging.INFO,  # Default
        1: logging.DEBUG,  # -v
    }
    # Get the log level from config if not overridden by --verbose
    if verbose == 0:
        log_level_str = config.get("log_level", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
    else:
        log_level = log_levels.get(verbose, logging.DEBUG)
    logger.setLevel(log_level)
    logger.debug(f"Log level set to {logging.getLevelName(log_level)}")
    logger.debug(f"Using configuration file: {config_file}")


def execute_command(command, vm_manager, args, parser):
    """
    Execute the specified command.
    Args:
        command (str): The command to execute
        vm_manager (GCPVirtualMachineManager): The VM manager instance
        args (argparse.Namespace): Command-line arguments
        parser (argparse.ArgumentParser): The argument parser
    Raises:
        SystemExit: If no command is specified or an unknown command is provided
    """
    if command is None:
        logger.error("No command specified")
        parser.print_help()
        sys.exit(1)
    elif command == "create":
        create_vm(vm_manager, args)
    elif command == "start":
        start_vm(vm_manager, args)
    elif command == "stop":
        stop_vm(vm_manager, args)
    elif command == "delete":
        delete_vm(vm_manager, args)
    elif command == "list":
        list_vms(vm_manager, args)
    else:
        logger.error(f"Unknown command: {command}")
        parser.print_help()
        sys.exit(1)