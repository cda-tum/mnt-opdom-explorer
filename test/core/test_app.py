import unittest
from PyQt6.QtWidgets import QApplication
from core.app import Application

class TestApplication(unittest.TestCase):

    def setUp(self):
        """Set up a QApplication instance before each test."""
        self.app = Application([])  # Initialize with an empty argument list

    def test_application_initialization(self):
        """Test that the Application class initializes correctly."""
        self.assertIsInstance(self.app, QApplication)
        self.assertEqual(self.app.arguments(), [])

    def tearDown(self):
        """Clean up after each test."""
        self.app.quit()

if __name__ == '__main__':
    unittest.main()
