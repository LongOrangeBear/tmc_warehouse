"""Test client startup."""
import sys
from PySide6.QtWidgets import QApplication
from client.src.ui.main_window import MainWindow

def test_main_window():
    app = QApplication(sys.argv)
    window = MainWindow()
    assert window is not None
    print("MainWindow instantiated successfully")
    return True

if __name__ == "__main__":
    test_main_window()
    print("Client startup test OK")
