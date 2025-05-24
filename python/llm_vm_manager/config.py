import os
import tomllib
from typing import Any, Dict, Optional


class ConfigLoader:
    """
    A class for loading and accessing configuration from TOML files.
    This class provides methods to load a TOML configuration file and
    access its values using dot notation or by retrieving entire sections.
    """

    def __init__(self, path: str) -> None:
        """
        Initialize the ConfigLoader with a TOML configuration file.
        Args:
            path (str): Path to the TOML configuration file.
        Raises:
            FileNotFoundError: If the specified configuration file does not exist.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file '{path}' not found")
        with open(path, "rb") as f:
            self.config = tomllib.load(f)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a value from the configuration using dot notation.
        This method allows accessing nested configuration values using dot notation.
        For example, get("gcp.machine_type") will access the machine_type key
        within the gcp section of the configuration.
        Args:
            key_path (str): The dot-separated path to the configuration value.
            default (Any, optional): The value to return if the key is not found. Defaults to None.
        Returns:
            Any: The configuration value if found, otherwise the default value.
        """
        keys = key_path.split(".")
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except KeyError:
            return default

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire section of the configuration as a dictionary.
        Args:
            section (str): The name of the configuration section to retrieve.
        Returns:
            Dict[str, Any]: The requested configuration section as a dictionary.
                           Returns an empty dictionary if the section doesn't exist.
        """
        return self.config.get(section, {})
