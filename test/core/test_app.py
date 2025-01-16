import unittest

from mnt.opdom_explorer.core.app import Application
from PyQt6.QtWidgets import QApplication


class TestApplication(unittest.TestCase):
    def setUp(self) -> None:
        """Set up a QApplication instance before each test."""
        self.app = Application([])  # Initialize with an empty argument list

    def test_application_initialization(self) -> None:
        """Test that the Application class initializes correctly."""
        assert isinstance(self.app, QApplication)
        assert self.app.arguments() == []

    def tearDown(self) -> None:
        """Clean up after each test."""
        self.app.quit()


if __name__ == "__main__":
    unittest.main()
