import os
import tomllib


class ConfigLoader:
    def __init__(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file '{path}' not found")
        with open(path, "rb") as f:
            self.config = tomllib.load(f)

    def get(self, key_path: str, default=None):
        """
        To get key value from config, with indent support. Like: get("gcp.machine_type")
        """
        keys = key_path.split(".")
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except KeyError:
            return default

    def get_section(self, section: str) -> dict:
        """To get whole sub config as dictionary"""
        return self.config.get(section, {})
