from llm_vm_manager.llm_vm_gcp import GCPVirtualMachineManager
from utils import parse_arguments, load_configuration, setup_logging, execute_command


def main() -> None:
    """
    Main entry point for the application.
    Parses command-line arguments, loads configuration, sets up logging,
    creates a VM manager, and executes the specified command.
    """
    # Parse command-line arguments
    parser, args = parse_arguments()
    # Load configuration
    config = load_configuration(args.config_file)
    # Set up logging
    setup_logging(args.verbose, config)
    # Create VM manager
    vm_manager = GCPVirtualMachineManager(config)
    # Execute the specified command
    execute_command(args.command, vm_manager, args, parser)


if __name__ == "__main__":
    main()
