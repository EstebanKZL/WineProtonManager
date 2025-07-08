#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Agregar la ruta del proyecto al sistema de importación
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from config_manager import ConfigManager
from ui.main_window import InstallerApp

if __name__ == "__main__":
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    config_manager = ConfigManager()
    installer = InstallerApp(config_manager)
    
    screen = app.primaryScreen().availableGeometry()
    window_size = config_manager.get_window_size()
    
    if window_size.width() > screen.width() * 0.9 or window_size.height() > screen.height() * 0.9:
        installer.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
    else:
        installer.resize(window_size)
    
    installer.show()
    sys.exit(app.exec_())