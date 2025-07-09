import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Import your modularized components
from config_manager import ConfigManager
from ui.main_window import InstallerApp # Corrected import path

if __name__ == "__main__":
    # Enable High DPI scaling for better appearance on high-resolution displays
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Use Fusion style for a more consistent look across platforms

    config_manager = ConfigManager()
    installer = InstallerApp(config_manager)
    
    # Adjust window size to screen if it's too large
    screen = app.primaryScreen().availableGeometry()
    window_size = config_manager.get_window_size()
    
    if window_size.width() > screen.width() * 0.9 or window_size.height() > screen.height() * 0.9:
        installer.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
    else:
        installer.resize(window_size)
        
    installer.show()
    sys.exit(app.exec_())
