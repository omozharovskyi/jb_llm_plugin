"""
Integration tests for the main module.
"""
import unittest
import sys
import os
import importlib

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


class TestMain(unittest.TestCase):
    """
    Integration tests for the main module.
    """

    def test_import_main(self):
        """
        Test that the main module can be imported without errors.
        """
        try:
            import python.main
            # If we get here, the import succeeded
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import main module: {e}")

    def test_import_utils(self):
        """
        Test that the utils module can be imported without errors.
        """
        try:
            import python.utils
            # If we get here, the import succeeded
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import utils module: {e}")

    def test_import_vm_operations(self):
        """
        Test that the vm_operations module can be imported without errors.
        """
        try:
            import python.vm_operations
            # If we get here, the import succeeded
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import vm_operations module: {e}")

    def test_import_ollama_utils(self):
        """
        Test that the ollama_utils module can be imported without errors.
        """
        try:
            import python.ollama_utils
            # If we get here, the import succeeded
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import ollama_utils module: {e}")

    def test_import_llm_vm_gcp(self):
        """
        Test that the llm_vm_gcp module can be imported without errors.
        """
        try:
            import python.llm_vm_manager.llm_vm_gcp
            # If we get here, the import succeeded
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import llm_vm_gcp module: {e}")


if __name__ == '__main__':
    unittest.main()
