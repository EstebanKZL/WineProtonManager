#!/usr/bin/env python3
import sys
import os
import subprocess
import json
import re
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QCheckBox, QDialog, QDialogButtonBox,
    QMessageBox, QGroupBox, QComboBox, QLineEdit, QFileDialog,
    QTabWidget, QFormLayout, QScrollArea, QListWidgetItem, QAction,
    QMenu, QMenuBar, QTableWidget, QTableWidgetItem, QHeaderView, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDir, QSize
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont

# Configuración de estilo mejorada para Plasma KDE moderno
KDE_STYLE = {
    "font": QFont("Noto Sans", 10),
    "title_font": QFont("Noto Sans", 12, QFont.Bold),
    "button_style": """
        QPushButton {
            background-color: #3daee9;
            color: white;
            border: 1px solid #3daee9;
            border-radius: 6px;
            padding: 6px 14px;
        }
        QPushButton:hover {
            background-color: #5dbff2;
        }
        QPushButton:pressed {
            background-color: #2980b9;
        }
        QPushButton:disabled {
            background-color: #d0d0d0;
            color: #9e9e9e;
            border: 1px solid #cccccc;
        }
    """,
    "dark_button_style": """
        QPushButton {
            background-color: #f0f0f0;
            color: #2e3436;
            border: 1px solid #bfc4c9;
            border-radius: 6px;
            padding: 6px 14px;
        }
        QPushButton:hover {
            background-color: #e0e1e2;
        }
        QPushButton:pressed {
            background-color: #d0d1d2;
        }
        QPushButton:disabled {
            background-color: #555b61;
            color: #b0b0b0;
            border: 1px solid #6a6f75;
        }
    """,
    "light_palette": {
        "window": QColor(247, 248, 249),
        "window_text": QColor(33, 37, 41),
        "base": QColor(255, 255, 255),
        "text": QColor(33, 37, 41),
        "button": QColor(247, 248, 249),
        "button_text": QColor(33, 37, 41),
        "highlight": QColor(61, 174, 233),
        "highlight_text": Qt.white
    },
    "dark_palette": {
        "window": QColor(49, 54, 59),
        "window_text": Qt.white,
        "base": QColor(35, 38, 41),
        "text": Qt.white,
        "button": QColor(64, 70, 77),
        "button_text": Qt.white,
        "highlight": QColor(61, 174, 233),
        "highlight_text": Qt.white
    },
    "table_style": """
        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f9f9fa;
            gridline-color: #d0d0d0;
            border: 1px solid #c4c9cc;
        }
        QTableWidget::item {
            padding: 6px;
        }
        QTableWidget::item:selected {
            background-color: #3daee9;
            color: white;
        }
        QHeaderView::section {
            background-color: #f1f3f4;
            padding: 8px;
            border: 1px solid #c4c9cc;
            font-weight: bold;
        }
    """,
    "dark_table_style": """
        QTableWidget {
            background-color: #31363b;
            alternate-background-color: #2b3035;
            gridline-color: #555b61;
            border: 1px solid #5c636a;
        }
        QTableWidget::item {
            padding: 6px;
            color: white;
        }
        QTableWidget::item:selected {
            background-color: #3daee9;
            color: white;
        }
        QHeaderView::section {
            background-color: #40464d;
            padding: 8px;
            border: 1px solid #5c636a;
            font-weight: bold;
            color: white;
        }
    """,
    "groupbox_style": """
        QGroupBox {
            border: 1px solid #bfc4c9;
            border-radius: 6px;
            margin-top: 20px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            font-weight: bold;
            color: #2e3436;
        }
    """,
    "dark_groupbox_style": """
        QGroupBox {
            border: 1px solid #5c636a;
            border-radius: 6px;
            margin-top: 20px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            font-weight: bold;
            color: white;
        }
    """
}

