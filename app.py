import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from gui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
from utils.paths import ensure_models_directory

def main():
    # Ensure models directory exists
    if not ensure_models_directory():
        print("❌ Failed to create models directory. Exiting.")
        sys.exit(1)
    
    # Create and run the application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 