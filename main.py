import sys
import shutil
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtCore import Qt, QProcess, QSize
from PyQt5.QtGui import QIcon

from config_manager import ConfigManager
from ui.main_window import InstallerApp # Importar InstallerApp de su nuevo módulo

if __name__ == "__main__":
    # Aumentar el límite de recursión por defecto (precaución: puede consumir más memoria)
    sys.setrecursionlimit(3000)

    try:
        # Habilitar escalado DPI para pantallas de alta resolución
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
        app = QApplication(sys.argv)
        app.setStyle("Fusion") # Fusion es un buen estilo base para temas personalizados
        config_manager = ConfigManager(None) # Temporalmente sin app_instance, se asignará más tarde.

        # Luego, instanciar InstallerApp con el config_manager ya creado
        installer = InstallerApp(config_manager)
        config_manager.app_instance = installer

        # Ajustar tamaño de la ventana al tamaño guardado o por defecto, y limitarlo a la pantalla disponible
        screen = app.primaryScreen().availableGeometry()
        window_size = config_manager.get_window_size()

        # Ajustar el tamaño si es demasiado grande para la pantalla
        if window_size.width() > screen.width() * 0.9 or window_size.height() > screen.height() * 0.9:
            installer.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
        else:
            installer.resize(window_size)

        installer.show()
        sys.exit(app.exec_())
    except RecursionError:
        print("\n=== RecursionError detectado ===")
        import traceback
        traceback.print_exc()
        print("===================================")
        sys.exit(1)
    except Exception as e:
        print(f"\n=== Error inesperado: {e} ===")
        import traceback
        traceback.print_exc()
        print("==============================")
        sys.exit(1)