class ConfigManager:
    """Gestor optimizado de configuraciones persistentes"""
    def __init__(self):
        config_dir = Path.home() / ".config" / "WineProtonManager"
        self.config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear directorio de logs si no existe
        log_dir = config_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.configs = self.load_configs()
        self.ensure_default_config()

    def ensure_default_config(self):
        """Garantiza la existencia de configuraciones básicas"""
        configs = self.configs.setdefault("configs", {})
        self.configs.setdefault("last_used", "Wine-System")
        
        if "Wine-System" not in configs:
            configs["Wine-System"] = {
                "type": "wine",
                "prefix": str(Path.home() / ".wine"),
                "arch": "win64"
            }
        
        settings = self.configs.setdefault("settings", {
            "winetricks_path": str(Path(__file__).parent / "AppDir" / "usr" / "bin" / "winetricks"),
            "config_path": str(self.config_file),
            "theme": "light",
            "window_size": [900, 650],
            "silent_install": True  # Modo silencioso activado por defecto
        })
        
        self.save_configs()

    def load_configs(self):
        """Carga configuraciones optimizada"""
        default = {
            "configs": {},
            "last_used": "Wine-System",
            "custom_programs": [],
            "settings": {
                "winetricks_path": str(Path(__file__).parent / "AppDir" / "usr" / "bin" / "winetricks"),
                "config_path": str(self.config_file),
                "theme": "light",
                "window_size": [900, 650],
                "silent_install": True
            }
        }
        
        if not self.config_file.exists():
            return default
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                loaded.setdefault("custom_programs", [])
                loaded.setdefault("settings", default["settings"])
                return loaded
        except Exception as e:
            print(f"Error loading config: {e}")
            return default

    def save_configs(self):
        """Guarda configuraciones con manejo de errores"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_config(self, config_name):
        """Obtiene una configuración específica por nombre"""
        return self.configs["configs"].get(config_name)

    def get_current_env(self, config_name):
        """Obtiene el entorno para la configuración actual"""
        config = self.get_config(config_name)
        if not config:
            return None

        env = os.environ.copy()
        env["WINEPREFIX"] = config["prefix"]
        env["WINEARCH"] = config.get("arch", "win64")

        if config.get("type") == "proton":
            proton_dir = Path(config["proton_dir"])
            env.update({
                "PROTON_DIR": str(proton_dir),
                "WINE": str(proton_dir / "files/bin/wine"),
                "WINESERVER": str(proton_dir / "files/bin/wineserver"),
                "PATH": f"{proton_dir / 'files/bin'}:{os.environ.get('PATH', '')}"
            })
            version_file = proton_dir / "version"
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    env["PROTON_VERSION"] = f.read().strip()

            try:
                result = subprocess.run(
                    [str(proton_dir / "files/bin/wine"), "--version"],
                    env=env,
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    env["WINE_VERSION_IN_PROTON"] = result.stdout.strip()
            except Exception:
                pass
        else:
            wine_dir = config.get("wine_dir")
            if wine_dir:
                wine_dir = Path(wine_dir)
                env.update({
                    "WINE": str(wine_dir / "bin/wine"),
                    "WINESERVER": str(wine_dir / "bin/wineserver"),
                    "PATH": f"{wine_dir / 'bin'}:{os.environ.get('PATH', '')}"
                })
                try:
                    result = subprocess.run(
                        [str(wine_dir / "bin/wine"), "--version"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        env["WINE_VERSION"] = result.stdout.strip()
                except Exception:
                    pass
            else:
                env.update({
                    "WINE": "wine",
                    "WINESERVER": "wineserver"
                })
                try:
                    result = subprocess.run(
                        ["wine", "--version"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        env["WINE_VERSION"] = result.stdout.strip()
                except Exception:
                    pass

        return env

    def remove_custom_program(self, program_name):
        """Elimina un programa personalizado por nombre"""
        if "custom_programs" not in self.configs:
            return False

        removed = False
        for i in range(len(self.configs["custom_programs"])-1, -1, -1):
            if self.configs["custom_programs"][i]["name"] == program_name:
                del self.configs["custom_programs"][i]
                removed = True

        if removed:
            self.save_configs()

        return removed

    def add_custom_program(self):
        dialog = CustomProgramDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                program_info = dialog.get_program_info()
                program_path = program_info["path"]
                program_name = program_info["name"]
                program_type = program_info["type"]

                display_type = "EXE" if program_type == "exe" else "Winetricks"
                
                # Añadimos a las listas internas
                self.custom_programs.append(program_path)
                self.custom_program_types.append(program_type)
                
                # Mostramos solo el nombre en la tabla
                self.add_item_to_table(program_name, display_type)
                self.update_install_button()
                
                # Guardamos en la configuración
                self.config_manager.add_custom_program(program_name, program_path)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al añadir programa:\n{str(e)}")

    def get_custom_programs(self):
        """Obtiene la lista de programas personalizados con tipo por defecto si falta"""
        programs = self.configs.get("custom_programs", [])

        for program in programs:
            if "type" not in program:
                program["type"] = "winetricks"

        return programs
        
    def set_theme(self, theme):
        """Establece el tema (light/dark)"""
        if "settings" not in self.configs:
            self.configs["settings"] = {}
        self.configs["settings"]["theme"] = theme
        self.save_configs()

    def get_theme(self):
        """Obtiene el tema actual"""
        return self.configs["settings"].get("theme", "light")
        
    def get_winetricks_path(self):
        """Obtiene la ruta de winetricks (sistema -> configurada -> interna)"""
        # Primero intentamos con el winetricks del sistema
        try:
            result = subprocess.run(["which", "winetricks"], 
                                  capture_output=True, 
                                  text=True,
                                  check=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        
        # Luego probamos con la ruta configurada
        configured_path = self.configs["settings"].get("winetricks_path", "")
        if configured_path:
            path_obj = Path(configured_path)
            if path_obj.exists() and path_obj.is_file():
                return configured_path
        
        # Finalmente probamos con la ruta interna
        internal_path = Path(__file__).parent / "AppDir" / "usr" / "bin" / "winetricks"
        if internal_path.exists():
            return str(internal_path)
        
        # Si todo falla, devolvemos solo el comando
        return "winetricks"

    def set_winetricks_path(self, path):
        """Establece y valida la ruta de winetricks"""
        if not path:
            return
        
        path = path.strip()
        
        if path == "winetricks":
            valid = True
        else:
            path_obj = Path(path)
            valid = path_obj.exists() and path_obj.is_file()
        
        if not valid:
            QMessageBox.warning(
                None, 
                "Ruta inválida",
                "La ruta de winetricks no es válida o no existe.\n"
                "Se usará la ruta por defecto."
            )
            return
        
        self.configs["settings"]["winetricks_path"] = path
        self.save_configs()
    
    def set_config_path(self, path):
        """Establece la ruta del archivo de configuración"""
        self.configs["settings"]["config_path"] = path
        self.save_configs()
    
    def get_config_path(self):
        """Obtiene la ruta del archivo de configuración"""
        return self.configs["settings"].get("config_path", str(Path.home() / ".config/wineprotonmanager_config.json"))
    
    def set_silent_install(self, enabled):
        """Establece si la instalación silenciosa está activada"""
        if "settings" not in self.configs:
            self.configs["settings"] = {}
        self.configs["settings"]["silent_install"] = enabled
        self.save_configs()
    
    def get_silent_install(self):
        """Obtiene si la instalación silenciosa está activada"""
        return self.configs["settings"].get("silent_install", True)

    def remove_config(self, config_name):
        """Elimina una configuración guardada"""
        if config_name in self.configs["configs"]:
            del self.configs["configs"][config_name]
            if self.configs["last_used"] == config_name:
                self.configs["last_used"] = "Wine-System" if "Wine-System" in self.configs["configs"] else ""
            self.save_configs()
            return True
        return False

    def get_installed_winetricks(self, prefix_path):
        """Obtiene la lista de componentes winetricks instalados en un prefix"""
        winetricks_log = Path(prefix_path) / "winetricks.log"
        if not winetricks_log.exists():
            return []
        
        try:
            with open(winetricks_log, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except Exception:
            return []

    def save_window_size(self, size):
        """Guarda el tamaño de la ventana"""
        if "settings" not in self.configs:
            self.configs["settings"] = {}
        self.configs["settings"]["window_size"] = [size.width(), size.height()]
        self.save_configs()
    
    def get_window_size(self):
        """Obtiene el tamaño guardado de la ventana"""
        size = self.configs["settings"].get("window_size", [900, 650])
        return QSize(size[0], size[1])
    
    def get_log_path(self, program_name):
        """Obtiene la ruta del archivo de log para un programa"""
        config_dir = Path.home() / ".config" / "WineProtonManager" / "logs"
        safe_name = re.sub(r'[^\w\-_.]', '_', program_name)
        return config_dir / f"{safe_name}.log"
    
    def write_to_log(self, program_name, message):
        """Escribe un mensaje en el log del programa"""
        log_path = self.get_log_path(program_name)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

class InstallerThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, items, env, item_types=None, silent_mode=False, winetricks_path="winetricks", config_manager=None):
        super().__init__()
        self.items = items
        self.env = env
        self._is_running = True
        self.silent_mode = silent_mode
        self.item_types = item_types or []
        self.winetricks_path = winetricks_path
        self.config_manager = config_manager

    def run(self):
        try:
            subprocess.run(["which", "konsole"], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            self.error.emit(
                "Konsole no está instalado. Es necesario para mostrar la consola.\n"
                "Puede instalarlo con: sudo apt install konsole"
            )
            return

        for idx, (item_path, item_type) in enumerate(zip(self.items, self.item_types)):
            if not self._is_running:
                break

            display_name = Path(item_path).name if item_type == "exe" else item_path
            self.progress.emit(idx, f"{display_name}: Instalando...")
            
            # Crear archivo de log temporal
            with tempfile.NamedTemporaryFile(delete=False) as temp_log:
                temp_log_path = temp_log.name
            
            try:
                if item_type == "exe":
                    exe_path = Path(item_path)
                    if not exe_path.exists():
                        raise FileNotFoundError(f"El archivo no existe:\n{exe_path}")
                    
                    wine_binary = self.env.get("WINE", "wine")
                    if "PROTON_DIR" in self.env:
                        proton_dir = Path(self.env["PROTON_DIR"])
                        wine_binary = str(proton_dir / "files" / "bin" / "wine")
                    
                    # Comando para ejecutable (.exe) - se cierra automáticamente
                    cmd = [
                        "konsole",
                        "--nofork",  # Esto permite que konsole se cierre automáticamente
                        "-e",
                        "bash", "-c",
                        f"{wine_binary} '{item_path}' 2>&1 | tee '{temp_log_path}'; exit"
                    ]
                    
                else:
                    # Comando para winetricks - se cierra automáticamente
                    silent_flag = "-q" if self.silent_mode else ""
                    cmd = [
                        "konsole",
                        "--nofork",  # Esto permite que konsole se cierre automáticamente
                        "-e",
                        "bash", "-c",
                        f"{self.winetricks_path} --force {silent_flag} '{item_path}' 2>&1 | tee '{temp_log_path}'; exit"
                    ]
                
                # Ejecutar el comando
                process = subprocess.Popen(
                    cmd,
                    env=self.env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Esperar a que termine el proceso
                process.wait()

                # Leer el log temporal
                with open(temp_log_path, 'r', encoding='utf-8', errors='replace') as log_file:
                    log_content = log_file.read()
                
                # Guardar en el log permanente
                if self.config_manager:
                    self.config_manager.write_to_log(display_name, f"=== INICIO DE INSTALACIÓN ===")
                    self.config_manager.write_to_log(display_name, f"Comando ejecutado: {' '.join(cmd)}")
                    self.config_manager.write_to_log(display_name, log_content)
                    self.config_manager.write_to_log(display_name, f"=== FIN DE INSTALACIÓN ===\n")

                if process.returncode != 0:
                    error_msg = f"Error durante la instalación. Código: {process.returncode}"
                    if self.config_manager:
                        self.config_manager.write_to_log(display_name, f"ERROR: {error_msg}")
                    raise subprocess.CalledProcessError(
                        process.returncode, cmd, error_msg
                    )

                self.progress.emit(idx, f"{display_name}: Finalizado ✅")
                
            except Exception as e:
                if self.config_manager:
                    self.config_manager.write_to_log(display_name, f"ERROR DURANTE INSTALACIÓN: {str(e)}")
                self.error.emit(f"Error instalando {display_name}:\n{str(e)}")
                break
            finally:
                # Eliminar archivo temporal
                try:
                    os.unlink(temp_log_path)
                except:
                    pass

        self.finished.emit()

    def stop(self):
        self._is_running = False

class ConfigDialog(QDialog):
    config_saved = pyqtSignal()
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Configuración de Entornos")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.load_configs()
        self.apply_kde_style()

    def apply_kde_style(self):
        self.setFont(KDE_STYLE["font"])
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(KDE_STYLE["font"])
            if isinstance(widget, QGroupBox):
                widget.setFont(KDE_STYLE["title_font"])
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(KDE_STYLE["button_style"])

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        self.current_tab = QWidget()
        self.setup_current_config_tab()
        self.tabs.addTab(self.current_tab, "Configuraciones")

        self.new_tab = QWidget()
        self.setup_new_config_tab()
        self.tabs.addTab(self.new_tab, "Nueva Configuración")

        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Configuración General")

        layout.addWidget(self.tabs)
        self.exit_btn = QPushButton("Salir")
        self.exit_btn.setAutoDefault(False)
        self.exit_btn.clicked.connect(self.reject)
        layout.addWidget(self.exit_btn)
        self.setLayout(layout)

    def setup_current_config_tab(self):
        layout = QVBoxLayout()
        self.config_list = QListWidget()
        self.config_list.itemDoubleClicked.connect(self.edit_config)
        self.config_list.itemSelectionChanged.connect(self.update_config_info)
        layout.addWidget(self.config_list)

        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Eliminar Configuración")
        self.delete_btn.setAutoDefault(False)
        self.delete_btn.clicked.connect(self.delete_config)
        btn_layout.addWidget(self.delete_btn)

        self.set_default_btn = QPushButton("Establecer como Predeterminada")
        self.set_default_btn.setAutoDefault(False)
        self.set_default_btn.clicked.connect(self.set_default_config)
        btn_layout.addWidget(self.set_default_btn)

        layout.addLayout(btn_layout)

        self.config_info = QLabel("Selecciona una configuración para ver detalles")
        self.config_info.setWordWrap(True)
        layout.addWidget(self.config_info)
        self.current_tab.setLayout(layout)

    def setup_new_config_tab(self):
        layout = QFormLayout()

        self.config_type = QComboBox()
        self.config_type.addItems(["Wine", "Proton"])
        self.config_type.currentTextChanged.connect(self.update_config_fields)
        layout.addRow("Tipo:", self.config_type)

        self.config_name = QLineEdit()
        layout.addRow("Nombre:", self.config_name)

        self.arch_combo = QComboBox()
        self.arch_combo.addItems(["win64", "win32"])
        layout.addRow("Arquitectura:", self.arch_combo)

        self.prefix_path = QLineEdit()
        self.prefix_btn = QPushButton("Examinar...")
        self.prefix_btn.setAutoDefault(False)
        self.prefix_btn.clicked.connect(self.browse_prefix)
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(self.prefix_path)
        prefix_layout.addWidget(self.prefix_btn)
        layout.addRow("Prefix:", prefix_layout)

        self.wine_dir = QLineEdit()
        self.wine_btn = QPushButton("Examinar...")
        self.wine_btn.setAutoDefault(False)
        self.wine_btn.clicked.connect(self.browse_wine)
        wine_layout = QHBoxLayout()
        wine_layout.addWidget(self.wine_dir)
        wine_layout.addWidget(self.wine_btn)

        self.wine_group = QGroupBox("Configuración Wine")
        wine_inner_layout = QFormLayout()
        wine_inner_layout.addRow("Directorio Wine:", wine_layout)
        self.wine_group.setLayout(wine_inner_layout)

        self.proton_dir = QLineEdit()
        self.proton_btn = QPushButton("Examinar...")
        self.proton_btn.setAutoDefault(False)
        self.proton_btn.clicked.connect(self.browse_proton)
        proton_layout = QHBoxLayout()
        proton_layout.addWidget(self.proton_dir)
        proton_layout.addWidget(self.proton_btn)

        self.proton_group = QGroupBox("Configuración Proton")
        proton_inner_layout = QFormLayout()
        proton_inner_layout.addRow("Directorio Proton:", proton_layout)
        self.proton_group.setLayout(proton_inner_layout)

        layout.addRow(self.wine_group)
        layout.addRow(self.proton_group)

        self.test_btn = QPushButton("Probar Configuración")
        self.test_btn.setAutoDefault(False)
        self.test_btn.clicked.connect(self.test_configuration)
        layout.addWidget(self.test_btn)
        
        self.save_config_btn = QPushButton("Guardar Configuración")
        self.save_config_btn.setAutoDefault(False)
        self.save_config_btn.clicked.connect(self.save_new_config)
        layout.addWidget(self.save_config_btn)

        self.update_config_fields()
        self.new_tab.setLayout(layout)

    def save_new_config(self):
        try:
            config_name = self.config_name.text().strip()
            if not config_name:
                QMessageBox.warning(self, "Error", "Debes especificar un nombre para la configuración")
                return

            config_type = "wine" if self.config_type.currentText() == "Wine" else "proton"
            arch = self.arch_combo.currentText()
            prefix = self.prefix_path.text().strip()

            if not prefix:
                QMessageBox.warning(self, "Error", "Debes especificar un prefix")
                return

            config = {
                "type": config_type,
                "prefix": prefix,
                "arch": arch
            }

            if config_type == "proton":
                proton_dir = self.proton_dir.text().strip()
                if not proton_dir:
                    QMessageBox.warning(self, "Error", "Debes especificar el directorio de Proton")
                    return
                config["proton_dir"] = proton_dir
            else:
                wine_dir = self.wine_dir.text().strip()
                if wine_dir:
                    config["wine_dir"] = wine_dir

            self.config_manager.configs["configs"][config_name] = config
            self.config_manager.save_configs()
            QMessageBox.information(self, "Guardado", f"Configuración '{config_name}' guardada correctamente")
            
            self.load_configs()
            self.config_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {str(e)}")

    def setup_settings_tab(self):
        layout = QFormLayout()
        self.winetricks_path = QLineEdit(self.config_manager.get_winetricks_path())
        self.winetricks_btn = QPushButton("Examinar...")
        self.winetricks_btn.setAutoDefault(False)
        self.winetricks_btn.clicked.connect(self.browse_winetricks)

        winetricks_layout = QHBoxLayout()
        winetricks_layout.addWidget(self.winetricks_path)
        winetricks_layout.addWidget(self.winetricks_btn)
        layout.addRow("Ruta de Winetricks:", winetricks_layout)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro"])
        current_theme = self.config_manager.get_theme()
        self.theme_combo.setCurrentText("Oscuro" if current_theme == "dark" else "Claro")
        layout.addRow("Tema de la interfaz:", self.theme_combo)

        # Opción para modo silencioso por defecto
        self.silent_checkbox = QCheckBox("Instalación silenciosa por defecto (winetricks)")
        self.silent_checkbox.setChecked(self.config_manager.get_silent_install())
        layout.addRow(self.silent_checkbox)

        self.save_settings_btn = QPushButton("Guardar Ajustes")
        self.save_settings_btn.setAutoDefault(False)
        self.save_settings_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_settings_btn)
        self.settings_tab.setLayout(layout)
        
    def save_settings(self):
        try:
            winetricks_path = self.winetricks_path.text().strip()
            if winetricks_path:
                self.config_manager.set_winetricks_path(winetricks_path)
            
            theme = "dark" if self.theme_combo.currentText() == "Oscuro" else "light"
            self.config_manager.set_theme(theme)
            
            # Guardar preferencia de instalación silenciosa
            self.config_manager.set_silent_install(self.silent_checkbox.isChecked())
            
            QMessageBox.information(self, "Guardado", "Ajustes guardados correctamente")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar ajustes: {str(e)}")

    def browse_winetricks(self):
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog) 
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Todos los archivos (*)")
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        
        self.apply_theme_to_dialog(dialog)
        
        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                self.winetricks_path.setText(selected[0])
                self.config_manager.set_winetricks_path(selected[0])

    def load_configs(self):
        self.config_list.clear()
        for name in self.config_manager.configs["configs"].keys():
            self.config_list.addItem(name)

    def edit_config(self, item):
        config_name = item.text()
        config = self.config_manager.get_config(config_name)
        if not config:
            return

        self.tabs.setCurrentIndex(1)
        self.config_name.setText(config_name)

        if config["type"] == "proton":
            self.config_type.setCurrentText("Proton")
            self.proton_dir.setText(config.get("proton_dir", ""))
            self.wine_dir.setText("")
        else:
            self.config_type.setCurrentText("Wine")
            self.wine_dir.setText(config.get("wine_dir", ""))
            self.proton_dir.setText("")

        self.prefix_path.setText(config.get("prefix", ""))
        self.arch_combo.setCurrentText(config.get("arch", "win64"))

    def delete_config(self):
        selected = self.config_list.currentItem()
        if not selected:
            return

        config_name = selected.text()
        if config_name in ["Wine-System"]:
            QMessageBox.warning(self, "Error", "No se puede eliminar la configuración por defecto")
            return

        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Estás seguro de que deseas eliminar la configuración '{config_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QDialog.Yes:
            if self.config_manager.remove_config(config_name):
                self.load_configs()
                QMessageBox.information(self, "Éxito", f"Configuración '{config_name}' eliminada")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la configuración")

    def set_default_config(self):
        selected = self.config_list.currentItem()
        if not selected:
            return

        config_name = selected.text()
        self.config_manager.configs["last_used"] = config_name
        self.config_manager.save_configs()
        QMessageBox.information(self, "Éxito", f"Configuración '{config_name}' establecida como predeterminada")
        self.update_config_info()

    def update_config_info(self):
        selected = self.config_list.currentItem()
        if not selected:
            self.config_info.setText("Selecciona una configuración para ver detalles")
            return

        config_name = selected.text()
        config = self.config_manager.get_config(config_name)
        if not config:
            self.config_info.setText("Configuración no encontrada")
            return

        env = self.config_manager.get_current_env(config_name)
        version = env.get("PROTON_VERSION") if config["type"] == "proton" else env.get("WINE_VERSION", "Desconocida")
        wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "Desconocida")

        info = [
            f"<b>Nombre:</b> {config_name}",
            f"<b>Tipo:</b> {'Proton' if config['type'] == 'proton' else 'Wine'}",
            f"<b>Versión:</b> <span style='color: #2a82da; font-weight: bold;'>{version}</span>",
        ]

        if config['type'] == 'proton':
            info.extend([
                f"<b>Wine en Proton:</b> <span style='color: #2a82da; font-weight: bold;'>{wine_version_in_proton}</span>",
                f"<b>Directorio Proton:</b> {config.get('proton_dir', 'No especificado')}"
            ])
        else:
            wine_dir = config.get('wine_dir', 'Sistema')
            info.extend([
                f"<b>Directorio Wine:</b> {wine_dir}"
            ])

        info.extend([
            f"<b>Arquitectura:</b> {config.get('arch', 'win64')}",
            f"<b>Prefix:</b> {config.get('prefix', 'No especificado')}"
        ])

        self.config_info.setText("<br>".join(info))

    def update_config_fields(self):
        is_proton = self.config_type.currentText() == "Proton"
        self.proton_group.setVisible(is_proton)
        self.wine_group.setVisible(not is_proton)

    def browse_prefix(self):
        path = self.get_directory_path()
        if path:
            self.prefix_path.setText(path)

    def browse_wine(self):
        path = self.get_directory_path()
        if path:
            self.wine_dir.setText(path)

    def browse_proton(self):
        path = self.get_directory_path()
        if path:
            self.proton_dir.setText(path)

    def get_directory_path(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        
        self.apply_theme_to_dialog(dialog)
        
        if dialog.exec_() == QDialog.Accepted:
            return dialog.selectedFiles()[0]
        return None

    def apply_theme_to_dialog(self, dialog):
        theme = self.config_manager.get_theme()
        if theme == "dark":
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, KDE_STYLE["dark_palette"]["window"])
            dark_palette.setColor(QPalette.WindowText, KDE_STYLE["dark_palette"]["window_text"])
            dark_palette.setColor(QPalette.Base, KDE_STYLE["dark_palette"]["base"])
            dark_palette.setColor(QPalette.Text, KDE_STYLE["dark_palette"]["text"])
            dark_palette.setColor(QPalette.Button, KDE_STYLE["dark_palette"]["button"])
            dark_palette.setColor(QPalette.ButtonText, KDE_STYLE["dark_palette"]["button_text"])
            dark_palette.setColor(QPalette.Highlight, KDE_STYLE["dark_palette"]["highlight"])
            dark_palette.setColor(QPalette.HighlightedText, KDE_STYLE["dark_palette"]["highlight_text"])
            dialog.setPalette(dark_palette)

    def test_configuration(self):
        try:
            env = self.prepare_test_env()

            if self.config_type.currentText() == "Proton":
                proton_dir = Path(self.proton_dir.text().strip())
                wine_bin = str(proton_dir / "files/bin/wine")
                cmd = [wine_bin, "--version"]
            else:
                wine_dir = self.wine_dir.text().strip()
                if wine_dir:
                    wine_bin = str(Path(wine_dir) / "bin/wine")
                else:
                    wine_bin = "wine"
                cmd = [wine_bin, "--version"]

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                QMessageBox.information(
                    self,
                    "Prueba Exitosa",
                    f"Configuración válida\nVersión detectada: {version}"
                )
            else:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    cmd,
                    result.stdout,
                    result.stderr
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error en Prueba",
                f"No se pudo ejecutar Wine/Proton:\n{str(e)}"
            )

    def prepare_test_env(self):
        env = os.environ.copy()
        env["WINEPREFIX"] = self.prefix_path.text().strip()
        env["WINEARCH"] = self.arch_combo.currentText()

        if self.config_type.currentText() == "Proton":
            proton_dir = Path(self.proton_dir.text().strip())
            env.update({
                "PROTON_DIR": str(proton_dir),
                "WINE": str(proton_dir / "files/bin/wine"),
                "WINESERVER": str(proton_dir / "files/bin/wineserver"),
                "PATH": f"{proton_dir / 'files/bin'}:{os.environ.get('PATH', '')}"
            })
        else:
            wine_dir = self.wine_dir.text().strip()
            if wine_dir:
                wine_dir = Path(wine_dir)
                env.update({
                    "WINE": str(wine_dir / "bin/wine"),
                    "WINESERVER": str(wine_dir / "bin/wineserver"),
                    "PATH": f"{wine_dir / 'bin'}:{os.environ.get('PATH', '')}"
                })
            else:
                env.update({
                    "WINE": "wine",
                    "WINESERVER": "wineserver"
                })

        return env

class SelectGroupsDialog(QDialog):
    def __init__(self, component_groups, parent=None):
        super().__init__(parent)
        self.component_groups = component_groups
        self.setWindowTitle("Seleccionar Componentes")
        self.setMinimumSize(450, 350)
        self.setup_ui()
        self.apply_kde_style()

    def apply_kde_style(self):
        self.setFont(KDE_STYLE["font"])
        
        theme = self.parent().config_manager.get_theme() if hasattr(self.parent(), 'config_manager') else 'light'
        
        if theme == 'dark':
            self.tree.setStyleSheet("""
                QTreeWidget {
                    background-color: #31363b;
                    color: white;
                }
                QTreeWidget::item {
                    padding: 6px;
                }
                QTreeWidget::item:selected {
                    background-color: #3daee9;
                    color: white;
                }
                QTreeWidget::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1px solid #76797C;
                    background: #ffffff;
                }
                QTreeWidget::indicator:unchecked {
                    background: #ffffff;
                    image: none;
                }
                QTreeWidget::indicator:checked {
                    background: #ffffff;
                    image: url("icons/check-black.svg");
                }
            """)
        else:
            self.tree.setStyleSheet("")
        
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(KDE_STYLE["font"])
            if isinstance(widget, QGroupBox):
                widget.setFont(KDE_STYLE["title_font"])
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(KDE_STYLE["button_style"])

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Componente", "Descripción"])
        self.tree.setColumnCount(2)
        self.tree.setSelectionMode(QTreeWidget.MultiSelection)
        
        self.component_descriptions = {
            "vb2run": "Visual Basic 2.0 Runtime",
            "vb3run": "Visual Basic 3.0 Runtime",
            "vb4run": "Visual Basic 4.0 Runtime",
            "vb5run": "Visual Basic 5.0 Runtime",
            "vb6run": "Visual Basic 6.0 Runtime",
            "vcrun6": "Visual C++ 6.0 Runtime (SP6 recomendado)",
            "vcrun2005": "Visual C++ 2005 Runtime",
            "vcrun2008": "Visual C++ 2008 Runtime",
            "dotnet40": "Microsoft .NET Framework 4.0",
            "dotnet48": "Microsoft .NET Framework 4.8",
        }
        
        for group_name, components in self.component_groups.items():
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, group_name)
            group_item.setFlags(group_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            
            for comp in components:
                child_item = QTreeWidgetItem(group_item)
                child_item.setText(0, comp)
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.Unchecked)
                
                description = self.component_descriptions.get(comp, "Componente Winetricks estándar")
                child_item.setText(1, description)
        
        self.tree.expandAll()
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.tree)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_selected_components(self):
        selected = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                if child_item.checkState(0) == Qt.Checked:
                    selected.append(child_item.text(0))
        return selected

class CustomProgramDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Programa Personalizado")
        self.setup_ui()
        self.apply_kde_style()

    def apply_kde_style(self):
        self.setFont(KDE_STYLE["font"])
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(KDE_STYLE["font"])
            if isinstance(widget, QGroupBox):
                widget.setFont(KDE_STYLE["title_font"])
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(KDE_STYLE["button_style"])

    def setup_ui(self):
        layout = QFormLayout()
        self.name_edit = QLineEdit()
        layout.addRow("Nombre del programa:", self.name_edit)

        self.path_edit = QLineEdit()
        self.path_btn = QPushButton("Examinar...")
        self.path_btn.setAutoDefault(False)
        self.path_btn.clicked.connect(self.browse_program)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.path_btn)
        layout.addRow("Ruta del instalador o comando Winetricks:", path_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

        self.setLayout(layout)

    def browse_program(self):
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Ejecutables (*.exe *.msi);;Todos los archivos (*)")
        dialog.setFilter(QDir.AllEntries | QDir.Hidden)
        
        if hasattr(self, 'last_browse_dir') and self.last_browse_dir:
            dialog.setDirectory(self.last_browse_dir)
        
        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                path = Path(selected[0])
                self.last_browse_dir = str(path.parent)
                self.path_edit.setText(str(path.absolute()))

    def get_program_info(self):
        name = self.name_edit.text().strip()
        path = self.path_edit.text().strip()
        
        if not name:
            raise ValueError("Debe especificar un nombre para el programa")
        
        path_obj = Path(path)
        if path.lower().endswith(('.exe', '.msi')):
            if not path_obj.exists():
                raise FileNotFoundError(f"No se encontró el archivo: {path}")
            program_type = "exe"
            path = str(path_obj.absolute())  # <-- Guardamos ruta absoluta
        else:
            program_type = "winetricks"
            # Para Winetricks, path ya es el nombre del componente (ej: "vcrun6")
        
        return {
            "name": name,
            "path": path,
            "type": program_type
        }

class ManageProgramsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Programas Guardados")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.apply_kde_style()

    def apply_kde_style(self):
        self.setFont(KDE_STYLE["font"])
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(KDE_STYLE["font"])
            if isinstance(widget, QGroupBox):
                widget.setFont(KDE_STYLE["title_font"])
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(KDE_STYLE["button_style"])

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nombre", "Comando", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.load_programs()
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Eliminar Seleccionados")
        self.delete_btn.setAutoDefault(False)
        self.delete_btn.clicked.connect(self.delete_programs)
        btn_layout.addWidget(self.delete_btn)

        self.close_btn = QPushButton("Cerrar")
        self.close_btn.setAutoDefault(False)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_programs(self):
        self.table.setRowCount(0)
        programs = self.config_manager.get_custom_programs()
        self.table.setRowCount(len(programs))
        
        for row, program in enumerate(programs):
            name_item = QTableWidgetItem(program['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            path_item = QTableWidgetItem(program['path'])
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, path_item)
            
            type_item = QTableWidgetItem("EXE" if program.get("type") == "exe" else "Winetricks")
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

    def delete_programs(self):
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        if not selected_rows:
            return

        rows_to_delete = sorted(selected_rows, reverse=True)
        programs = self.config_manager.get_custom_programs()
        programs_to_delete = [programs[row]['name'] for row in rows_to_delete]

        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar los {len(programs_to_delete)} programas seleccionados?",
            QMessageBox.Yes | QMessageBox.No 
        )

        if reply == QMessageBox.Yes:
            success = True
            for program_name in programs_to_delete:
                if not self.config_manager.remove_custom_program(program_name):
                    success = False
            if success:
                self.load_programs()
                QMessageBox.information(self, "Éxito", "Programas eliminados correctamente")
            else:
                QMessageBox.warning(self, "Error", "Algunos programas no pudieron ser eliminados")

class LoadProgramsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Cargar Programas Guardados")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.apply_kde_style()

    def apply_kde_style(self):
        self.setFont(KDE_STYLE["font"])
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(KDE_STYLE["font"])
            if isinstance(widget, QGroupBox):
                widget.setFont(KDE_STYLE["title_font"])
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(KDE_STYLE["button_style"])

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nombre", "Comando", "Tipo", "Seleccionar"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.load_programs()
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Cargar Seleccionados")
        self.load_btn.setAutoDefault(False)
        self.load_btn.clicked.connect(self.load_selected)
        btn_layout.addWidget(self.load_btn)

        self.close_btn = QPushButton("Cerrar")
        self.close_btn.setAutoDefault(False)
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_programs(self):
        self.table.setRowCount(0)
        programs = self.config_manager.get_custom_programs()
        self.table.setRowCount(len(programs))
        
        for row, program in enumerate(programs):
            name_item = QTableWidgetItem(program['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            path_item = QTableWidgetItem(program['path'])
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, path_item)
            
            program_type = "EXE" if program.get("type") == "exe" else "Winetricks"
            type_item = QTableWidgetItem(program_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)
            
            checkbox = QTableWidgetItem()
            checkbox.setFlags(checkbox.flags() | Qt.ItemIsUserCheckable)
            checkbox.setCheckState(Qt.Unchecked)
            checkbox.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, checkbox)

    def load_selected(self):
        selected_rows = []
        for row in range(self.table.rowCount()):
            if self.table.item(row, 3).checkState() == Qt.Checked:
                selected_rows.append(row)
                
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No hay programas seleccionados")
            return

        programs = self.config_manager.get_custom_programs()
        self.selected_programs = [programs[row] for row in selected_rows]
        self.accept()

    def get_selected_programs(self):
        return getattr(self, 'selected_programs', [])

class InstallerApp(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.installer_thread = None
        self.selected_components = []
        self.custom_programs = []
        self.custom_program_types = []
        self.silent_mode = self.config_manager.get_silent_install()

        self.setup_ui()
        self.apply_theme()
        self.apply_kde_style()

    def apply_kde_style(self):
        self.setFont(KDE_STYLE["font"])
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(KDE_STYLE["font"])
            if isinstance(widget, QGroupBox):
                widget.setFont(KDE_STYLE["title_font"])
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(KDE_STYLE["button_style"])

    def setup_ui(self):
        self.setWindowTitle("WineProton Manager")
        self.resize(self.config_manager.get_window_size())
        self.setWindowIcon(QIcon.fromTheme("wine"))

        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout_content = QHBoxLayout(content)
        
        layout_content.addWidget(self.create_left_panel(), 1)
        layout_content.addWidget(self.create_right_panel(), 2)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        config_group = QGroupBox("Configuración del Entorno")
        config_layout = QVBoxLayout()
        self.config_label = QLabel()
        self.config_label.setWordWrap(True)
        self.update_config_label()
        
        self.config_btn = QPushButton("Configurar Entornos...")
        self.config_btn.setAutoDefault(False)
        self.config_btn.clicked.connect(self.configure_environments)
        config_layout.addWidget(self.config_label)
        config_layout.addWidget(self.config_btn)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        action_group = QGroupBox("Acciones")
        action_layout = QVBoxLayout()
        
        comp_group = QGroupBox("Componentes")
        comp_layout = QVBoxLayout()
        self.select_components_btn = QPushButton("Seleccionar Componentes")
        self.select_components_btn.setAutoDefault(False)
        self.select_components_btn.clicked.connect(self.select_components)
        comp_layout.addWidget(self.select_components_btn)
        comp_group.setLayout(comp_layout)
        action_layout.addWidget(comp_group)
        
        custom_group = QGroupBox("Programas Personalizados")
        custom_layout = QVBoxLayout()
        self.add_custom_btn = QPushButton("Añadir Programa")
        self.add_custom_btn.setAutoDefault(False)
        self.add_custom_btn.clicked.connect(self.add_custom_program)
        custom_layout.addWidget(self.add_custom_btn)
        
        self.load_custom_btn = QPushButton("Cargar Programas Guardados")
        self.load_custom_btn.setAutoDefault(False)
        self.load_custom_btn.clicked.connect(self.load_custom_programs)
        custom_layout.addWidget(self.load_custom_btn)
        
        self.manage_custom_btn = QPushButton("Gestionar Programas Guardados")
        self.manage_custom_btn.setAutoDefault(False)
        self.manage_custom_btn.clicked.connect(self.manage_custom_programs)
        custom_layout.addWidget(self.manage_custom_btn)
        custom_group.setLayout(custom_layout)
        action_layout.addWidget(custom_group)
        
        options_group = QGroupBox("Opciones de Instalación")
        options_layout = QVBoxLayout()
        self.silent_checkbox = QCheckBox("Modo silencioso (solo para winetricks)")
        self.silent_checkbox.setChecked(self.silent_mode)
        self.silent_checkbox.stateChanged.connect(self.update_silent_mode)
        options_layout.addWidget(self.silent_checkbox)
        options_group.setLayout(options_layout)
        action_layout.addWidget(options_group)
        
        self.install_btn = QPushButton("Iniciar Instalación")
        self.install_btn.setAutoDefault(False)
        self.install_btn.clicked.connect(self.start_installation)
        self.install_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancelar Instalación")
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.clicked.connect(self.cancel_installation)
        self.cancel_btn.setEnabled(False)
        
        self.winetricks_btn = QPushButton("Abrir Winetricks GUI")
        self.winetricks_btn.setAutoDefault(False)
        self.winetricks_btn.clicked.connect(self.open_winetricks)
        
        self.shell_btn = QPushButton("Abrir Terminal con Prefix")
        self.shell_btn.setAutoDefault(False)
        self.shell_btn.clicked.connect(self.open_shell)
        
        self.prefix_btn = QPushButton("Abrir Carpeta Prefix")
        self.prefix_btn.setAutoDefault(False)
        self.prefix_btn.clicked.connect(self.open_prefix_folder)
        
        action_layout.addWidget(self.install_btn)
        action_layout.addWidget(self.cancel_btn)
        action_layout.addWidget(self.winetricks_btn)
        action_layout.addWidget(self.shell_btn)
        action_layout.addWidget(self.prefix_btn)
        action_layout.addStretch()
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        return panel

    def create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.status_label = QLabel("Items a instalar:")
        layout.addWidget(self.status_label)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["", "Nombre", "Tipo", "Estado"])
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.items_table)
        
        btn_layout = QHBoxLayout()
        buttons = [
            ("Limpiar Lista", self.clear_list),
            ("Eliminar Seleccionados", self.remove_selected),
            ("Mover Arriba", self.move_item_up),
            ("Mover Abajo", self.move_item_down)
        ]
        
        for text, handler in buttons:
            btn = QPushButton(text)
            btn.setAutoDefault(False)
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        return panel

    def apply_theme(self):
        theme = self.config_manager.get_theme()
        palette = QApplication.palette()
        
        if theme == "dark":
            palette.setColor(QPalette.Window, KDE_STYLE["dark_palette"]["window"])
            palette.setColor(QPalette.WindowText, KDE_STYLE["dark_palette"]["window_text"])
            palette.setColor(QPalette.Base, KDE_STYLE["dark_palette"]["base"])
            palette.setColor(QPalette.Text, KDE_STYLE["dark_palette"]["text"])
            palette.setColor(QPalette.Button, KDE_STYLE["dark_palette"]["button"])
            palette.setColor(QPalette.ButtonText, KDE_STYLE["dark_palette"]["button_text"])
            palette.setColor(QPalette.Highlight, KDE_STYLE["dark_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, KDE_STYLE["dark_palette"]["highlight_text"])
        else:
            palette = QApplication.style().standardPalette()
        
        QApplication.setPalette(palette)
        for widget in QApplication.allWidgets():
            widget.update()

    def set_theme(self, theme):
        self.config_manager.set_theme(theme)
        self.apply_theme()

    def closeEvent(self, event):
        self.config_manager.save_window_size(self.size())
        super().closeEvent(event)

    def configure_environments(self):
        dialog = ConfigDialog(self.config_manager, self)
        dialog.config_saved.connect(self.update_config_label)
        dialog.exec_()
        self.update_config_label()

    def update_config_label(self):
        current = self.config_manager.configs["last_used"]
        config = self.config_manager.get_config(current)

        if not config:
            self.config_label.setText("No hay configuración seleccionada")
            return

        env = self.config_manager.get_current_env(current)
        version = env.get("PROTON_VERSION") if config.get("type") == "proton" else env.get("WINE_VERSION", "Desconocida")
        wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "Desconocida")

        text = [
            f"<b>Configuración actual:</b> <span style='color: #2a82da;'>{current}</span>",
            f"<b>Tipo:</b> <span style='color: #2a82da;'>{'Proton' if config.get('type') == 'proton' else 'Wine'}</span>",
            f"<b>Versión:</b> <span style='color: #2a82da;'>{version}</span>",
        ]

        if config.get('type') == 'proton':
            text.extend([
                f"<b>Wine en Proton:</b> <span style='color: #2a82da;'>{wine_version_in_proton}</span>",
                f"<b>Directorio Proton:</b> <span style='color: #2a82da;'>{config.get('proton_dir', 'No especificado')}</span>"
            ])
        else:
            wine_dir = config.get('wine_dir', 'Sistema')
            text.extend([
                f"<b>Directorio Wine:</b> <span style='color: #2a82da;'>{wine_dir}</span>"
            ])

        text.extend([
            f"<b>Arquitectura:</b> <span style='color: #2a82da;'>{config.get('arch', 'win64')}</span>",
            f"<b>Prefix:</b> <span style='color: #2a82da;'>{config.get('prefix', 'No especificado')}</span>"
        ])

        self.config_label.setText("<br>".join(text))

    def add_custom_program(self):
        dialog = CustomProgramDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                program_info = dialog.get_program_info()
                program_path = program_info["path"]  # Ruta completa o comando Winetricks
                program_name = program_info["name"]
                program_type = program_info["type"]

                display_type = "EXE" if program_type == "exe" else "Winetricks"
                
                # Añadimos a las listas internas (usando el path/command exacto)
                self.custom_programs.append(program_path)
                self.custom_program_types.append(program_type)
                
                # Mostramos en la tabla (nombre en columna 1, path/command en columna 2)
                self.add_item_to_table(program_name, display_type)
                self.update_install_button()
                
                # Guardamos en config.json
                program_data = {
                    "name": program_name,
                    "path": program_path,  # Guardamos el path/command exacto
                    "type": program_type
                }
                if "custom_programs" not in self.config_manager.configs:
                    self.config_manager.configs["custom_programs"] = []
                self.config_manager.configs["custom_programs"].append(program_data)
                self.config_manager.save_configs()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al añadir programa:\n{str(e)}")
                
    def add_item_to_table(self, name, item_type, status="Pendiente", command=None):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Checkbox
        checkbox = QTableWidgetItem()
        checkbox.setFlags(checkbox.flags() | Qt.ItemIsUserCheckable)
        checkbox.setCheckState(Qt.Checked)
        self.items_table.setItem(row, 0, checkbox)
        
        # Nombre
        name_item = QTableWidgetItem(name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 1, name_item)
        
        # Tipo
        type_item = QTableWidgetItem(item_type)
        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 2, type_item)
        
        # Estado
        status_item = QTableWidgetItem(status)
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 3, status_item)
    
    def update_silent_mode(self, state):
        self.silent_mode = state == Qt.Checked
        self.config_manager.set_silent_install(self.silent_mode)

    def load_custom_programs(self):
        dialog = LoadProgramsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_programs = dialog.get_selected_programs()
            
            current_config = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config)
            installed_components = []
            
            if config and "prefix" in config:
                installed_components = self.config_manager.get_installed_winetricks(config["prefix"])
            
            for program in selected_programs:
                if program["type"] == "winetricks" and program["path"] in installed_components:
                    reply = QMessageBox.question(
                        self,
                        "Componente ya instalado",
                        f"El componente '{program['path']}' ya está instalado en este prefix. ¿Deseas instalarlo de todos modos?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        continue
                
                self.custom_programs.append(program["path"])
                self.custom_program_types.append(program["type"])
                display_type = "EXE" if program["type"] == "exe" else "Winetricks"
                self.add_item_to_table(program['name'], display_type)
            self.update_install_button()

    def manage_custom_programs(self):
        dialog = ManageProgramsDialog(self.config_manager, self)
        dialog.exec_()

    def select_components(self):
        component_groups = {
            "Bibliotecas Visual Basic": ["vb2run", "vb3run", "vb4run", "vb5run", "vb6run"],
            "Visual C++ Runtime": [
                "vcrun6", "vcrun6sp6", "vcrun2003", "vcrun2005", "vcrun2008",
                "vcrun2010", "vcrun2012", "vcrun2013", "vcrun2015", "vcrun2017",
                "vcrun2019", "vcrun2022"
            ],
            ".NET Framework": [
                "dotnet11", "dotnet11sp1", "dotnet20", "dotnet20sp1", "dotnet20sp2",
                "dotnet30", "dotnet30sp1", "dotnet35", "dotnet35sp1", "dotnet40",
                "dotnet40_kb2468871", "dotnet45", "dotnet452", "dotnet46", "dotnet461",
                "dotnet462", "dotnet471", "dotnet472", "dotnet48", "dotnet6", "dotnet7",
                "dotnet8", "dotnet9", "dotnetcore2", "dotnetcore3", "dotnetcoredesktop3",
                "dotnetdesktop6", "dotnetdesktop7", "dotnetdesktop8", "dotnetdesktop9"
            ],
            "DirectX y Multimedia": [
                "d3dcompiler_42", "d3dcompiler_43", "d3dcompiler_46", "d3dcompiler_47",
                "d3dx9", "d3dx9_24", "d3dx9_25", "d3dx9_26", "d3dx9_27", "d3dx9_28",
                "d3dx9_29", "d3dx9_30", "d3dx9_31", "d3dx9_32", "d3dx9_33", "d3dx9_34",
                "d3dx9_35", "d3dx9_36", "d3dx9_37", "d3dx9_38", "d3dx9_39", "d3dx9_40",
                "d3dx9_41", "d3dx9_42", "d3dx9_43", "d3dx10", "d3dx10_43", "d3dx11_42",
                "d3dx11_43", "d3dxof", "devenum", "dinput", "dinput8", "directmusic",
                "directplay", "directshow", "directx9", "dmband", "dmcompos", "dmime",
                "dmloader", "dmscript", "dmstyle", "dmsynth", "dmusic", "dmusic32",
                "dx8vb", "dxdiag", "dxdiagn", "dxdiagn_feb2010", "dxtrans", "xact",
                "xact_x64", "xaudio29", "xinput", "xna31", "xna40"
            ],
            "DXVK y VKD3D": [
                "dxvk", "dxvk1000", "dxvk1001", "dxvk1002", "dxvk1003", "dxvk1011",
                "dxvk1020", "dxvk1021", "dxvk1022", "dxvk1023", "dxvk1030", "dxvk1031",
                "dxvk1032", "dxvk1033", "dxvk1034", "dxvk1040", "dxvk1041", "dxvk1042",
                "dxvk1043", "dxvk1044", "dxvk1045", "dxvk1046", "dxvk1050", "dxvk1051",
                "dxvk1052", "dxvk1053", "dxvk1054", "dxvk1055", "dxvk1060", "dxvk1061",
                "dxvk1070", "dxvk1071", "dxvk1072", "dxvk1073", "dxvk1080", "dxvk1081",
                "dxvk1090", "dxvk1091", "dxvk1092", "dxvk1093", "dxvk1094", "dxvk1100",
                "dxvk1101", "dxvk1102", "dxvk1103", "dxvk2000", "dxvk2010", "dxvk2020",
                "dxvk2030", "dxvk2040", "dxvk2041", "dxvk2050", "dxvk2051", "dxvk2052",
                "dxvk2053", "dxvk2060", "dxvk2061", "dxvk2062", "vkd3d"
            ],
            "Codecs Multimedia": [
                "allcodecs", "avifil32", "binkw32", "cinepak", "dirac", "ffdshow",
                "icodecs", "l3codecx", "lavfilters", "lavfilters702", "ogg", "qasf",
                "qcap", "qdvd", "qedit", "quartz", "quartz_feb2010", "quicktime72",
                "quicktime76", "wmp9", "wmp10", "wmp11", "wmv9vcm", "xvid"
            ],
            "Componentes de Sistema": [
                "amstream", "atmlib", "cabinet", "cmd", "comctl32", "comctl32ocx",
                "comdlg32ocx", "crypt32", "crypt32_winxp", "dbghelp", "esent", "filever",
                "gdiplus", "gdiplus_winxp", "glidewrapper", "glut", "gmdls", "hid",
                "jet40", "mdac27", "mdac28", "msaa", "msacm32", "msasn1", "msctf",
                "msdelta", "msdxmocx", "msflxgrd", "msftedit", "mshflxgd", "msls31",
                "msmask", "mspatcha", "msscript", "msvcirt", "msvcrt40", "msxml3",
                "msxml4", "msxml6", "ole32", "oleaut32", "pdh", "pdh_nt4", "peverify",
                "pngfilt", "prntvpt", "python26", "python27", "riched20", "riched30",
                "richtx32", "sapi", "sdl", "secur32", "setupapi", "shockwave",
                "speechsdk", "tabctl32", "ucrtbase2019", "uiribbon", "updspapi",
                "urlmon", "usp10", "webio", "windowscodes", "winhttp", "wininet",
                "wininet_win2k", "wmi", "wsh57", "xmllite"
            ],
            "Controladores y Utilidades": [
                "art2k7min", "art2kmin", "cnc_ddraw", "d2gl", "d3drm", "dpvoice",
                "dsdmo", "dsound", "dswave", "faudio", "faudio1901", "faudio1902",
                "faudio1903", "faudio1904", "faudio1905", "faudio1906", "faudio190607",
                "galliumnine", "galliumnine02", "galliumnine03", "galliumnine04",
                "galliumnine05", "galliumnine06", "galliumnine07", "galliumnine08",
                "galliumnine09", "gfw", "ie6", "ie7", "ie8", "ie8_kb2936068",
                "ie8_tls12", "iertutil", "itircl", "itss", "mdx", "mf", "mfc40",
                "mfc42", "mfc70", "mfc71", "mfc80", "mfc90", "mfc100", "mfc110",
                "mfc120", "mfc140", "nuget", "openal", "otvdm", "otvdm090",
                "physx", "powershell", "powershell_core"
            ]
        }

        dialog = SelectGroupsDialog(component_groups)
        if dialog.exec_() == QDialog.Accepted:
            selected_components = dialog.get_selected_components()
            
            current_config = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config)
            installed_components = []
            
            if config and "prefix" in config:
                installed_components = self.config_manager.get_installed_winetricks(config["prefix"])
            
            for comp in selected_components:
                if comp in installed_components:
                    reply = QMessageBox.question(
                        self,
                        "Componente ya instalado",
                        f"El componente '{comp}' ya está instalado en este prefix. ¿Deseas instalarlo de todos modos?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        continue
                
                self.selected_components.append(comp)
                self.add_item_to_table(comp, "Winetricks")
            self.update_install_button()

    def clear_list(self):
        # Limpiar la lista como antes
        self.items_table.setRowCount(0)
        self.selected_components = []
        self.custom_programs = []
        self.custom_program_types = []
        
        # Restablecer los botones a su estado normal
        self.install_btn.setEnabled(False)
        self.add_custom_btn.setEnabled(True)
        self.load_custom_btn.setEnabled(True)
        self.select_components_btn.setEnabled(True)
        
        # Actualizar estado del botón de instalación
        self.update_install_button()

    def remove_selected(self):
        selected_rows = set()
        for index in self.items_table.selectedIndexes():
            selected_rows.add(index.row())
        
        if not selected_rows:
            return

        for row in sorted(selected_rows, reverse=True):
            item_name = self.items_table.item(row, 1).text()
            
            if item_name in self.selected_components:
                self.selected_components.remove(item_name)
            else:
                for i, prog in enumerate(self.custom_programs[:]):
                    if item_name in prog:
                        del self.custom_programs[i]
                        del self.custom_program_types[i]
                        break
            
            self.items_table.removeRow(row)
        
        self.update_install_button()

    def move_item_up(self):
        selected_rows = set()
        for index in self.items_table.selectedIndexes():
            selected_rows.add(index.row())
        
        if not selected_rows or len(selected_rows) > 1:
            return

        current_row = list(selected_rows)[0]
        if current_row > 0:
            self.swap_table_rows(current_row, current_row - 1)
            self.items_table.selectRow(current_row - 1)
            self._reorder_internal_lists()

    def move_item_down(self):
        selected_rows = set()
        for index in self.items_table.selectedIndexes():
            selected_rows.add(index.row())
        
        if not selected_rows or len(selected_rows) > 1:
            return

        current_row = list(selected_rows)[0]
        if current_row < self.items_table.rowCount() - 1:
            self.swap_table_rows(current_row, current_row + 1)
            self.items_table.selectRow(current_row + 1)
            self._reorder_internal_lists()

    def swap_table_rows(self, row1, row2):
        for col in range(self.items_table.columnCount()):
            item1 = self.items_table.takeItem(row1, col)
            item2 = self.items_table.takeItem(row2, col)
            self.items_table.setItem(row2, col, item1)
            self.items_table.setItem(row1, col, item2)

    def _reorder_internal_lists(self):
        new_selected_components = []
        new_custom_programs = []
        new_custom_program_types = []
        
        for row in range(self.items_table.rowCount()):
            item_name = self.items_table.item(row, 1).text()
            item_type = self.items_table.item(row, 2).text()
            
            if item_type == "Winetricks":
                new_selected_components.append(item_name)
            else:
                for i, prog in enumerate(self.custom_programs):
                    if item_name in prog:
                        new_custom_programs.append(prog)
                        new_custom_program_types.append(self.custom_program_types[i])
                        break
        
        self.selected_components = new_selected_components
        self.custom_programs = new_custom_programs
        self.custom_program_types = new_custom_program_types

    def update_install_button(self):
        self.install_btn.setEnabled(self.items_table.rowCount() > 0)

    def start_installation(self):
        current_config = self.config_manager.configs["last_used"]
        config = self.config_manager.get_config(current_config)

        if not config:
            QMessageBox.critical(self, "Error", "No hay configuración seleccionada")
            return

        prefix_path = Path(config["prefix"])
        if not prefix_path.exists():
            reply = QMessageBox.question(
                self,
                "Prefix no encontrado",
                f"El prefix {config['prefix']} no existe. ¿Deseas crearlo?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    prefix_path.mkdir(parents=True, exist_ok=True, mode=0o755)
                    env = self.config_manager.get_current_env(current_config)

                    if config["type"] == "proton":
                        proton_dir = Path(config["proton_dir"])
                        wine_bin = str(proton_dir / "files/bin/wine")
                    else:
                        wine_dir = config.get("wine_dir")
                        if wine_dir:
                            wine_bin = str(Path(wine_dir) / "bin/wine")
                        else:
                            wine_bin = "wine"

                    subprocess.run(
                        ["konsole", "--noclose", "-e", wine_bin, "wineboot"],
                        env=env,
                        check=True
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"No se pudo crear el prefix: {str(e)}"
                    )
                    return
            else:
                return

        env = self.config_manager.get_current_env(current_config)
        
        all_items = []
        all_types = []
        
        for row in range(self.items_table.rowCount()):
            item_name = self.items_table.item(row, 1).text()  # Nombre mostrado en la tabla
            item_type = self.items_table.item(row, 2).text().lower()  # "exe" o "winetricks"
            
            # Buscamos el programa en config.json por su nombre
            custom_programs = self.config_manager.get_custom_programs()
            program_info = next((p for p in custom_programs if p['name'] == item_name), None)
            
            if program_info:
                # Usamos el path exacto guardado en config.json
                all_items.append(program_info['path'])
                all_types.append(program_info['type'])
            else:
                # Si no está en custom_programs, es un componente Winetricks seleccionado manualmente
                all_items.append(item_name)
                all_types.append("winetricks")
            
            self.items_table.item(row, 3).setText("Pendiente")

        if all_items:
            self.installer_thread = InstallerThread(
                all_items,
                env,
                item_types=all_types,
                silent_mode=self.silent_mode,
                winetricks_path=self.config_manager.get_winetricks_path(),
                config_manager=self.config_manager
            )
            self.installer_thread.progress.connect(self.update_progress)
            self.installer_thread.finished.connect(self.installation_finished)
            self.installer_thread.error.connect(self.show_error)

            self.install_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.installer_thread.start()

    def update_progress(self, idx, message):
        self.items_table.item(idx, 3).setText(message)

    def installation_finished(self):
        # Mostrar mensaje de completado pero NO limpiar la lista
        QMessageBox.information(self, "Completado", "Instalación finalizada. Limpie la lista para instalar nuevos programas.")
        
        # Deshabilitar botones relevantes
        self.install_btn.setEnabled(False)
        self.add_custom_btn.setEnabled(False)
        self.load_custom_btn.setEnabled(False)
        self.select_components_btn.setEnabled(False)
        
        # Habilitar solo el botón de limpiar
        self.cancel_btn.setEnabled(False)

    def reset_ui(self):
        # Solo deshabilitar los botones de instalación/cancelación
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        # No cambiar el estado de los otros botones aquí

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        # Solo resetear la UI parcialmente
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

    def cancel_installation(self):
        if self.installer_thread and self.installer_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirmar",
                "¿Estás seguro de que deseas cancelar la instalación?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.installer_thread.stop()
                self.installer_thread.wait()
                self.reset_ui()

    def open_winetricks(self):
        try:
            current_config = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_env(current_config)
            
            winetricks_path = self.config_manager.get_winetricks_path()
            
            subprocess.Popen(
                [winetricks_path, "--gui"],
                env=env
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir Winetricks: {str(e)}"
            )

    def open_shell(self):
        try:
            current_config = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_env(current_config)
            subprocess.Popen(["konsole"], env=env)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir la terminal: {str(e)}"
            )
            
    def open_prefix_folder(self):
        try:
            current_config = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config)
            
            if config and "prefix" in config:
                prefix_path = Path(config["prefix"])
                if prefix_path.exists():
                    subprocess.Popen(["xdg-open", str(prefix_path)])
                else:
                    QMessageBox.warning(
                        self,
                        "Advertencia",
                        f"El prefix {config['prefix']} no existe"
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Advertencia",
                    "No hay un prefix configurado"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el directorio: {str(e)}"
            )

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