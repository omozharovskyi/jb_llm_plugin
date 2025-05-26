import unittest
import os
import tempfile
from unittest.mock import patch, mock_open
from llm_vm_manager.config import ConfigLoader


class TestConfigLoader(unittest.TestCase):
    """Test cases for the ConfigLoader class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary TOML file for testing
        self.test_config_content = """
[section1]
key1 = "value1"
key2 = 42

[section2]
nested = { key3 = "value3", key4 = true }

[gcp]
project_id = "test-project"
zone = "us-central1-a"
machine_type = "n1-standard-1"
instance_name = "test-instance"
"""
        # Create a temporary file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.toml')
        self.temp_file.write(self.test_config_content.encode('utf-8'))
        self.temp_file.close()
        self.config_path = self.temp_file.name

    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary file
        os.unlink(self.config_path)

    def test_init_with_valid_file(self):
        """Test initialization with a valid config file."""
        config_loader = ConfigLoader(self.config_path)
        self.assertIsNotNone(config_loader.config)
        self.assertIn('section1', config_loader.config)
        self.assertIn('section2', config_loader.config)
        self.assertIn('gcp', config_loader.config)

    def test_init_with_invalid_file(self):
        """Test initialization with a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            ConfigLoader('non_existent_file.toml')

    def test_get_simple_key(self):
        """Test getting a simple key value."""
        config_loader = ConfigLoader(self.config_path)
        self.assertEqual(config_loader.get('section1.key1'), 'value1')
        self.assertEqual(config_loader.get('section1.key2'), 42)

    def test_get_nested_key(self):
        """Test getting a nested key value."""
        config_loader = ConfigLoader(self.config_path)
        self.assertEqual(config_loader.get('section2.nested.key3'), 'value3')
        self.assertEqual(config_loader.get('section2.nested.key4'), True)

    def test_get_with_default(self):
        """Test getting a non-existent key with a default value."""
        config_loader = ConfigLoader(self.config_path)
        self.assertEqual(config_loader.get('non_existent_key', 'default'), 'default')
        self.assertEqual(config_loader.get('section1.non_existent_key', 123), 123)

    def test_get_section(self):
        """Test getting an entire section."""
        config_loader = ConfigLoader(self.config_path)
        section1 = config_loader.get_section('section1')
        self.assertIsInstance(section1, dict)
        self.assertEqual(section1['key1'], 'value1')
        self.assertEqual(section1['key2'], 42)

    def test_get_non_existent_section(self):
        """Test getting a non-existent section."""
        config_loader = ConfigLoader(self.config_path)
        section = config_loader.get_section('non_existent_section')
        self.assertEqual(section, {})

    def test_gcp_config(self):
        """Test getting GCP configuration values."""
        config_loader = ConfigLoader(self.config_path)
        self.assertEqual(config_loader.get('gcp.project_id'), 'test-project')
        self.assertEqual(config_loader.get('gcp.zone'), 'us-central1-a')
        self.assertEqual(config_loader.get('gcp.machine_type'), 'n1-standard-1')
        self.assertEqual(config_loader.get('gcp.instance_name'), 'test-instance')


if __name__ == '__main__':
    unittest.main()