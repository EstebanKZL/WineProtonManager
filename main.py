import sys
import ssl
import traceback

# Mover estas configuraciones globales aquí
ssl._create_default_https_context = ssl._create_unverified_context
sys.setrecursionlimit(3000)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QProcess

from config_manager import ConfigManager
from ui.main_window import InstallerApp

def main():
    try:
        # Habilitar escalado DPI para pantallas de alta resolución
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        # Primero, se crea el gestor de configuración
        config_manager = ConfigManager(None)

        # Luego, se inyecta en la ventana principal
        installer = InstallerApp(config_manager)
        
        # Se asigna la instancia de la app al config_manager para referencias cruzadas
        config_manager.app_instance = installer

        # Lógica para ajustar el tamaño de la ventana
        screen = app.primaryScreen().availableGeometry()
        window_size = config_manager.get_window_size()

        if window_size.width() > screen.width() * 0.9 or window_size.height() > screen.height() * 0.9:
            installer.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        else:
            installer.resize(window_size)

        installer.show()
        sys.exit(app.exec_())

    except Exception as e:
        print(f"\n=== Error inesperado en main: {e} ===")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()