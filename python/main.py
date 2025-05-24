import logging
import argparse
import sys
from llm_vm_manager.config import ConfigLoader
from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from llm_vm_manager.jb_llm_logger import logger
from vm_operations import create_vm, start_vm, stop_vm, delete_vm, list_vms

# Version information
__version__ = "1.0.0"


def main() -> None:
    """
    Main entry point for the application.

    Parses command-line arguments, loads configuration, sets up logging,
    creates a VM manager, and executes the specified command.
    """
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Manage LLM VMs for running Large Language Models")
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}',
                        help='Show program version and exit')
    parser.add_argument('--config', dest='config_file', default='config.toml', 
                        help='Path to the configuration file (default: config.toml)')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Increase verbosity (can be used multiple times)')

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

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

    # Note: The "setup" command has been removed as its functionality is now included in the "create" command

    # Parse arguments
    args = parser.parse_args()

    # Load configuration
    try:
        config = ConfigLoader(args.config_file)
    except FileNotFoundError:
        logger.error(f"Configuration file '{args.config_file}' not found")
        sys.exit(1)

    # Set up logging based on verbosity
    log_levels = {
        0: logging.INFO,  # Default
        1: logging.DEBUG,  # -v
    }
    # Get the log level from config if not overridden by --verbose
    if args.verbose == 0:
        log_level_str = config.get("log_level", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
    else:
        log_level = log_levels.get(args.verbose, logging.DEBUG)

    logger.setLevel(log_level)
    logger.debug(f"Log level set to {logging.getLevelName(log_level)}")
    logger.debug(f"Using configuration file: {args.config_file}")

    # Create VM manager
    vm_manager = GCPVirtualMachineManager(config)

    # Execute the specified command
    if args.command is None:
        logger.error("No command specified")
        parser.print_help()
        sys.exit(1)
    elif args.command == "create":
        create_vm(vm_manager, args)
    elif args.command == "start":
        start_vm(vm_manager, args)
    elif args.command == "stop":
        stop_vm(vm_manager, args)
    elif args.command == "delete":
        delete_vm(vm_manager, args)
    elif args.command == "list":
        list_vms(vm_manager, args)
    # The "setup" command has been removed as its functionality is now included in the "create" command
    else:
        logger.error(f"Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
