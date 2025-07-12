import sys
import os
import subprocess
import json
import re
import time
import tempfile
import ssl
import tarfile
import zipfile
import shutil
from urllib.request import urlopen, Request, HTTPError
from pathlib import Path
from functools import partial

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QCheckBox, QDialog, QDialogButtonBox,
    QMessageBox, QGroupBox, QComboBox, QLineEdit, QFileDialog,
    QTabWidget, QFormLayout, QScrollArea, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTreeWidget, QTreeWidgetItem, QProgressDialog, QProgressBar,
    QInputDialog, QRadioButton, QSizePolicy
)

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDir, QSize, QUrl, QTimer, QProcess
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QDesktopServices

# --- Configuración de Estilo Breeze ---
# Colores centralizados para fácil modificación, inspirados en Plasma 6.0 Breeze
COLOR_BREEZE_PRIMARY = "#3daee9"  # Azul Breeze estándar
COLOR_BREEZE_ACCENT = "#5dbff2"   # Azul más claro para efectos de hover y foco
COLOR_BREEZE_PRESSED = "#2980b9"  # Azul más oscuro para estado presionado

# Colores del Tema Claro
COLOR_BREEZE_LIGHT_WINDOW = "#F7F8F9" # Fondo de ventanas
COLOR_BREEZE_LIGHT_WINDOW_TEXT = "#212529" # Color de texto general
COLOR_BREEZE_LIGHT_BASE = "#FFFFFF" # Fondo para widgets (listas, tablas)
COLOR_BREEZE_LIGHT_TEXT = "#212529" # Texto en widgets base
COLOR_BREEZE_LIGHT_BUTTON = "#F0F0F0" # Fondo para botones
COLOR_BREEZE_LIGHT_BUTTON_TEXT = "#212529" # Texto en botones
COLOR_BREEZE_LIGHT_HIGHLIGHT = COLOR_BREEZE_PRIMARY # Color de resaltado
COLOR_BREEZE_LIGHT_HIGHLIGHT_TEXT = "#FFFFFF" # Texto en resaltado
COLOR_BREEZE_LIGHT_BORDER = "#BFC4C9" # Color de borde
COLOR_BREEZE_LIGHT_DISABLED_BG = "#E0E0E0"
COLOR_BREEZE_LIGHT_DISABLED_TEXT = "#A0A0A0"

# Colores del Tema Oscuro
COLOR_BREEZE_DARK_WINDOW = "#2A2E32" # Fondo de ventanas
COLOR_BREEZE_DARK_WINDOW_TEXT = "#D0D0D0" # Color de texto general
COLOR_BREEZE_DARK_BASE = "#31363B" # Fondo para widgets (listas, tablas)
COLOR_BREEZE_DARK_TEXT = "#D0D0D0" # Texto en widgets base
COLOR_BREEZE_DARK_BUTTON = "#3A3F44" # Fondo para botones
COLOR_BREEZE_DARK_BUTTON_TEXT = "#D0D0D0" # Texto en botones
COLOR_BREEZE_DARK_HIGHLIGHT = COLOR_BREEZE_PRIMARY # Color de resaltado
COLOR_BREEZE_DARK_HIGHLIGHT_TEXT = "#FFFFFF" # Texto en resaltado
COLOR_BREEZE_DARK_BORDER = "#5A5F65" # Color de borde
COLOR_BREEZE_DARK_DISABLED_BG = "#4A4F54"
COLOR_BREEZE_DARK_DISABLED_TEXT = "#808080"


STYLE_BREEZE = {
    "font": QFont("Noto Sans", 11),
    "title_font": QFont("Noto Sans", 13, QFont.Bold),
    "light_border": COLOR_BREEZE_LIGHT_BORDER,
    "dark_border": COLOR_BREEZE_DARK_BORDER,
    # Estilo de botón para Breeze (más plano, sutil hover/pressed)
    "button_style": f"""
        QPushButton {{
            background-color: {COLOR_BREEZE_LIGHT_BUTTON};
            color: {COLOR_BREEZE_LIGHT_BUTTON_TEXT};
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
            border-radius: 4px;
            padding: 8px 18px;
            font-size: 13px;
            font-weight: bold;
            outline: none;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BREEZE_PRIMARY};
            color: {COLOR_BREEZE_LIGHT_HIGHLIGHT_TEXT};
            border: 1px solid {COLOR_BREEZE_PRIMARY};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_BREEZE_PRESSED};
            border: 1px solid {COLOR_BREEZE_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BREEZE_LIGHT_DISABLED_BG};
            color: {COLOR_BREEZE_LIGHT_DISABLED_TEXT};
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
        }}
    """,
    "dark_button_style": f"""
        QPushButton {{
            background-color: {COLOR_BREEZE_DARK_BUTTON};
            color: {COLOR_BREEZE_DARK_BUTTON_TEXT};
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
            border-radius: 4px;
            padding: 8px 18px;
            font-size: 14px;
            font-weight: bold;
            outline: none;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BREEZE_PRIMARY};
            color: {COLOR_BREEZE_DARK_HIGHLIGHT_TEXT};
            border: 1px solid {COLOR_BREEZE_PRIMARY};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_BREEZE_PRESSED};
            border: 1px solid {COLOR_BREEZE_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BREEZE_DARK_DISABLED_BG};
            color: {COLOR_BREEZE_DARK_DISABLED_TEXT};
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
        }}
    """,
    "light_palette": {
        "window": QColor(COLOR_BREEZE_LIGHT_WINDOW),
        "window_text": QColor(COLOR_BREEZE_LIGHT_WINDOW_TEXT),
        "base": QColor(COLOR_BREEZE_LIGHT_BASE),
        "text": QColor(COLOR_BREEZE_LIGHT_TEXT),
        "button": QColor(COLOR_BREEZE_LIGHT_BUTTON),
        "button_text": QColor(COLOR_BREEZE_LIGHT_BUTTON_TEXT),
        "highlight": QColor(COLOR_BREEZE_PRIMARY),
        "highlight_text": QColor(COLOR_BREEZE_LIGHT_HIGHLIGHT_TEXT)
    },
    "dark_palette": {
        "window": QColor(COLOR_BREEZE_DARK_WINDOW),
        "window_text": QColor(COLOR_BREEZE_DARK_WINDOW_TEXT),
        "base": QColor(COLOR_BREEZE_DARK_BASE),
        "text": QColor(COLOR_BREEZE_DARK_TEXT),
        "button": QColor(COLOR_BREEZE_DARK_BUTTON),
        "button_text": QColor(COLOR_BREEZE_DARK_BUTTON_TEXT),
        "highlight": QColor(COLOR_BREEZE_PRIMARY),
        "highlight_text": QColor(COLOR_BREEZE_DARK_HIGHLIGHT_TEXT)
    },
    "table_style": f"""
        QTableWidget {{
            background-color: {COLOR_BREEZE_LIGHT_BASE};
            alternate-background-color: {QColor(COLOR_BREEZE_LIGHT_BASE).lighter(105).name()};
            gridline-color: {COLOR_BREEZE_LIGHT_BORDER};
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
            selection-background-color: {COLOR_BREEZE_PRIMARY};
            selection-color: white;
        }}
        QTableWidget::item {{
            padding: 4px;
        }}
        QHeaderView::section {{
            background-color: {QColor(COLOR_BREEZE_LIGHT_WINDOW).lighter(105).name()};
            padding: 6px;
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
            font-weight: bold;
            color: {COLOR_BREEZE_LIGHT_WINDOW_TEXT};
        }}
        QTableCornerButton::section {{
            background-color: {QColor(COLOR_BREEZE_LIGHT_WINDOW).lighter(105).name()};
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
        }}
    """,
    "dark_table_style": f"""
        QTableWidget {{
            background-color: {COLOR_BREEZE_DARK_BASE};
            alternate-background-color: {QColor(COLOR_BREEZE_DARK_BASE).lighter(105).name()};
            gridline-color: {COLOR_BREEZE_DARK_BORDER};
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
            color: {COLOR_BREEZE_DARK_TEXT};
            selection-background-color: {COLOR_BREEZE_PRIMARY};
            selection-color: white;
        }}
        QTableWidget::item {{
            padding: 4px;
        }}
        QHeaderView::section {{
            background-color: {QColor(COLOR_BREEZE_DARK_WINDOW).lighter(105).name()};
            padding: 6px;
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
            font-weight: bold;
            color: {COLOR_BREEZE_DARK_WINDOW_TEXT};
        }}
        QTableCornerButton::section {{
            background-color: {QColor(COLOR_BREEZE_DARK_WINDOW).lighter(105).name()};
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
        }}
    """,
    "groupbox_style": f"""
        QGroupBox {{
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
            border-radius: 4px;
            margin-top: 20px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
            font-weight: bold;
            color: {COLOR_BREEZE_LIGHT_WINDOW_TEXT};
        }}
    """,
    "dark_groupbox_style": f"""
        QGroupBox {{
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
            border-radius: 4px;
            margin-top: 20px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
            font-weight: bold;
            color: {COLOR_BREEZE_DARK_WINDOW_TEXT};
        }}
    """,
    "list_tree_style_template": """
        QAbstractItemView {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            font-size: {font_size}px;
        }}
        QAbstractItemView::item {{
            padding: 3px;
        }}
        QAbstractItemView::item:selected {{
            background-color: {highlight_color};
            color: {highlight_text_color};
        }}
        QHeaderView::section {{
            background-color: {header_bg_color};
            padding: 6px;
            border: 1px solid {border_color};
            font-weight: bold;
            color: {header_text_color};
        }}
    """,
    # MODIFICACIÓN 3: Estilo para QLineEdit y QComboBox con borde azul agua al enfocar
    "lineedit_combobox_style_template": """
        QLineEdit, QComboBox {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 3px;
            padding: 3px;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {accent_color}; /* Borde azul agua al enfocar */
        }}
        QComboBox::drop-down {{
            border: 0px;
        }}
        QComboBox::down-arrow {{
            image: url(no_image_needed);
        }}
    """,
    "checkbox_radiobutton_style_template": """
        QCheckBox {{ color: {text_color}; }}
        QRadioButton {{ color: {text_color}; }}
    """
}

# Deshabilitar verificación SSL (usar con precaución y solo si las fuentes son de confianza).
ssl._create_default_https_context = ssl._create_unverified_context

class ConfigManager:
    """
    Gestor optimizado para configuraciones persistentes, incluyendo rutas, temas y repositorios.
    Asegura la estructura básica de configuración al inicio.
    """
    def __init__(self, app_instance):
        self.app_instance = app_instance # Referencia a la instancia de InstallerApp
        self.config_dir = Path.home() / ".config" / "WineProtonManager"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.log_dir = self.config_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.installation_log_file = self.log_dir / "installation.log"

        self.wine_download_dir = self.config_dir / "Wine"
        self.proton_download_dir = self.config_dir / "Proton"
        self.wine_download_dir.mkdir(exist_ok=True)
        self.proton_download_dir.mkdir(exist_ok=True)
        self.programs_dir = self.config_dir / "Programas"
        self.programs_dir.mkdir(exist_ok=True)

        self.backup_dir = self.config_dir / "Backup"
        self.backup_dir.mkdir(exist_ok=True)

        self.last_browsed_dirs = {
            "wine_prefix": str(self.wine_download_dir),
            "proton_prefix": str(self.proton_download_dir),
            "wine_install": str(self.wine_download_dir),
            "proton_install": str(self.proton_download_dir),
            "programs": str(self.programs_dir),
            "winetricks": str(Path.home())
        }

        self.configs = self._load_configs()
        self._ensure_default_config()

    def _ensure_default_config(self):
        """Asegura que existan configuraciones básicas, inicializándolas si faltan."""
        default_settings = {
            "winetricks_path": str(Path(__file__).parent / "AppDir" / "usr" / "bin" / "winetricks"),
            "config_path": str(self.config_file),
            "theme": "dark",
            "window_size": [900, 650],
            "silent_install": True,
            "force_winetricks_install": False,
            "ask_for_backup_before_action": True,
            "last_browsed_dirs": self.last_browsed_dirs,
            "last_full_backup_path": {} # MODIFICACIÓN: Cambiado a un diccionario para almacenar por configuración
        }

        default_repositories = {
            "proton": [
                {"name": "GloriousEggroll Proton", "url": "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases", "enabled": True}
            ],
            "wine": [
                {"name": "Kron4ek Wine Builds", "url": "https://api.github.com/repos/Kron4ek/Wine-Builds/releases", "enabled": True}
            ]
        }

        self.configs.setdefault("configs", {})
        self.configs.setdefault("last_used", "Wine-System")
        self.configs.setdefault("settings", default_settings)
        self.configs.setdefault("repositories", default_repositories)
        self.configs.setdefault("custom_programs", [])

        for key, value in default_settings.items():
            # Si 'last_full_backup_path' existe pero no es un diccionario (e.g. era una cadena de texto de una versión anterior)
            # lo convertimos a un diccionario vacío para evitar errores.
            if key == "last_full_backup_path" and not isinstance(self.configs["settings"].get(key), dict):
                self.configs["settings"][key] = {}
            else:
                self.configs["settings"].setdefault(key, value)


        if "last_browsed_dirs" not in self.configs["settings"]:
            self.configs["settings"]["last_browsed_dirs"] = self.last_browsed_dirs
        else:
            for key, default_path in self.last_browsed_dirs.items():
                self.configs["settings"]["last_browsed_dirs"].setdefault(key, default_path)
            self.last_browsed_dirs = self.configs["settings"]["last_browsed_dirs"]

        # MODIFICACIÓN: Ya no se necesita esta línea si 'last_full_backup_path' se inicializa como {}
        # if "last_full_backup_path" not in self.configs["settings"]:
        #    self.configs["settings"]["last_full_backup_path"] = ""

        if "Wine-System" not in self.configs["configs"]:
            self.configs["configs"]["Wine-System"] = {
                "type": "wine",
                "prefix": str(Path.home() / ".wine"),
                "arch": "win64"
            }

        self.save_configs()

    def _load_configs(self):
        """Carga las configuraciones desde el archivo JSON. Devuelve un diccionario vacío si falla o no existe."""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_configs = json.load(f)
                if "settings" in loaded_configs and "last_browsed_dirs" in loaded_configs["settings"]:
                    self.last_browsed_dirs = loaded_configs["settings"]["last_browsed_dirs"]
                return loaded_configs
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error cargando el archivo de configuración {self.config_file}: {e}. Se usará la configuración por defecto.")
            return {}

    def save_configs(self):
        """Guarda las configuraciones en el archivo JSON con manejo de errores."""
        try:
            self.configs["settings"]["last_browsed_dirs"] = self.last_browsed_dirs
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error guardando el archivo de configuración {self.config_file}: {e}")

    def get_config(self, config_name: str) -> dict | None:
        """Obtiene una configuración específica por nombre."""
        return self.configs.get("configs", {}).get(config_name)

    def get_current_environment(self, config_name: str) -> dict:
        """
        Obtiene las variables de entorno para la configuración dada.
        Valida la existencia de los ejecutables clave de Wine/Proton.
        """
        config = self.get_config(config_name)
        if not config:
            raise ValueError(f"Configuración '{config_name}' no encontrada.")

        env = os.environ.copy()
        env["WINEPREFIX"] = config["prefix"]
        env["WINEARCH"] = config.get("arch", "win64")

        wine_executable = "wine"
        wineserver_executable = "wineserver"
        path_override = ""

        if config.get("type") == "proton":
            proton_dir = Path(config["proton_dir"])
            wine_executable = str(proton_dir / "files/bin/wine")
            wineserver_executable = str(proton_dir / "files/bin/wineserver")
            path_override = str(proton_dir / "files/bin")

            if not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el directorio de Proton: {wine_executable}")

            if "steam_appid" in config and config["steam_appid"]:
                steam_compat_data_path_base = Path.home() / ".local/share/Steam/steamapps/compatdata"
                # Asegurarse de que el WINEPREFIX es el correcto para Steam
                if not Path(env["WINEPREFIX"]).is_relative_to(steam_compat_data_path_base / config["steam_appid"]):
                    env["WINEPREFIX"] = str(steam_compat_data_path_base / config["steam_appid"] / "pfx")

                env["STEAM_COMPAT_DATA_PATH"] = str(steam_compat_data_path_base / config["steam_appid"])
                env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(Path.home() / ".local/share/Steam")
                env["STEAM_COMPAT_SHADER_PATH"] = str(Path(env["STEAM_COMPAT_DATA_PATH"]) / "shadercache")
                env["STEAM_COMPAT_MOUNTPOINT"] = str(Path(env["STEAM_COMPAT_DATA_PATH"]) / "pfx")

            env["PROTON_DIR"] = str(proton_dir)
            version_file = proton_dir / "version"
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    env["PROTON_VERSION"] = f.read().strip()

            try:
                result = subprocess.run([wine_executable, "--version"], env=env, capture_output=True, text=True, check=True, timeout=5)
                env["WINE_VERSION_IN_PROTON"] = result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                env["WINE_VERSION_IN_PROTON"] = "N/A (Error al obtener versión o tiempo de espera agotado)"

        else: # type == "wine"
            wine_dir = config.get("wine_dir")
            if wine_dir:
                wine_dir = Path(wine_dir)
                wine_executable = str(wine_dir / "bin/wine")
                wineserver_executable = str(wine_dir / "bin/wineserver")
                path_override = str(wine_dir / "bin")

                if not Path(wine_executable).is_file():
                    raise FileNotFoundError(f"Ejecutable de Wine no encontrado en {wine_dir}: {wine_executable}")

                try:
                    result = subprocess.run([wine_executable, "--version"], capture_output=True, text=True, check=True, timeout=5)
                    env["WINE_VERSION"] = result.stdout.strip()
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    env["WINE_VERSION"] = "N/A (Error al obtener versión)"
            else: # Usar Wine del sistema
                try:
                    subprocess.run(["which", "wine"], capture_output=True, text=True, check=True, timeout=5)
                    result = subprocess.run(["wine", "--version"], capture_output=True, text=True, check=True, timeout=5)
                    env["WINE_VERSION"] = result.stdout.strip()
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    env["WINE_VERSION"] = "N/A (Versión no detectable)"

        if path_override:
            env["PATH"] = f"{path_override}:{os.environ.get('PATH', '')}"

        env["WINE"] = wine_executable
        env["WINESERVER"] = wineserver_executable

        return env

    def delete_custom_program(self, program_name: str) -> bool:
        """Elimina un programa personalizado por nombre."""
        initial_count = len(self.configs.get("custom_programs", []))
        self.configs["custom_programs"] = [
            p for p in self.configs.get("custom_programs", []) if p.get("name") != program_name
        ]
        if len(self.configs["custom_programs"]) < initial_count:
            self.save_configs()
            return True
        return False

    def get_custom_programs(self) -> list[dict]:
        """Obtiene la lista de programas personalizados, asegurando el campo 'type'."""
        programs = self.configs.get("custom_programs", [])
        for program in programs:
            program.setdefault("type", "winetricks") # Asegurar que 'type' exista
        return programs

    def add_custom_program(self, program_info: dict):
        """Añade un programa personalizado a la configuración."""
        self.configs.setdefault("custom_programs", []).append(program_info)
        self.save_configs()

    def set_theme(self, theme: str):
        """Establece el tema (claro/oscuro) y guarda la configuración.
        NOTA: Para que el cambio de tema se aplique globalmente, la aplicación debe reiniciarse.
        """
        self.configs.setdefault("settings", {})["theme"] = theme

    def get_theme(self) -> str:
        """Obtiene el tema actual. Por defecto es 'dark'."""
        return self.configs.get("settings", {}).get("theme", "dark")

    def get_winetricks_path(self) -> str:
        """
        Obtiene la ruta de winetricks en el siguiente orden de prioridad:
        1. Ruta configurada por el usuario.
        2. Ruta interna (AppDir).
        3. 'winetricks' (comando disponible en PATH).
        """
        configured_path = self.configs.get("settings", {}).get("winetricks_path", "")
        if configured_path and Path(configured_path).is_file():
            return configured_path

        internal_path = Path(__file__).parent / "AppDir" / "usr" / "bin" / "winetricks"
        if internal_path.exists() and internal_path.is_file():
            return str(internal_path)

        return "winetricks" # Fallback a winetricks en PATH

    def set_winetricks_path(self, path: str) -> bool:
        """Establece y valida la ruta de winetricks."""
        path = path.strip()
        if not path:
            return False

        if path == "winetricks" or Path(path).is_file():
            self.configs.setdefault("settings", {})["winetricks_path"] = path
            self.save_configs()
            return True
        else:
            QMessageBox.warning(None, "Ruta Inválida", "La ruta de Winetricks no es válida o no existe.")
            return False

    def set_silent_install(self, enabled: bool):
        """Establece si la instalación silenciosa está habilitada y guarda la configuración."""
        self.configs.setdefault("settings", {})["silent_install"] = enabled
        self.save_configs()

    def get_silent_install(self) -> bool:
        """Obtiene si la instalación silenciosa está habilitada. Por defecto es True."""
        return self.configs.get("settings", {}).get("silent_install", True)

    def set_force_winetricks_install(self, enabled: bool):
        """Establece si la instalación forzada de Winetricks está habilitada y guarda la configuración."""
        self.configs.setdefault("settings", {})["force_winetricks_install"] = enabled
        self.save_configs()

    def get_force_winetricks_install(self) -> bool:
        """Obtiene si la instalación forzada de Winetricks está habilitada. Por defecto es False."""
        return self.configs.get("settings", {}).get("force_winetricks_install", False)

    def set_ask_for_backup_before_action(self, enabled: bool):
        """Establece si se pregunta por backup antes de una acción y guarda la configuración."""
        self.configs.setdefault("settings", {})["ask_for_backup_before_action"] = enabled
        self.save_configs()

    def get_ask_for_backup_before_action(self) -> bool:
        """Obtiene si se pregunta por backup antes de una acción. Por defecto es True."""
        return self.configs.get("settings", {}).get("ask_for_backup_before_action", True)

    def set_last_full_backup_path(self, config_name: str, path: str):
        """Guarda la ruta del último backup completo exitoso para una configuración específica."""
        # Asegurarse de que el diccionario 'last_full_backup_path' exista en settings
        self.configs.setdefault("settings", {}).setdefault("last_full_backup_path", {})
        self.configs["settings"]["last_full_backup_path"][config_name] = path
        self.save_configs()

    def get_last_full_backup_path(self, config_name: str) -> str:
        """Obtiene la ruta del último backup completo exitoso para una configuración específica."""
        # Acceder al diccionario y devolver la ruta para el config_name dado, o una cadena vacía si no existe.
        return self.configs.get("settings", {}).get("last_full_backup_path", {}).get(config_name, "")

    def delete_config(self, config_name: str) -> bool:
        """Elimina una configuración guardada, ajustando 'last_used' si es necesario."""
        if config_name in self.configs.get("configs", {}):
            del self.configs["configs"][config_name]
            if self.configs["last_used"] == config_name:
                self.configs["last_used"] = "Wine-System" if "Wine-System" in self.configs["configs"] else ""
            self.save_configs()
            return True
        return False

    def get_installed_winetricks(self, prefix_path: str) -> list[str]:
        """
        Obtiene la lista de componentes de winetricks instalados en un prefijo
        desde el archivo wineprotomanager.ini.
        """
        wineprotonmanager_ini = Path(prefix_path) / "wineprotonmanager.ini"
        installed = set()
        if wineprotonmanager_ini.exists():
            try:
                with open(wineprotonmanager_ini, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        match = re.search(r"installed\s+(\S+)", line)
                        if match:
                            installed.add(match.group(1))

            except Exception as e:
                print(f"Error leyendo el archivo wineprotomanager.ini: {e}")
        return list(installed)

    def save_window_size(self, size: QSize):
        """Guarda el tamaño de la ventana."""
        self.configs.setdefault("settings", {})["window_size"] = [size.width(), size.height()]
        self.save_configs()

    def get_window_size(self) -> QSize:
        """Obtiene el tamaño de ventana guardado. Por defecto es 900x650."""
        size = self.configs.get("settings", {}).get("window_size", [900, 650])
        return QSize(size[0], size[1])

    def get_log_path(self) -> Path:
        """Obtiene la ruta al archivo de registro unificado para la instalación."""
        return self.installation_log_file

    def write_to_log(self, program_name: str, message: str):
        """Escribe un mensaje con marca de tiempo en el registro de instalación unificado."""
        log_path = self.get_log_path()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] [{program_name}] {message}\n")
        except IOError as e:
            print(f"Error escribiendo en el log {log_path}: {e}")

    def get_backup_log_path(self) -> Path:
        """Obtiene la ruta al archivo de registro de backup."""
        current_config_name = self.configs.get("last_used", "default")
        log_sub_dir = self.log_dir / current_config_name # Todavía se mantiene un subdirectorio para logs de backup
        log_sub_dir.mkdir(parents=True, exist_ok=True)
        return log_sub_dir / "backup.log"

    def write_to_backup_log(self, message: str):
        """Escribe un mensaje con marca de tiempo en el registro de backup."""
        log_path = self.get_backup_log_path()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except IOError as e:
            print(f"Error escribiendo en el log de backup {log_path}: {e}")

    def get_repositories(self, type_: str) -> list[dict]:
        """Obtiene repositorios para Wine o Proton."""
        return self.configs.get("repositories", {}).get(type_, [])

    def add_repository(self, type_: str, name: str, url: str) -> bool:
        """Añade un nuevo repositorio, evitando duplicados."""
        repos = self.configs.setdefault("repositories", {}).setdefault(type_, [])
        if not any(r["url"] == url for r in repos):
            repos.append({"name": name, "url": url, "enabled": True})
            self.save_configs()
            return True
        return False

    def delete_repository(self, type_: str, index: int) -> bool:
        """Elimina un repositorio por índice."""
        if "repositories" in self.configs and type_ in self.configs["repositories"]:
            if 0 <= index < len(self.configs["repositories"][type_]):
                del self.configs["repositories"][type_][index]
                self.save_configs()
                return True
        return False

    def toggle_repository(self, type_: str, index: int, enabled: bool) -> bool:
        """Habilita/deshabilita un repositorio por índice."""
        if "repositories" in self.configs and type_ in self.configs["repositories"]:
            if 0 <= index < len(self.configs["repositories"][type_]):
                self.configs["repositories"][type_][index]["enabled"] = enabled
                self.save_configs()
                return True
        return False

    def get_last_browsed_dir(self, key: str) -> str:
        """Obtiene la última carpeta explorada para una clave específica."""
        return self.last_browsed_dirs.get(key, str(Path.home()))

    def set_last_browsed_dir(self, key: str, path: str):
        """Establece la última carpeta explorada para una clave específica."""
        if Path(path).is_dir():
            self.last_browsed_dirs[key] = path
            self.save_configs() # Guardar inmediatamente para persistencia

    def apply_breeze_style_to_widget(self, widget: QWidget):
        """Aplica el estilo Breeze a un widget y sus hijos de forma recursiva."""

        theme = self.get_theme()
        style_settings = STYLE_BREEZE

        # Aplicar paleta principal
        palette = QPalette()
        current_palette_colors = style_settings["dark_palette"] if theme == "dark" else style_settings["light_palette"]

        palette.setColor(QPalette.Window, current_palette_colors["window"])
        palette.setColor(QPalette.WindowText, current_palette_colors["window_text"])
        palette.setColor(QPalette.Base, current_palette_colors["base"])
        palette.setColor(QPalette.Text, current_palette_colors["text"])
        palette.setColor(QPalette.Button, current_palette_colors["button"])
        palette.setColor(QPalette.ButtonText, current_palette_colors["button_text"])
        palette.setColor(QPalette.Highlight, current_palette_colors["highlight"])
        palette.setColor(QPalette.HighlightedText, current_palette_colors["highlight_text"])
        palette.setColor(QPalette.ToolTipBase, current_palette_colors["base"])
        palette.setColor(QPalette.ToolTipText, current_palette_colors["text"])

        widget.setPalette(palette)
        widget.setFont(style_settings["font"])

        # Aplicar estilos CSS específicos a los hijos
        for child_widget in widget.findChildren(QWidget):
            if isinstance(child_widget, QApplication) or (isinstance(child_widget, QWidget) and not isinstance(child_widget, (QPushButton, QTableWidget, QGroupBox, QListWidget, QTreeWidget, QLineEdit, QComboBox, QCheckBox, QRadioButton))):
                continue

            child_widget.setFont(style_settings["font"])

            if isinstance(child_widget, QPushButton):
                child_widget.setStyleSheet(style_settings["dark_button_style"] if theme == "dark" else style_settings["button_style"])
            elif isinstance(child_widget, QTableWidget):
                child_widget.setStyleSheet(style_settings["dark_table_style"] if theme == "dark" else style_settings["table_style"])
            elif isinstance(child_widget, QGroupBox):
                child_widget.setStyleSheet(style_settings["dark_groupbox_style"] if theme == "dark" else style_settings["groupbox_style"])
                child_widget.setFont(style_settings["title_font"])
            elif isinstance(child_widget, (QListWidget, QTreeWidget)):
                list_tree_bg = style_settings["dark_palette"]["base"] if theme == "dark" else style_settings["light_palette"]["base"]
                list_tree_text = style_settings["dark_palette"]["text"] if theme == "dark" else style_settings["light_palette"]["text"]
                list_tree_border = style_settings["dark_border"] if theme == "dark" else style_settings["light_border"]
                list_tree_highlight = style_settings["dark_palette"]["highlight"] if theme == "dark" else style_settings["light_palette"]["highlight"]
                list_tree_highlight_text = style_settings["dark_palette"]["highlight_text"] if theme == "dark" else style_settings["light_palette"]["highlight_text"]
                header_bg = style_settings["dark_palette"]["button"] if theme == "dark" else style_settings["light_palette"]["button"]
                header_text = style_settings["dark_palette"]["button_text"] if theme == "dark" else style_settings["light_palette"]["button_text"]

                child_widget.setStyleSheet(style_settings["list_tree_style_template"].format(
                    bg_color=list_tree_bg.name(),
                    text_color=list_tree_text.name(),
                    border_color=list_tree_border,
                    font_size=style_settings["font"].pointSize(), # Se usa el tamaño de fuente general
                    highlight_color=list_tree_highlight.name(),
                    highlight_text_color=list_tree_highlight_text.name(),
                    header_bg_color=header_bg.name(),
                    header_text_color=header_text.name()
                ))

            elif isinstance(child_widget, (QLineEdit, QComboBox)):
                bg_color = style_settings["dark_palette"]["base"].name() if theme == "dark" else style_settings["light_palette"]["base"].name()
                text_color = style_settings["dark_palette"]["text"].name() if theme == "dark" else style_settings["light_palette"]["text"].name()
                border_color = style_settings["dark_border"] if theme == "dark" else style_settings["light_border"]
                accent_color = COLOR_BREEZE_ACCENT # Color de borde para el foco

                child_widget.setStyleSheet(STYLE_BREEZE["lineedit_combobox_style_template"].format(
                    bg_color=bg_color,
                    text_color=text_color,
                    border_color=border_color,
                    accent_color=accent_color
                ))
            elif isinstance(child_widget, (QCheckBox, QRadioButton)):
                text_color = style_settings["dark_palette"]["text"].name() if theme == "dark" else style_settings["light_palette"]["text"].name()
                child_widget.setStyleSheet(STYLE_BREEZE["checkbox_radiobutton_style_template"].format(
                    text_color=text_color
                ))

        widget.repaint()

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url: str, destination_path: Path, name: str, config_manager: ConfigManager):
        super().__init__()
        self.url = url
        self.destination = destination_path
        self.name = name
        self.config_manager = config_manager
        self._is_running = True

    def run(self):
        self.config_manager.write_to_log(self.name, f"Iniciando descarga de {self.url} a {self.destination}")
        try:
            req = Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=30) as response:
                if response.getcode() != 200:
                    raise HTTPError(self.url, response.getcode(), response.reason, response.headers, None)

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192

                free_space = shutil.disk_usage(self.destination.parent).free
                # Espacio requerido: tamaño total * 2 (para el archivo comprimido y la descompresión) o 500MB
                required_space = total_size * 2 if total_size > 0 else 500 * 1024 * 1024

                if free_space < required_space:
                    raise IOError(f"Espacio en disco insuficiente en {self.destination.parent}. Requerido: {required_space / (1024*1024):.1f} MB, Disponible: {free_space / (1024*1024):.1f} MB")

                if self.destination.exists():
                    try:
                        self.destination.unlink()
                    except OSError as e:
                        raise IOError(f"No se pudo eliminar el archivo parcial existente {self.destination}: {e}")

                with open(self.destination, 'wb') as f:
                    while self._is_running:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = int(downloaded * 100 / total_size)
                            self.progress.emit(progress)

                if not self._is_running:
                    # Si se cancela, intentar eliminar el archivo parcial
                    if self.destination.exists():
                        try:
                            self.destination.unlink()
                        except OSError:
                            pass
                    self.config_manager.write_to_log(self.name, f"Descarga de {self.name} cancelada.")
                    return

                self.finished.emit(str(self.destination))
                self.config_manager.write_to_log(self.name, f"Descarga de {self.name} completada.")

        except HTTPError as e:
            msg = f"Error HTTP descargando {self.url}: {e.code} - {e.reason}"
            self.config_manager.write_to_log(self.name, f"ERROR: {msg}")
            self.error.emit(msg)
        except Exception as e:
            msg = f"Error inesperado durante la descarga de {self.name}: {str(e)}"
            self.config_manager.write_to_log(self.name, f"ERROR: {msg}")
            if self.destination.exists(): # Intentar limpiar si hubo un error
                try:
                    self.destination.unlink()
                except OSError:
                    pass
            self.error.emit(msg)

    def stop(self):
        """Detiene la descarga."""
        self._is_running = False

class DecompressionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int) # Este hilo no emite progreso detallado, pero se mantiene para consistencia

    def __init__(self, archive_path: str, config_manager: ConfigManager, name: str):
        super().__init__()
        self.archive_path = Path(archive_path)
        self.config_manager = config_manager
        self.name = name
        self.target_dir = None
        self._is_running = True

    def _set_permissions_recursively(self, path: Path):
        """Aplica permisos 0o755 (ejecutable para todos) a directorios y archivos específicos, 0o644 a otros archivos."""
        if not path.exists():
            return

        try:
            if path.is_dir():
                os.chmod(path, 0o755)
                for item in path.iterdir():
                    self._set_permissions_recursively(item)
            elif path.is_file():
                # Aplicar permisos ejecutables a archivos en directorios 'bin' o con nombres específicos
                if "bin" in path.parts or "wine" in path.name.lower() or "wineserver" in path.name.lower():
                    os.chmod(path, 0o755)
                else:
                    os.chmod(path, 0o644)
        except OSError as e:
            self.config_manager.write_to_log(self.name, f"Advertencia: No se pudieron establecer permisos en {path}: {e}")

    def run(self):
        self.config_manager.write_to_log(self.name, f"Iniciando descompresión de {self.archive_path}")
        try:
            if not self.archive_path.exists():
                raise FileNotFoundError(f"El archivo {self.archive_path} no existe.")

            dest_dir_root = self.archive_path.parent
            base_name = self.archive_path.stem # nombre sin la última extensión
            # Si es un archivo tipo .tar.gz o .tar.xz, quitar también la extensión .tar
            if self.archive_path.suffix in ['.gz', '.xz', '.zip'] and base_name.endswith('.tar'):
                base_name = Path(base_name).stem

            self.target_dir = dest_dir_root / base_name

            if self.target_dir.exists():
                self.config_manager.write_to_log(self.name, f"El directorio de destino {self.target_dir} ya existe. Eliminando...")
                shutil.rmtree(self.target_dir)

            with tempfile.TemporaryDirectory(prefix="wpm_decompress_") as temp_unzip_dir_str:
                temp_unzip_dir = Path(temp_unzip_dir_str)
                self.config_manager.write_to_log(self.name, f"Descomprimiendo al directorio temporal: {temp_unzip_dir}")

                if self.archive_path.suffix == '.zip':
                    with zipfile.ZipFile(self.archive_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_unzip_dir)
                elif self.archive_path.suffix in ['.gz', '.xz', '.bz2', '.zst'] or self.archive_path.name.endswith(('.tar.gz', '.tar.xz', '.tar.bz2', '.tar.zst')):
                    # Determinar el modo correcto para tarfile
                    mode = "r:" + self.archive_path.suffix[1:]
                    if self.archive_path.name.endswith('.tar.gz'):
                        mode = "r:gz"
                    elif self.archive_path.name.endswith('.tar.xz'):
                        mode = "r:xz"
                    elif self.archive_path.name.endswith('.tar.bz2'):
                        mode = "r:bz2"
                    elif self.archive_path.name.endswith('.tar.zst'): # Experimental
                        mode = "r:zst"

                    with tarfile.open(self.archive_path, mode) as tar:
                        # Usar filtro 'data' para evitar problemas de permisos o archivos especiales
                        tar.extractall(path=temp_unzip_dir, filter='data')
                else:
                    raise ValueError(f"Formato de archivo no compatible para descompresión: {self.archive_path.suffix}")

                # Buscar el directorio principal si el archivo se descomprime en un subdirectorio
                extracted_contents = list(temp_unzip_dir.iterdir())
                if len(extracted_contents) == 1 and extracted_contents[0].is_dir():
                    source_dir_to_move = extracted_contents[0]
                else:
                    source_dir_to_move = temp_unzip_dir

                self.config_manager.write_to_log(self.name, f"Moviendo {source_dir_to_move} a {self.target_dir}")
                shutil.move(str(source_dir_to_move), str(self.target_dir))

                self._set_permissions_recursively(self.target_dir)

            # Eliminar el archivo comprimido original
            try:
                self.archive_path.unlink()
                self.config_manager.write_to_log(self.name, f"Archivo comprimido {self.archive_path} eliminado.")
            except OSError as e:
                self.config_manager.write_to_log(self.name, f"Advertencia: No se pudo eliminar el archivo comprimido {self.archive_path}: {e}")

            self.finished.emit(str(self.target_dir))
            self.config_manager.write_to_log(self.name, f"Descompresión de {self.name} completada. Ruta: {self.target_dir}")

        except Exception as e:
            msg = f"Error descomprimiendo {self.name}: {str(e)}"
            self.config_manager.write_to_log(self.name, f"ERROR: {msg}")
            # Limpiar directorio de destino si la descompresión falló
            if self.target_dir and self.target_dir.exists():
                try:
                    shutil.rmtree(self.target_dir, ignore_errors=True)
                    self.config_manager.write_to_log(self.name, f"Directorio incompleto {self.target_dir} eliminado después del error.")
                except OSError as cleanup_error:
                    self.config_manager.write_to_log(self.name, f"Error limpiando {self.target_dir}: {cleanup_error}")
            self.error.emit(msg)

    def stop(self):
        """Detiene la descompresión (no es directamente cancelable en tar/zip de Python, pero establece la bandera)."""
        self._is_running = False

class InstallerThread(QThread):
    progress = pyqtSignal(str, str) # Emite (nombre_del_elemento, estado)
    finished = pyqtSignal()
    error = pyqtSignal(str) # Ahora se usa para errores globales o al final del bucle
    item_error = pyqtSignal(str, str) # [MODIFICACIÓN 1] Nuevo: Emite (nombre_del_elemento, mensaje_de_error_específico) cuando falla un solo ítem.
    canceled = pyqtSignal(str) # Emite (nombre_del_elemento) cuando se cancela
    console_output = pyqtSignal(str) # Emite salida de consola en tiempo real

    def __init__(self, items_to_install: list[tuple[str, str, str]], env: dict, silent_mode: bool, force_mode: bool, winetricks_path: str, config_manager: ConfigManager):
        super().__init__()
        self.items_to_install = items_to_install # Lista de (ruta_o_nombre, tipo, nombre_mostrar)
        self.env = env
        self.silent_mode = silent_mode
        self.force_mode = force_mode
        self.winetricks_path = winetricks_path
        self.config_manager = config_manager
        self._is_running = True
        self.current_process: subprocess.Popen | None = None

    def run(self):
        try:
            # Verificar si wine/proton es accesible antes de empezar
            wine_executable = self.env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                # [MODIFICACIÓN 1] Emitir un error fatal si el ejecutable principal no se encuentra
                self.error.emit(f"Ejecutable de Wine/Proton no encontrado o no ejecutable: {wine_executable}")
                return

            # Verificar winetricks si se va a usar
            if any(item[1] in ["winetricks", "wtr"] for item in self.items_to_install):
                winetricks_executable = self.winetricks_path
                if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
                    # [MODIFICACIÓN 1] Emitir un error fatal si winetricks no se encuentra y se necesita
                    self.error.emit(f"Ejecutable de Winetricks no encontrado o no ejecutable: {winetricks_executable}")
                    return

        except EnvironmentError as e:
            self.error.emit(str(e))
            return

        for idx, (item_path_or_name, item_type, user_defined_name) in enumerate(self.items_to_install):
            if not self._is_running:
                self.canceled.emit(user_defined_name)
                # [MODIFICACIÓN 1] Ya no se usa 'break' aquí, la cancelación se maneja de forma más granular
                # El bucle termina si _is_running es False
                break # El bucle for debe terminar si se ha cancelado

            display_name_for_progress = user_defined_name

            self.progress.emit(display_name_for_progress, f"Instalando")
            self.config_manager.write_to_log(display_name_for_progress, f"Iniciando instalación: {item_path_or_name} (Tipo: {item_type}, Silencioso: {self.silent_mode}, Forzado: {self.force_mode})")

            temp_log_path = None # Se sigue usando temp_log_path para capturar stdout/stderr del proceso antes de agregarlo al log unificado.
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".log", mode='w+', encoding='utf-8') as temp_log_file:
                    temp_log_path = Path(temp_log_file.name)

                if item_type == "exe":
                    self._install_exe(item_path_or_name, temp_log_path, display_name_for_progress)
                elif item_type == "winetricks":
                    self._install_winetricks(item_path_or_name, temp_log_path, display_name_for_progress)
                elif item_type == "wtr":
                    self._install_winetricks_script(item_path_or_name, temp_log_path, display_name_for_progress)
                else:
                    raise ValueError(f"Tipo de instalación no reconocido: {item_type}")

                self._register_successful_installation(display_name_for_progress, item_type, item_path_or_name) # MODIFICACIÓN 3: Pasar item_type y item_path_or_name
                self.progress.emit(display_name_for_progress, f"Finalizado")
                self.config_manager.write_to_log(display_name_for_progress, f"Instalación de {display_name_for_progress} completada exitosamente.")

            except Exception as e:
                # [MODIFICACIÓN 1] Ahora emitimos 'item_error' y continuamos el bucle
                error_msg = f"Comando fallido para {display_name_for_progress}. Detalles:\n"
                if isinstance(e, subprocess.CalledProcessError):
                    error_msg += f"Comando: {' '.join(e.cmd)}\nCódigo de Salida: {e.returncode}\nSalida/Error: {e.output or e.stderr}"
                else:
                    error_msg += str(e)

                self.config_manager.write_to_log(display_name_for_progress, f"ERROR: DURANTE LA INSTALACIÓN: {error_msg}")
                self.progress.emit(display_name_for_progress, f"Error") # Actualiza el estado en la UI
                self.item_error.emit(display_name_for_progress, error_msg) # Emitir error específico del ítem
                # No se usa 'break', la instalación continúa con el siguiente ítem
            finally:
                if temp_log_path and temp_log_path.exists():
                    try:
                        temp_log_path.unlink() # Limpiar el archivo de log temporal
                        retcode_file = Path(str(temp_log_path) + ".retcode")
                        if retcode_file.exists():
                            retcode_file.unlink()
                    except OSError as e:
                        self.config_manager.write_to_log(display_name_for_progress, f"Advertencia: No se pudo eliminar el archivo temporal {temp_log_path}: {e}")

        # [MODIFICACIÓN 1] La señal 'finished' se emite solo cuando todos los ítems han sido procesados.
        if self._is_running: # Solo si no se ha cancelado globalmente
            self.finished.emit()

    def _install_exe(self, exe_path: str, temp_log_path: Path, display_name: str):
        """Ejecuta un archivo .exe usando Wine/Proton, capturando la salida."""
        exe_path = Path(exe_path)
        if not exe_path.exists():
            raise FileNotFoundError(f"El archivo EXE no existe: {exe_path}")

        wine_executable = self.env.get("WINE")
        # Ya verificado al inicio de run(), pero una doble verificación no hace daño
        if not wine_executable or not Path(wine_executable).is_file():
            raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")

        cmd = [wine_executable, str(exe_path)]
        self.config_manager.write_to_log(display_name, f"Comando EXE: {' '.join(cmd)}")
        self._execute_command_and_capture_output(cmd, display_name, temp_log_path)

    def _install_winetricks(self, component_name: str, temp_log_path: Path, display_name: str):
        """Ejecuta un comando de winetricks, capturando la salida."""
        winetricks_executable = self.winetricks_path
        if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
            raise FileNotFoundError(f"Ejecutable de Winetricks no encontrado: {winetricks_executable}")

        silent_flag = "-q" if self.silent_mode else ""
        force_flag = "--force" if self.force_mode else ""

        cmd = [winetricks_executable, silent_flag, force_flag, component_name]
        cmd = [c for c in cmd if c] # Elimina los flags vacíos

        self.config_manager.write_to_log(display_name, f"Comando Winetricks: {' '.join(cmd)}")
        self._execute_command_and_capture_output(cmd, display_name, temp_log_path)

    def _install_winetricks_script(self, script_path: str, temp_log_path: Path, display_name: str):
        """Ejecuta un script personalizado de Winetricks (.wtr), capturando la salida."""
        script_path = Path(script_path)
        if not script_path.exists():
            raise FileNotFoundError(f"El archivo de script de Winetricks no existe: {script_path}")

        winetricks_executable = self.winetricks_path
        if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
            raise FileNotFoundError(f"Ejecutable de Winetricks no encontrado: {winetricks_executable}")

        silent_flag = "-q" if self.silent_mode else ""
        force_flag = "--force" if self.force_mode else ""

        cmd = [winetricks_executable, silent_flag, force_flag, str(script_path)]
        cmd = [c for c in cmd if c] # Elimina los flags vacíos

        self.config_manager.write_to_log(display_name, f"Comando de script Winetricks: {' '.join(cmd)}")
        self._execute_command_and_capture_output(cmd, display_name, temp_log_path)

    def _execute_command_and_capture_output(self, cmd: list[str], display_name: str, temp_log_path: Path):
        """Ejecuta un comando, captura su salida y la emite para la ventana emergente."""
        try:
            self.current_process = subprocess.Popen(
                cmd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Capturar stdout y stderr juntos
                text=True, # Modo texto para unicode
                bufsize=1, # Line-buffered
                universal_newlines=True, # Para compatibilidad de saltos de línea
                preexec_fn=os.setsid # Crear un nuevo grupo de procesos para matar hijos
            )

            log_content = ""
            while True:
                line = self.current_process.stdout.readline()
                if not line:
                    break
                log_content += line
                self.console_output.emit(line.strip())
                QApplication.processEvents() # Permitir que la UI se actualice

            # Esperar a que el proceso termine después de leer toda la salida
            self.current_process.wait(timeout=300) # Tiempo de espera para la ejecución del comando

            retcode = self.current_process.returncode

            # Escribir el log completo al archivo temporal (esto es solo para debugging si se desea)
            with open(temp_log_path, 'w', encoding='utf-8') as f:
                f.write(log_content)

            self.config_manager.write_to_log(display_name, "=== INICIO DEL LOG DEL PROCESO ===")
            self.config_manager.write_to_log(display_name, log_content)
            self.config_manager.write_to_log(display_name, f"Código de retorno del proceso: {retcode}")
            self.config_manager.write_to_log(display_name, "=== FIN DEL LOG DEL PROCESO ===\n")

            if retcode != 0:
                raise subprocess.CalledProcessError(retcode, cmd, output=log_content)

        except subprocess.TimeoutExpired:
            self.current_process.kill() # Matar proceso si se excede el tiempo
            raise Exception("El comando de instalación agotó el tiempo de espera.")
        except subprocess.CalledProcessError as e:
            # Relanzar el error para que sea capturado por el manejador de errores principal
            raise e
        except Exception as e:
            raise Exception(f"Error inesperado al ejecutar comando: {str(e)}")

    def _register_successful_installation(self, display_name: str, item_type: str, original_path_or_name: str): # MODIFICACIÓN 3: Nuevos parámetros
        """
        MODIFICACIÓN 3: Registra una instalación exitosa en el log del prefijo (wineprotomanager.ini).
        Añade más contexto al registro.
        """
        prefix_path = Path(self.env["WINEPREFIX"])
        # MODIFICACIÓN 3: Cambiar a wineprotomanager.ini
        log_file = prefix_path / "wineprotonmanager.ini"
        try:
            # Usar un formato simple para el .ini
            entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} installed {display_name} (Type: {item_type}, Source: {original_path_or_name})"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{entry}\n")
        except IOError as e:
            self.config_manager.write_to_log(display_name, f"Advertencia: No se pudo escribir en el log del prefijo {log_file}: {e}")

    def stop(self):
        """Detiene la instalación, incluyendo el proceso hijo."""
        self._is_running = False
        if self.current_process and self.current_process.poll() is None:
            try:
                # Usar os.killpg para matar el grupo de procesos y asegurar que los hijos también mueran
                os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGTERM)
                self.current_process.wait(5) # Dar tiempo para terminar limpiamente
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if self.current_process.poll() is None: # Si aún no ha terminado, forzar
                    os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGKILL)
            except Exception as e:
                self.config_manager.write_to_log("InstallerThread", f"Error al intentar detener el proceso de instalación: {e}")

# --- Hilo de Backup ---
class BackupThread(QThread):
    progress_update = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str, str) # MODIFICACIÓN: Añadir config_name al finished signal

    def __init__(self, source_path: Path, destination_path: Path, config_manager: ConfigManager, is_full_backup: bool, config_name: str): # MODIFICACIÓN: Añadir config_name
        super().__init__()
        self.source_path = source_path
        self.destination_path = destination_path
        self.config_manager = config_manager
        self.is_full_backup = is_full_backup
        self.config_name = config_name # Guardar config_name
        self._is_running = True
        self._process: subprocess.Popen | None = None

    def run(self):
        self.config_manager.write_to_backup_log(f"Iniciando backup de '{self.source_path}' a '{self.destination_path}' para '{self.config_name}'") # MODIFICACIÓN: Log más detallado
        try:
            if not self.source_path.exists() or not self.source_path.is_dir():
                raise FileNotFoundError(f"La carpeta de origen del prefijo no existe: {self.source_path}")

            rsync_command = ["rsync", "-av", "--no-o", "--no-g"]

            final_backup_path_str = "" # Inicializar aquí
            if not self.is_full_backup: # Si es backup incremental (rsync)
                rsync_command.append("--checksum")
                self.config_manager.write_to_backup_log("Realizando backup incremental con rsync --checksum.")
                rsync_command.append(f"{self.source_path}/")
                rsync_command.append(str(self.destination_path))
                final_backup_path_str = str(self.destination_path) # El destino es el backup existente
            else:
                self.config_manager.write_to_backup_log("Realizando backup completo (nueva carpeta con timestamp).")
                temp_backup_dir = self.destination_path.parent / (self.destination_path.name + "_tmp")
                temp_backup_dir.mkdir(parents=True, exist_ok=True)

                rsync_command.append(f"{self.source_path}/")
                rsync_command.append(str(temp_backup_dir))
                final_backup_path_str = str(self.destination_path) # Este es el nombre final deseado

            self.progress_update.emit("Iniciando sincronización...")
            self.config_manager.write_to_backup_log(f"Comando rsync: {' '.join(rsync_command)}")

            self._process = subprocess.Popen(rsync_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True, preexec_fn=os.setsid)

            while self._process.poll() is None and self._is_running:
                line = self._process.stdout.readline()
                if line:
                    self.progress_update.emit(line.strip())
                else:
                    QThread.msleep(50)
                QApplication.processEvents()

            stdout, stderr = self._process.communicate()

            if not self._is_running:
                self.finished.emit(False, "Backup cancelado por el usuario.", "", self.config_name) # MODIFICACIÓN: Añadir config_name
                self.config_manager.write_to_backup_log("Backup cancelado por el usuario.")
                if self.is_full_backup and temp_backup_dir.exists():
                    shutil.rmtree(temp_backup_dir, ignore_errors=True)
            elif self._process.returncode == 0:
                if self.is_full_backup:
                    shutil.move(str(temp_backup_dir), str(Path(final_backup_path_str))) # Asegurarse de que Path() se usa correctamente
                    self.config_manager.set_last_full_backup_path(self.config_name, final_backup_path_str) # MODIFICACIÓN: Guardar la ruta para esta config
                    success_msg = f"Backup COMPLETO de '{self.source_path.name}' completado exitosamente a '{final_backup_path_str}'."
                else:
                    success_msg = f"Backup INCREMENTAL de '{self.source_path.name}' completado exitosamente a '{self.destination_path}'."
                self.config_manager.write_to_backup_log(success_msg)
                self.finished.emit(True, success_msg, final_backup_path_str, self.config_name) # MODIFICACIÓN: Añadir config_name
            else:
                error_msg = f"Rsync falló con código {self._process.returncode}.\nStderr: {stderr}\nStdout: {stdout}"
                self.config_manager.write_to_backup_log(f"ERROR: {error_msg}")
                if self.is_full_backup and temp_backup_dir.exists():
                    shutil.rmtree(temp_backup_dir, ignore_errors=True)
                self.finished.emit(False, f"Error durante el backup: {stderr.strip() or stdout.strip()}", "", self.config_name) # MODIFICACIÓN: Añadir config_name

        except FileNotFoundError as e:
            msg = f"Error: Comando rsync no encontrado o ruta de origen/destino inválida. Asegúrate de que rsync esté instalado. {e}"
            self.config_manager.write_to_backup_log(f"ERROR: {msg}")
            self.finished.emit(False, msg, "", self.config_name) # MODIFICACIÓN: Añadir config_name
        except Exception as e:
            msg = f"Error inesperado durante el backup: {str(e)}"
            self.config_manager.write_to_backup_log(f"ERROR: {msg}")
            self.finished.emit(False, msg, "", self.config_name) # MODIFICACIÓN: Añadir config_name

    def stop(self):
        """Detiene el hilo y el subproceso de backup."""
        self._is_running = False
        if self._process and self._process.poll() is None:
            try:
                # Envía SIGINT para intentar una terminación limpia
                os.killpg(os.getpgid(self._process.pid), subprocess.signal.SIGINT)
            except ProcessLookupError:
                pass # El proceso ya no existe

class InstallationProgressDialog(QDialog):
    def __init__(self, item_name: str, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"Instalando: {item_name}")
        self.config_manager = config_manager
        self.item_name = item_name
        self.setWindowModality(Qt.NonModal) # Cambiado a NonModal
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.label = QLabel(f"Instalando: <b>{self.item_name}</b>")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        self.log_output = QListWidget()
        self.log_output.setSelectionMode(QListWidget.NoSelection)
        self.log_output.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.log_output.setWordWrap(True)
        main_layout.addWidget(self.log_output)

        self.close_button = QPushButton("Cerrar")
        self.close_button.setAutoDefault(False)
        self.close_button.clicked.connect(self.accept)
        # MODIFICACIÓN 1: El botón de cerrar siempre está habilitado en modo NonModal,
        # pero la señal `accepted` solo se emite si el usuario hace clic.
        # El diálogo se puede cerrar normalmente.
        self.close_button.setEnabled(True)

        main_layout.addWidget(self.close_button)
        self.setLayout(main_layout)

    def append_log(self, text: str):
        """Añade una línea al log de salida de la consola."""
        self.log_output.addItem(text)
        self.log_output.scrollToBottom()

    def set_status(self, status_text: str):
        """Actualiza el texto de estado en el diálogo."""
        self.label.setText(f"Estado de la Instalación: <b>{status_text}</b>")

    def closeEvent(self, event):
        """Permite el cierre del diálogo sin detener el hilo de instalación."""
        event.accept() # Siempre aceptar el evento de cierre

# --- Diálogos de Aplicación ---
class ConfigDialog(QDialog):
    config_saved = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Configuración de Entorno")
        self.setMinimumSize(825, 625)
        self.current_config_name_for_editing = None
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)
        self.load_configs()
        self.update_save_settings_button_state()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.current_tab = QWidget()
        self.setup_current_config_tab()
        self.tabs.addTab(self.current_tab, "Configuraciones Guardadas")

        self.new_tab = QWidget()
        self.setup_new_config_tab()
        self.tabs.addTab(self.new_tab, "Crear/Editar Configuración")

        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Ajustes Generales")

        self.downloads_tab = QWidget()
        # [CORRECCIÓN] Inicializar los QWidget para los tabs antes de llamar a setup_
        self.proton_tab = QWidget()  # Inicializar proton_tab aquí
        self.wine_tab = QWidget()    # Inicializar wine_tab aquí
        self.setup_downloads_tab()
        self.tabs.addTab(self.downloads_tab, "Descargas de Versiones")

        layout.addWidget(self.tabs)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.button(QDialogButtonBox.Close).setAutoDefault(False)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def setup_current_config_tab(self):
        layout = QVBoxLayout()
        self.list_config = QListWidget()
        self.list_config.itemDoubleClicked.connect(self.edit_config)
        self.list_config.itemSelectionChanged.connect(self.update_displayed_config_info)
        layout.addWidget(self.list_config)

        btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("Eliminar Configuración")
        self.btn_delete.setAutoDefault(False)
        self.btn_delete.clicked.connect(self.delete_config)
        btn_layout.addWidget(self.btn_delete)

        self.btn_set_default = QPushButton("Establecer por Defecto")
        self.btn_set_default.setAutoDefault(False)
        self.btn_set_default.clicked.connect(self.set_default_config)
        btn_layout.addWidget(self.btn_set_default)

        layout.addLayout(btn_layout)

        self.lbl_config_info = QLabel("Selecciona una configuración para ver los detalles")
        self.lbl_config_info.setWordWrap(True)
        layout.addWidget(self.lbl_config_info)
        self.current_tab.setLayout(layout)

    def setup_new_config_tab(self):
        layout = QFormLayout()

        self.config_type = QComboBox()
        self.config_type.addItems(["Wine", "Proton"])
        self.config_type.currentTextChanged.connect(self.update_config_field_visibility)
        layout.addRow("Tipo:", self.config_type)

        self.config_name = QLineEdit()
        layout.addRow("Nombre:", self.config_name)

        self.architecture_combo = QComboBox()
        self.architecture_combo.addItems(["win64", "win32"])
        layout.addRow("Arquitectura:", self.architecture_combo)

        self.prefix_path = QLineEdit()
        self.btn_prefix = QPushButton("Explorar...")
        self.btn_prefix.setAutoDefault(False)
        self.btn_prefix.clicked.connect(self.browse_prefix)
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(self.prefix_path)
        prefix_layout.addWidget(self.btn_prefix)
        layout.addRow("Ruta del Prefijo (WINEPREFIX):", prefix_layout)

        # Grupo para opciones de prefijo de Proton (personalizado o Steam)
        self.proton_prefix_type_group = QGroupBox("Tipo de Prefijo de Proton")
        proton_prefix_layout = QVBoxLayout()
        self.radio_proton_custom_prefix = QRadioButton("Prefijo personalizado")
        self.radio_proton_custom_prefix.setChecked(True) # Por defecto
        self.radio_proton_custom_prefix.toggled.connect(self.update_proton_prefix_options)

        self.radio_proton_steam_prefix = QRadioButton("Usar prefijo de Steam (por APPID)")
        self.radio_proton_steam_prefix.toggled.connect(self.update_proton_prefix_options)

        proton_prefix_layout.addWidget(self.radio_proton_custom_prefix)
        proton_prefix_layout.addWidget(self.radio_proton_steam_prefix)

        self.appid_line_edit = QLineEdit()
        self.appid_line_edit.setPlaceholderText("Ingresa el APPID de Steam (ej. 123456)")
        proton_prefix_layout.addWidget(self.appid_line_edit)
        self.appid_line_edit.hide() # Oculto por defecto

        self.proton_prefix_type_group.setLayout(proton_prefix_layout)
        layout.addRow(self.proton_prefix_type_group)

        # Grupo para configuración de Wine (directorio de instalación)
        self.wine_directory = QLineEdit()
        self.btn_wine = QPushButton("Explorar...")
        self.btn_wine.setAutoDefault(False)
        self.btn_wine.clicked.connect(self.browse_wine)
        wine_layout = QHBoxLayout()
        wine_layout.addWidget(self.wine_directory)
        wine_layout.addWidget(self.btn_wine)

        self.wine_group = QGroupBox("Configuración de Wine Personalizada")
        wine_inner_layout = QFormLayout()
        wine_inner_layout.addRow("Directorio de instalación de Wine:", wine_layout)
        self.wine_group.setLayout(wine_inner_layout)

        # Grupo para configuración de Proton (directorio de instalación)
        self.proton_directory = QLineEdit()
        self.btn_proton = QPushButton("Explorar...")
        self.btn_proton.setAutoDefault(False)
        self.btn_proton.clicked.connect(self.browse_proton)
        proton_layout = QHBoxLayout()
        proton_layout.addWidget(self.proton_directory)
        proton_layout.addWidget(self.btn_proton)

        self.proton_group = QGroupBox("Configuración de Proton Personalizada")
        proton_inner_layout = QFormLayout()
        proton_inner_layout.addRow("Directorio de instalación de Proton:", proton_layout)
        self.proton_group.setLayout(proton_inner_layout)

        layout.addRow(self.wine_group)
        layout.addRow(self.proton_group)

        self.btn_create_prefix = QPushButton("Crear/Inicializar Prefijo")
        self.btn_create_prefix.setAutoDefault(False)
        self.btn_create_prefix.clicked.connect(self.create_and_initialize_prefix)
        layout.addRow(self.btn_create_prefix)

        buttons_layout = QHBoxLayout()
        self.btn_test = QPushButton("Probar Configuración")
        self.btn_test.setAutoDefault(False)
        self.btn_test.clicked.connect(self.test_configuration)
        buttons_layout.addWidget(self.btn_test)

        self.btn_save_config = QPushButton("Guardar Configuración")
        self.btn_save_config.setAutoDefault(False)
        self.btn_save_config.clicked.connect(self.save_new_config)
        buttons_layout.addWidget(self.btn_save_config)
        layout.addRow(buttons_layout)

        self.update_config_field_visibility() # Inicializar visibilidad
        self.new_tab.setLayout(layout)

    def create_and_initialize_prefix(self):
        """Crea el directorio del prefijo si no existe y ejecuta wineboot."""
        config_name = self.config_name.text().strip()
        if not config_name:
            QMessageBox.warning(self, "Error", "Debes especificar un nombre para la configuración antes de crear/inicializar el prefijo.")
            return

        current_config_data = {
            "type": "wine" if self.config_type.currentText() == "Wine" else "proton",
            "arch": self.architecture_combo.currentText()
        }

        if current_config_data["type"] == "proton":
            proton_dir = self.proton_directory.text().strip()
            if not proton_dir or not Path(proton_dir).is_dir():
                QMessageBox.warning(self, "Error", "Debes especificar un directorio de Proton válido.")
                return
            current_config_data["proton_dir"] = proton_dir
            if self.radio_proton_steam_prefix.isChecked():
                appid = self.appid_line_edit.text().strip()
                if not appid.isdigit() or not appid:
                    QMessageBox.warning(self, "Error", "Para un prefijo de Steam, debes ingresar un APPID numérico válido.")
                    return
                steam_compat_data_root = Path.home() / ".local/share/Steam/steamapps/compatdata"
                current_config_data["prefix"] = str(steam_compat_data_root / appid / "pfx")
                current_config_data["steam_appid"] = appid
            else:
                prefix = self.prefix_path.text().strip()
                if not prefix:
                    QMessageBox.warning(self, "Error", "Debes especificar un prefijo para Proton personalizado.")
                    return
                current_config_data["prefix"] = prefix
        else: # Tipo Wine
            prefix = self.prefix_path.text().strip()
            if not prefix:
                QMessageBox.warning(self, "Error", "Debes especificar un prefijo para Wine.")
                return
            current_config_data["prefix"] = prefix
            wine_dir = self.wine_directory.text().strip()
            if wine_dir and Path(wine_dir).is_dir():
                current_config_data["wine_dir"] = wine_dir
            elif wine_dir: # Si no está vacío pero no es un directorio válido
                QMessageBox.warning(self, "Error", "El directorio de instalación de Wine especificado no es válido.")
                return

        prefix_path = Path(current_config_data["prefix"])

        # Preguntar si el prefijo ya existe
        if prefix_path.exists():
            reply = QMessageBox.question(self, "Prefijo Existente",
                                         f"El prefijo '{prefix_path}' ya existe. ¿Deseas reinicializarlo con wineboot?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # Temporalmente añadir la configuración para obtener el entorno con ConfigManager
        original_configs = self.config_manager.configs.copy()
        temp_configs_dict = {k: v.copy() if isinstance(v, dict) else v for k, v in original_configs.get("configs", {}).items()}
        temp_configs_dict[config_name] = current_config_data
        self.config_manager.configs["configs"] = temp_configs_dict
        self.config_manager.configs["last_used"] = config_name # Para que get_current_environment funcione correctamente

        progress_dialog = QProgressDialog("Inicializando Prefijo de Wine/Proton...", "", 0, 0, self)
        progress_dialog.setWindowTitle("Inicialización del Prefijo")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None) # No permitir cancelar wineboot fácilmente
        progress_dialog.setFixedSize(450, 150)
        self.config_manager.apply_breeze_style_to_widget(progress_dialog)
        progress_dialog.show()

        try:
            prefix_path.mkdir(parents=True, exist_ok=True, mode=0o755) # Crear el directorio si no existe
            env = self.config_manager.get_current_environment(config_name)

            wine_executable = env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")

            process = subprocess.Popen(
                [wine_executable, "wineboot"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            log_output = ""
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                log_output += line
                progress_dialog.setLabelText(f"Inicializando Prefijo de Wine/Proton...\n{line.strip()}")
                QApplication.processEvents() # Mantener la UI responsiva

            process.wait(timeout=120) # Esperar a que wineboot termine

            self.config_manager.write_to_log("Creación del Prefijo", f"Salida de Wineboot para {config_name}:\n{log_output}")

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "wineboot", output=log_output)

            QMessageBox.information(self, "Prefijo Creado/Inicializado", "El prefijo ha sido creado/inicializado exitosamente.")
        except subprocess.TimeoutExpired:
            process.kill()
            QMessageBox.critical(self, "Error al Crear/Inicializar Prefijo", "La inicialización del prefijo de Wine/Proton agotó el tiempo de espera.")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error al Crear/Inicializar Prefijo", f"No se pudo inicializar el prefijo de Wine/Proton. Código de salida: {e.returncode}\nSalida: {e.output}")
        except Exception as e:
            QMessageBox.critical(self, "Error al Crear/Inicializar Prefijo", f"Error: {str(e)}")
        finally:
            progress_dialog.close()
            # Restaurar la configuración original (si no se guardó permanentemente)
            self.config_manager.configs = original_configs
            self.config_manager.save_configs() # Asegurarse de que el estado guardado sea consistente

    def update_proton_prefix_options(self):
        """Controla la visibilidad de los campos de prefijo según el tipo de Proton."""
        if self.radio_proton_steam_prefix.isChecked():
            self.appid_line_edit.show()
            self.prefix_path.setEnabled(False)
            self.btn_prefix.setEnabled(False)
            self.prefix_path.setPlaceholderText("Se generará automáticamente con el APPID")
        else:
            self.appid_line_edit.hide()
            self.prefix_path.setEnabled(True)
            self.btn_prefix.setEnabled(True)
            self.prefix_path.setPlaceholderText("")

    def update_config_field_visibility(self):
        """Actualiza la visibilidad de los campos de configuración Wine/Proton."""
        is_proton = self.config_type.currentText() == "Proton"
        self.proton_group.setVisible(is_proton)
        self.wine_group.setVisible(not is_proton)
        self.proton_prefix_type_group.setVisible(is_proton)

        # Lógica adicional para deshabilitar campos si es prefijo Steam
        if is_proton and self.radio_proton_steam_prefix.isChecked():
            self.prefix_path.setEnabled(False)
            self.btn_prefix.setEnabled(False)
        else:
            self.prefix_path.setEnabled(True)
            self.btn_prefix.setEnabled(True)

    def setup_downloads_tab(self):
        # [CORRECCIÓN] Crear un layout para downloads_tab
        downloads_tab_layout = QVBoxLayout(self.downloads_tab) # Asignar a downloads_tab

        self.download_tabs = QTabWidget() # Es importante que este sea un miembro del diálogo si se accede desde otros métodos

        # Configuración de la pestaña Proton
        proton_inner_layout = QVBoxLayout(self.proton_tab) # Nuevo layout para el contenido de proton_tab
        self.group_proton_repos = QGroupBox("Repositorios de Proton")
        repo_layout = QVBoxLayout()
        self.list_repos_proton = QListWidget()
        self.list_repos_proton.setSelectionMode(QListWidget.SingleSelection)
        self.load_proton_repositories()
        repo_layout.addWidget(self.list_repos_proton)
        repo_btn_layout = QHBoxLayout()
        self.btn_add_proton_repo = QPushButton("Añadir")
        self.btn_add_proton_repo.setAutoDefault(False)
        self.btn_add_proton_repo.clicked.connect(self.add_proton_repository)
        repo_btn_layout.addWidget(self.btn_add_proton_repo)
        self.btn_delete_proton_repo = QPushButton("Eliminar")
        self.btn_delete_proton_repo.setAutoDefault(False)
        self.btn_delete_proton_repo.clicked.connect(self.delete_proton_repository)
        repo_btn_layout.addWidget(self.btn_delete_proton_repo)
        self.btn_toggle_proton_repo = QPushButton("Habilitar/Deshabilitar")
        self.btn_toggle_proton_repo.setAutoDefault(False)
        self.btn_toggle_proton_repo.clicked.connect(self.toggle_proton_repository)
        repo_btn_layout.addWidget(self.btn_toggle_proton_repo)
        repo_layout.addLayout(repo_btn_layout)
        self.group_proton_repos.setLayout(repo_layout)
        proton_inner_layout.addWidget(self.group_proton_repos) # Añadir al layout interno de proton_tab

        self.group_proton_versions = QGroupBox("Versiones de Proton Disponibles")
        versions_layout = QVBoxLayout()
        self.list_versions_proton = QListWidget()
        versions_layout.addWidget(self.list_versions_proton)
        buttons_layout = QHBoxLayout()
        self.btn_update_proton = QPushButton("Actualizar Lista")
        self.btn_update_proton.setAutoDefault(False)
        self.btn_update_proton.clicked.connect(self.update_proton_versions)
        buttons_layout.addWidget(self.btn_update_proton)
        self.btn_download_proton = QPushButton("Descargar Seleccionado")
        self.btn_download_proton.setAutoDefault(False)
        self.btn_download_proton.clicked.connect(self.download_selected_proton_version)
        buttons_layout.addWidget(self.btn_download_proton)
        versions_layout.addLayout(buttons_layout)
        self.group_proton_versions.setLayout(versions_layout)
        proton_inner_layout.addWidget(self.group_proton_versions) # Añadir al layout interno de proton_tab

        # Configuración de la pestaña Wine
        wine_inner_layout = QVBoxLayout(self.wine_tab) # Nuevo layout para el contenido de wine_tab
        self.group_wine_repos = QGroupBox("Repositorios de Wine")
        wine_repo_layout = QVBoxLayout()
        self.list_repos_wine = QListWidget()
        self.list_repos_wine.setSelectionMode(QListWidget.SingleSelection)
        self.load_wine_repositories()
        wine_repo_layout.addWidget(self.list_repos_wine)
        wine_repo_btn_layout = QHBoxLayout()
        self.btn_add_wine_repo = QPushButton("Añadir")
        self.btn_add_wine_repo.setAutoDefault(False)
        self.btn_add_wine_repo.clicked.connect(self.add_wine_repository)
        wine_repo_btn_layout.addWidget(self.btn_add_wine_repo)
        self.btn_delete_wine_repo = QPushButton("Eliminar")
        self.btn_delete_wine_repo.setAutoDefault(False)
        self.btn_delete_wine_repo.clicked.connect(self.delete_wine_repository)
        wine_repo_btn_layout.addWidget(self.btn_delete_wine_repo)
        self.btn_toggle_wine_repo = QPushButton("Habilitar/Deshabilitar")
        self.btn_toggle_wine_repo.setAutoDefault(False)
        self.btn_toggle_wine_repo.clicked.connect(self.toggle_wine_repository)
        wine_repo_btn_layout.addWidget(self.btn_toggle_wine_repo)
        wine_repo_layout.addLayout(wine_repo_btn_layout)
        self.group_wine_repos.setLayout(wine_repo_layout)
        wine_inner_layout.addWidget(self.group_wine_repos) # Añadir al layout interno de wine_tab

        self.group_wine_versions = QGroupBox("Versiones de Wine Disponibles")
        wine_versions_layout = QVBoxLayout()
        self.list_versions_wine = QListWidget()
        wine_versions_layout.addWidget(self.list_versions_wine)
        wine_buttons_layout = QHBoxLayout()
        self.btn_update_wine = QPushButton("Actualizar Lista")
        self.btn_update_wine.setAutoDefault(False)
        self.btn_update_wine.clicked.connect(self.update_wine_versions)
        wine_buttons_layout.addWidget(self.btn_update_wine)
        self.btn_download_wine = QPushButton("Descargar Seleccionado")
        self.btn_download_wine.setAutoDefault(False)
        self.btn_download_wine.clicked.connect(self.download_selected_wine_version)
        wine_buttons_layout.addWidget(self.btn_download_wine)
        wine_versions_layout.addLayout(wine_buttons_layout)
        self.group_wine_versions.setLayout(wine_versions_layout)
        wine_inner_layout.addWidget(self.group_wine_versions) # Añadir al layout interno de wine_tab
        # self.wine_tab.setLayout(wine_inner_layout) # Ya se asignó en el constructor del layout

        # [CORRECCIÓN] Añadir los tabs al QTabWidget principal de descargas
        self.download_tabs.addTab(self.proton_tab, "Proton")
        self.download_tabs.addTab(self.wine_tab, "Wine")

        downloads_tab_layout.addWidget(self.download_tabs) # Añadir el QTabWidget al layout de downloads_tab

    def download_selected_proton_version(self):
        """Inicia la descarga de la versión de Proton seleccionada."""
        selected_item = self.list_versions_proton.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección Inválida", "Por favor, selecciona una versión de Proton para descargar.")
            return

        assets = selected_item.data(Qt.UserRole)

        # Diálogo para seleccionar el archivo específico (si hay varios)
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Archivo Proton")
        layout = QVBoxLayout()

        label = QLabel("Selecciona el archivo específico para descargar:")
        layout.addWidget(label)

        version_combo = QComboBox()
        for asset in assets:
            name = asset["name"]
            size = asset.get("size", 0) / (1024 * 1024) # Mostrar tamaño en MB
            version_combo.addItem(f"{name} ({size:.1f} MB)", asset)
        layout.addWidget(version_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        self.config_manager.apply_breeze_style_to_widget(dialog) # Aplicar estilo al diálogo

        if dialog.exec_() == QDialog.Accepted:
            selected_asset = version_combo.currentData()
            download_url = selected_asset["browser_download_url"]
            filename = selected_asset["name"]
            destination = self.config_manager.proton_download_dir / filename

            self.download_file(download_url, destination, f"Proton {selected_item.text()}")

    def setup_wine_download_tab(self):
        layout = QVBoxLayout()
        self.group_wine_repos = QGroupBox("Repositorios de Wine")
        repo_layout = QVBoxLayout()

        self.list_repos_wine = QListWidget()
        self.list_repos_wine.setSelectionMode(QListWidget.SingleSelection)
        self.load_wine_repositories()
        repo_layout.addWidget(self.list_repos_wine)

        repo_btn_layout = QHBoxLayout()
        self.btn_add_wine_repo = QPushButton("Añadir")
        self.btn_add_wine_repo.setAutoDefault(False)
        self.btn_add_wine_repo.clicked.connect(self.add_wine_repository)
        repo_btn_layout.addWidget(self.btn_add_wine_repo)

        self.btn_delete_wine_repo = QPushButton("Eliminar")
        self.btn_delete_wine_repo.setAutoDefault(False)
        self.btn_delete_wine_repo.clicked.connect(self.delete_wine_repository)
        repo_btn_layout.addWidget(self.btn_delete_wine_repo)

        self.btn_toggle_wine_repo = QPushButton("Habilitar/Deshabilitar")
        self.btn_toggle_wine_repo.setAutoDefault(False)
        self.btn_toggle_wine_repo.clicked.connect(self.toggle_wine_repository)
        repo_btn_layout.addWidget(self.btn_toggle_wine_repo)

        repo_layout.addLayout(repo_btn_layout)
        self.group_wine_repos.setLayout(repo_layout)
        layout.addWidget(self.group_wine_repos)

        self.group_wine_versions = QGroupBox("Versiones de Wine Disponibles")
        versions_layout = QVBoxLayout()

        self.list_versions_wine = QListWidget()
        versions_layout.addWidget(self.list_versions_wine)

        buttons_layout = QHBoxLayout()
        self.btn_update_wine = QPushButton("Actualizar Lista")
        self.btn_update_wine.setAutoDefault(False)
        self.btn_update_wine.clicked.connect(self.update_wine_versions)
        buttons_layout.addWidget(self.btn_update_wine)

        self.btn_download_wine = QPushButton("Descargar Seleccionado")
        self.btn_download_wine.setAutoDefault(False)
        self.btn_download_wine.clicked.connect(self.download_selected_wine_version)
        buttons_layout.addWidget(self.btn_download_wine)
        versions_layout.addLayout(buttons_layout)

        self.group_wine_versions.setLayout(versions_layout)
        layout.addWidget(self.group_wine_versions)

        self.wine_tab.setLayout(layout)

    def load_proton_repositories(self):
        """Carga y muestra los repositorios de Proton."""
        self.list_repos_proton.clear()
        repos = self.config_manager.get_repositories("proton")

        base_font = STYLE_BREEZE["font"]
        list_font_size = base_font.pointSize() + 2
        font_for_item = QFont(base_font.family(), list_font_size)
        font_for_item.setBold(True)

        for repo in repos:
            item = QListWidgetItem(repo["name"])
            item.setData(Qt.UserRole, repo["url"])
            item.setCheckState(Qt.Checked if repo.get("enabled", True) else Qt.Unchecked)
            item.setFont(font_for_item)
            self.list_repos_proton.addItem(item)

    def load_wine_repositories(self):
        """Carga y muestra los repositorios de Wine."""
        self.list_repos_wine.clear()
        repos = self.config_manager.get_repositories("wine")

        base_font = STYLE_BREEZE["font"]
        list_font_size = base_font.pointSize() + 2
        font_for_item = QFont(base_font.family(), list_font_size)
        font_for_item.setBold(True)

        for repo in repos:
            item = QListWidgetItem(repo["name"])
            item.setData(Qt.UserRole, repo["url"])
            item.setCheckState(Qt.Checked if repo.get("enabled", True) else Qt.Unchecked)
            item.setFont(font_for_item)
            self.list_repos_wine.addItem(item)

    def add_repository_dialog(self, repo_type: str):
        """Abre el diálogo para añadir un nuevo repositorio."""
        dialog = RepositoryDialog(repo_type, self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                name, url = dialog.get_repository_info()
                if self.config_manager.add_repository(repo_type, name, url):
                    if repo_type == "proton":
                        self.load_proton_repositories()
                    else:
                        self.load_wine_repositories()
                    QMessageBox.information(self, "Repositorio Añadido", f"Repositorio '{name}' añadido exitosamente.")
                else:
                    QMessageBox.warning(self, "Duplicado", f"El repositorio '{name}' ya existe.")
            except ValueError as e:
                QMessageBox.warning(self, "Entrada Inválida", str(e))

    def add_proton_repository(self):
        self.add_repository_dialog("proton")

    def add_wine_repository(self):
        self.add_repository_dialog("wine")

    def delete_repository_dialog(self, repo_type: str):
        """Elimina un repositorio seleccionado."""
        list_widget = self.list_repos_proton if repo_type == "proton" else self.list_repos_wine
        selected_row = list_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona un repositorio para eliminar.")
            return

        repo_name = list_widget.item(selected_row).text()
        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Estás seguro de que quieres eliminar el repositorio '{repo_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.config_manager.delete_repository(repo_type, selected_row):
                if repo_type == "proton":
                    self.load_proton_repositories()
                else:
                    self.load_wine_repositories()
                QMessageBox.information(self, "Eliminado", f"Repositorio '{repo_name}' eliminado.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el repositorio.")

    def delete_proton_repository(self):
        self.delete_repository_dialog("proton")

    def delete_wine_repository(self):
        self.delete_repository_dialog("wine")

    def toggle_repository_state(self, repo_type: str):
        """Habilita o deshabilita un repositorio seleccionado."""
        list_widget = self.list_repos_proton if repo_type == "proton" else self.list_repos_wine
        selected_row = list_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona un repositorio para habilitar/deshabilitar.")
            return

        item = list_widget.item(selected_row)
        current_state = item.checkState() == Qt.Checked
        if self.config_manager.toggle_repository(repo_type, selected_row, not current_state):
            item.setCheckState(Qt.Unchecked if current_state else Qt.Checked)

    def toggle_proton_repository(self):
        self.toggle_repository_state("proton")

    def toggle_wine_repository(self):
        self.toggle_repository_state("wine")

    def update_versions(self, repo_type: str):
        """Actualiza la lista de versiones disponibles desde los repositorios."""
        list_widget = self.list_versions_proton if repo_type == "proton" else self.list_versions_wine
        list_widget.clear()
        enabled_repos = [repo for repo in self.config_manager.get_repositories(repo_type) if repo.get("enabled", True)]

        if not enabled_repos:
            QMessageBox.information(self, "No hay Repositorios", f"No hay repositorios de {repo_type.capitalize()} activos. Por favor, añade o habilita uno.")
            return

        self.progress_dialog = QProgressDialog(f"Buscando versiones de {repo_type.capitalize()}...", "Cancelar", 0, len(enabled_repos), self)
        self.progress_dialog.setWindowTitle("Actualizando Versiones")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setCancelButton(None) # No permitir cancelar la búsqueda de versiones
        self.config_manager.apply_breeze_style_to_widget(self.progress_dialog)

        self.version_search_thread = VersionSearchThread(repo_type, enabled_repos)
        self.version_search_thread.progress.connect(self.progress_dialog.setValue)
        self.version_search_thread.new_release.connect(self._add_release_to_list)
        self.version_search_thread.finished.connect(self.progress_dialog.close)
        self.version_search_thread.error.connect(lambda msg: QMessageBox.warning(self, "Error Obteniendo Versiones", msg))

        self.version_search_thread.start()
        self.progress_dialog.exec_() # Mostrar el diálogo de progreso de forma modal

    def update_proton_versions(self):
        self.update_versions("proton")

    def update_wine_versions(self):
        self.update_versions("wine")

    def _add_release_to_list(self, repo_type: str, release_name: str, version: str, assets: object, published_at: str):
        """Añade un lanzamiento a la lista correspondiente (Wine o Proton)."""
        list_widget = self.list_versions_proton if repo_type == "proton" else self.list_versions_wine
        item = QListWidgetItem(release_name)
        item.setData(Qt.UserRole, assets) # Almacena los assets para usarlos al descargar

        tooltip = f"<b>Versión:</b> {version}<br/>" \
                  f"<b>Fecha:</b> {published_at.split('T')[0] if published_at else 'N/A'}<br/>" \
                  f"<b>Archivos:</b> {len(assets)}"
        item.setToolTip(tooltip)

        base_font = STYLE_BREEZE["font"]
        list_font_size = base_font.pointSize() + 2
        font_for_item = QFont(base_font.family(), list_font_size)
        font_for_item.setBold(True)
        item.setFont(font_for_item)

        list_widget.addItem(item)

    def download_selected_wine_version(self):
        """Inicia la descarga de la versión de Wine seleccionada."""
        selected_item = self.list_versions_wine.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección Inválida", "Por favor, selecciona una versión de Wine para descargar.")
            return

        assets = selected_item.data(Qt.UserRole)

        # Diálogo para seleccionar el archivo específico (si hay varios)
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Archivo Wine")
        layout = QVBoxLayout()

        label = QLabel("Selecciona el archivo específico para descargar:")
        layout.addWidget(label)

        version_combo = QComboBox()
        for asset in assets:
            name = asset["name"]
            size = asset.get("size", 0) / (1024 * 1024)
            version_combo.addItem(f"{name} ({size:.1f} MB)", asset)
        layout.addWidget(version_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        self.config_manager.apply_breeze_style_to_widget(dialog)

        if dialog.exec_() == QDialog.Accepted:
            selected_asset = version_combo.currentData()
            download_url = selected_asset["browser_download_url"]
            filename = selected_asset["name"]
            destination = self.config_manager.wine_download_dir / filename

            self.download_file(download_url, destination, f"Wine {selected_item.text()}")

    def download_file(self, url: str, destination: Path, name: str):
        """Inicia el proceso de descarga de un archivo."""
        self.progress_dialog = QProgressDialog(f"Descargando {name}...", "Cancelar", 0, 100, self)
        self.progress_dialog.setWindowTitle("Descargando")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(False) # No cerrar automáticamente hasta que se maneje la descompresión/error
        self.config_manager.apply_breeze_style_to_widget(self.progress_dialog)

        self.download_progress_bar = QProgressBar(self.progress_dialog)
        self.download_progress_bar.setRange(0, 100)
        self.progress_dialog.setBar(self.download_progress_bar)

        self.download_thread = DownloadThread(url, destination, name, self.config_manager)
        self.download_thread.progress.connect(self.download_progress_bar.setValue)
        self.download_thread.finished.connect(partial(self.on_download_finished, name=name))
        self.download_thread.error.connect(self.show_download_error)
        self.progress_dialog.canceled.connect(self.download_thread.stop) # Conectar botón de cancelar a stop del hilo

        self.download_thread.start()
        self.progress_dialog.exec_() # Mostrar el diálogo de progreso de forma modal

    def show_download_error(self, error_msg: str):
        """Muestra un mensaje de error de descarga."""
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error de Descarga", error_msg)

    def on_download_finished(self, filepath: str, name: str):
        """Maneja la finalización de una descarga, iniciando la descompresión."""
        self.progress_dialog.setLabelText(f"Descomprimiendo {name}...")
        self.progress_dialog.setMaximum(0) # Indeterminado para descompresión
        self.config_manager.apply_breeze_style_to_widget(self.progress_dialog)

        self.decompression_thread = DecompressionThread(filepath, self.config_manager, name)
        self.decompression_thread.finished.connect(partial(self.on_decompression_finished, name=name))
        self.decompression_thread.error.connect(self.show_decompression_error)
        self.decompression_thread.start()

    def show_decompression_error(self, error_msg: str):
        """Muestra un mensaje de error de descompresión."""
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error de Descompresión", error_msg)

    def on_decompression_finished(self, path: str, name: str):
        """Maneja la finalización de la descompresión."""
        self.progress_dialog.close()
        QMessageBox.information(self, "Éxito", f"Descarga y descompresión de {name} completadas.\nInstalado en: {path}")

    def save_new_config(self):
        """Guarda una nueva configuración o actualiza una existente."""
        try:
            new_config_name = self.config_name.text().strip()
            if not new_config_name:
                QMessageBox.warning(self, "Error", "Debes especificar un nombre para la configuración.")
                return

            original_config_name = self.current_config_name_for_editing

            if new_config_name != original_config_name and new_config_name in self.config_manager.configs.get("configs", {}):
                QMessageBox.warning(self, "Nombre Duplicado", f"Ya existe una configuración con el nombre '{new_config_name}'. Por favor, elige otro nombre.")
                return

            config_type = "wine" if self.config_type.currentText() == "Wine" else "proton"
            architecture = self.architecture_combo.currentText()
            prefix = self.prefix_path.text().strip()

            config_data = {
                "type": config_type,
                "arch": architecture
            }

            if config_type == "proton":
                proton_directory = self.proton_directory.text().strip()
                if not proton_directory or not Path(proton_directory).is_dir():
                    QMessageBox.warning(self, "Error", "Debes especificar un directorio de Proton válido.")
                    return
                config_data["proton_dir"] = proton_directory

                if self.radio_proton_steam_prefix.isChecked():
                    appid = self.appid_line_edit.text().strip()
                    if not appid.isdigit() or not appid:
                        QMessageBox.warning(self, "Error", "Para un prefijo de Steam, debes ingresar un APPID numérico válido.")
                        return
                    steam_compat_data_root = Path.home() / ".local/share/Steam/steamapps/compatdata"
                    config_data["prefix"] = str(steam_compat_data_root / appid / "pfx")
                    config_data["steam_appid"] = appid
                else:
                    if not prefix:
                        QMessageBox.warning(self, "Error", "Debes especificar un prefijo para Proton personalizado.")
                        return
                    config_data["prefix"] = prefix
            else: # Tipo Wine
                if not prefix:
                    QMessageBox.warning(self, "Error", "Debes especificar un prefijo para Wine.")
                    return
                config_data["prefix"] = prefix
                wine_directory = self.wine_directory.text().strip()
                if wine_directory:
                    if not Path(wine_directory).is_dir():
                        QMessageBox.warning(self, "Error", "El directorio de instalación de Wine especificado no es válido.")
                        return
                    config_data["wine_dir"] = wine_directory

            # Guardar o actualizar la configuración
            self.config_manager.configs.setdefault("configs", {})[new_config_name] = config_data
            self.config_manager.save_configs()
            QMessageBox.information(self, "Guardado", f"Configuración '{new_config_name}' guardada exitosamente.")

            self.load_configs() # Recargar la lista de configs en la primera pestaña
            self.tabs.setCurrentIndex(0) # Volver a la pestaña de "Configuraciones Guardadas"
            self.current_config_name_for_editing = None # Limpiar el estado de edición

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando configuración: {str(e)}")

    def setup_settings_tab(self):
        main_layout = QVBoxLayout()
        # El tema se aplica inmediatamente, el resto de ajustes pide reiniciar

        paths_group = QGroupBox("Rutas")
        paths_layout = QFormLayout()

        self.edit_winetricks_path = QLineEdit(self.config_manager.get_winetricks_path())
        self.btn_winetricks = QPushButton("Explorar...")
        self.btn_winetricks.setAutoDefault(False)
        self.btn_winetricks.clicked.connect(self.browse_winetricks)

        winetricks_layout = QHBoxLayout()
        winetricks_layout.addWidget(self.edit_winetricks_path)
        winetricks_layout.addWidget(self.btn_winetricks)
        paths_layout.addRow("Ruta de Winetricks:", winetricks_layout)

        paths_group.setLayout(paths_layout)
        main_layout.addWidget(paths_group)

        install_options_group = QGroupBox("Tema y Opciones de Instalación")
        install_options_layout = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro"])
        current_theme = self.config_manager.get_theme()
        self.theme_combo.setCurrentText("Oscuro" if current_theme == "dark" else "Claro")

        install_options_layout.addRow("Tema de Interfaz:", self.theme_combo)

        silent_layout = QHBoxLayout()
        silent_label = QLabel("Habilitar modo silencioso por defecto (-q)")
        self.checkbox_silent_global = QCheckBox()
        self.checkbox_silent_global.setChecked(self.config_manager.get_silent_install())
        silent_layout.addWidget(silent_label)
        silent_layout.addStretch()
        silent_layout.addWidget(self.checkbox_silent_global)
        install_options_layout.addRow(silent_layout)

        force_winetricks_layout = QHBoxLayout()
        force_winetricks_label = QLabel("Forzar instalación de Winetricks (--force)")
        self.checkbox_force_winetricks = QCheckBox()
        self.checkbox_force_winetricks.setChecked(self.config_manager.get_force_winetricks_install())
        force_winetricks_layout.addWidget(force_winetricks_label)
        force_winetricks_layout.addStretch()
        force_winetricks_layout.addWidget(self.checkbox_force_winetricks)
        install_options_layout.addRow(force_winetricks_layout)

        install_options_group.setLayout(install_options_layout)
        main_layout.addWidget(install_options_group)

        backup_options_group = QGroupBox("Opciones de Backup") # Todavía usamos el grupo para la última opción
        backup_options_layout = QFormLayout()

        ask_for_backup_layout = QHBoxLayout()
        ask_for_backup_label = QLabel("Preguntar por backup antes de iniciar una herramienta/instalación")
        self.checkbox_ask_for_backup_before_action = QCheckBox()
        self.checkbox_ask_for_backup_before_action.setToolTip("Si está activado, se le preguntará si desea hacer un backup antes de ciertas operaciones que puedan modificar el prefijo.")
        self.checkbox_ask_for_backup_before_action.setChecked(self.config_manager.get_ask_for_backup_before_action())
        ask_for_backup_layout.addWidget(ask_for_backup_label)
        ask_for_backup_layout.addStretch()
        ask_for_backup_layout.addWidget(self.checkbox_ask_for_backup_before_action)
        backup_options_layout.addRow(ask_for_backup_layout)

        backup_options_group.setLayout(backup_options_layout)
        main_layout.addWidget(backup_options_group)

        main_layout.addStretch()

        self.btn_save_settings = QPushButton("Guardar Ajustes")
        self.btn_save_settings.setAutoDefault(False)
        self.btn_save_settings.clicked.connect(self.save_settings)
        stretch_button_layout = QHBoxLayout()
        stretch_button_layout.addWidget(self.btn_save_settings)
        main_layout.addLayout(stretch_button_layout)

        self.settings_tab.setLayout(main_layout)

    # MODIFICACIÓN 1: Método para actualizar el estado del botón "Guardar Ajustes"
    def update_save_settings_button_state(self):
        """Habilita/deshabilita el botón 'Guardar Ajustes' basándose en si hay una instalación en curso."""
        # Se asume que config_manager.app_instance es una referencia válida a InstallerApp
        if hasattr(self.config_manager, 'app_instance') and self.config_manager.app_instance:
            is_installer_running = self.config_manager.app_instance.installer_thread is not None and self.config_manager.app_instance.installer_thread.isRunning()
            is_backup_running = self.config_manager.app_instance.backup_thread is not None and self.config_manager.app_instance.backup_thread.isRunning()
            self.btn_save_settings.setEnabled(not is_installer_running and not is_backup_running)
        else:
            self.btn_save_settings.setEnabled(True) # Por defecto habilitado si no hay app_instance

    def _apply_theme_setting(self, text: str):
        """[MODIFICACIÓN 3] Este método ya no se llama directamente por currentTextChanged.
        Ahora solo actualiza la configuración en memoria. El cambio real se aplica al reiniciar la app."""
        theme_name = "dark" if text == "Oscuro" else "light"
        self.config_manager.set_theme(theme_name)

    def save_settings(self):
        """Guarda los ajustes generales de la aplicación."""
        try:
            winetricks_path_ok = self.config_manager.set_winetricks_path(self.edit_winetricks_path.text().strip())

            theme = "dark" if self.theme_combo.currentText() == "Oscuro" else "light"
            self.config_manager.set_theme(theme) # Actualiza self.configs["settings"]["theme"]
            self.config_manager.save_configs() # Guarda la configuración actualizada en el archivo

            self.config_manager.set_silent_install(self.checkbox_silent_global.isChecked())
            self.config_manager.set_force_winetricks_install(self.checkbox_force_winetricks.isChecked())
            self.config_manager.set_ask_for_backup_before_action(self.checkbox_ask_for_backup_before_action.isChecked())

            QMessageBox.information(self, "Guardado", "Ajustes guardados exitosamente.\nLa aplicación se reiniciará para aplicar los cambios.")
            self.config_saved.emit() # Notificar a la ventana principal para que inicie el reinicio
            self.accept() # Cerrar el diálogo de configuración
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando ajustes: {str(e)}")

    def browse_winetricks(self):
        """Abre un diálogo para seleccionar la ruta de Winetricks."""
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Ejecutables (*);;Todos los Archivos (*)")
        # MODIFICACIÓN 4: Usar la última ruta explorada para Winetricks
        dialog.setDirectory(self.config_manager.get_last_browsed_dir("winetricks"))
        dialog.setFilter(QDir.AllEntries | QDir.AllDirs | QDir.NoDotAndDotDot) # Permitir directorios también

        self.config_manager.apply_breeze_style_to_widget(dialog) # Aplicar estilo al diálogo de archivo

        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                self.edit_winetricks_path.setText(selected[0])
                # MODIFICACIÓN 4: Guardar la nueva ruta explorada
                self.config_manager.set_last_browsed_dir("winetricks", str(Path(selected[0]).parent))


    def load_configs(self):
        """Carga y muestra las configuraciones guardadas."""
        self.list_config.clear()
        configs = self.config_manager.configs.get("configs", {})
        last_used = self.config_manager.configs.get("last_used", "")

        # Ordenar alfabéticamente, pero con 'last_used' primero
        sorted_config_names = sorted(configs.keys())
        if last_used and last_used in sorted_config_names:
            sorted_config_names.remove(last_used)
            sorted_config_names.insert(0, last_used)

        # Aplicar fuente negrita a los ítems de la lista
        base_font = STYLE_BREEZE["font"]
        # MODIFICACIÓN 3: Reducir tamaño de fuente en 2 puntos
        list_font_size = base_font.pointSize() + 1
        font_for_item = QFont(base_font.family(), list_font_size)
        font_for_item.setBold(True)

        for name in sorted_config_names:
            item = QListWidgetItem(name)
            if name == last_used:
                item.setText(f"{name} (Por Defecto)")
            item.setFont(font_for_item) # Aplicar la fuente
            self.list_config.addItem(item)
            if name == last_used:
                self.list_config.setCurrentItem(item) # Seleccionar el por defecto

        self.update_displayed_config_info() # Actualizar info al cargar

    def edit_config(self, item: QListWidgetItem):
        """Carga una configuración seleccionada para edición."""
        config_name_display = item.text()
        config_name = config_name_display.replace(" (Por Defecto)", "").strip()
        self.current_config_name_for_editing = config_name # Guardar el nombre original para la edición

        config = self.config_manager.get_config(config_name)
        if not config:
            QMessageBox.warning(self, "Error", "Configuración no encontrada o corrupta.")
            return

        self.tabs.setCurrentIndex(1) # Ir a la pestaña de edición
        self.config_name.setText(config_name)

        self.config_type.setCurrentText("Proton" if config.get("type") == "proton" else "Wine")
        self.prefix_path.setText(config.get("prefix", ""))
        self.architecture_combo.setCurrentText(config.get("arch", "win64"))

        if config.get("type") == "proton":
            self.proton_directory.setText(config.get("proton_dir", ""))
            self.wine_directory.setText("") # Limpiar campo no relevante
            if "steam_appid" in config:
                self.radio_proton_steam_prefix.setChecked(True)
                self.appid_line_edit.setText(config["steam_appid"])
            else:
                self.radio_proton_custom_prefix.setChecked(True)
                self.appid_line_edit.setText("")
        else: # Tipo Wine
            self.wine_directory.setText(config.get("wine_dir", ""))
            self.proton_directory.setText("") # Limpiar campo no relevante
            self.radio_proton_custom_prefix.setChecked(True) # Asegurarse de que esté en modo "custom" para Wine
            self.appid_line_edit.setText("")

        self.update_config_field_visibility() # Actualizar visibilidad de campos

    def delete_config(self):
        """Elimina una configuración seleccionada."""
        selected = self.list_config.currentItem()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Selecciona una configuración para eliminar.")
            return

        config_name_display = selected.text()
        config_name = config_name_display.replace(" (Por Defecto)", "").strip()

        if config_name == "Wine-System":
            QMessageBox.warning(self, "Error", "No se puede eliminar la configuración 'Wine-System' ya que es la predeterminada del sistema.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar la configuración '{config_name}'? Esto no eliminará el prefijo o los archivos de Wine/Proton asociados.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.config_manager.delete_config(config_name):
                self.load_configs()
                QMessageBox.information(self, "Éxito", f"Configuración '{config_name}' eliminada.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la configuración.")

    def set_default_config(self):
        """Establece una configuración seleccionada como predeterminada."""
        selected = self.list_config.currentItem()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Selecciona una configuración para establecer como predeterminada.")
            return

        config_name = selected.text().replace(" (Por Defecto)", "").strip()
        self.config_manager.configs["last_used"] = config_name
        self.config_manager.save_configs()
        QMessageBox.information(self, "Éxito", f"Configuración '{config_name}' establecida como predeterminada.")
        self.load_configs() # Recargar para que se actualice el texto "(Por Defecto)"

    def update_displayed_config_info(self):
        """Actualiza la información de la configuración seleccionada en la GUI."""
        selected = self.list_config.currentItem()
        if not selected:
            self.lbl_config_info.setText("Selecciona una configuración para ver los detalles.")
            return

        config_name = selected.text().replace(" (Por Defecto)", "").strip()
        config = self.config_manager.get_config(config_name)
        if not config:
            self.lbl_config_info.setText("Configuración no encontrada o corrupta.")
            return

        try:
            env = self.config_manager.get_current_environment(config_name)
        except Exception as e:
            self.lbl_config_info.setText(f"Error cargando el entorno para '{config_name}': {e}")
            return

        version = env.get("PROTON_VERSION") if config.get("type") == "proton" else env.get("WINE_VERSION", "Desconocida")
        wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "N/A")

        info = [
            f"<b>Configuración Actual:</b> {config_name}",
            f"<b>Tipo:</b> {'Proton' if config['type'] == 'proton' else 'Wine'}",
            f"<b>Versión Detectada:</b> <span style='color: {COLOR_BREEZE_PRIMARY}; font-weight: bold;'>{version}</span>",
        ]

        if config['type'] == 'proton':
            info.extend([
                f"<b>Wine en Proton:</b> <span style='color: {COLOR_BREEZE_PRIMARY}; font-weight: bold;'>{wine_version_in_proton}</span>",
                f"<b>Directorio de Proton:</b> {config.get('proton_dir', 'No especificado')}"
            ])
            if "steam_appid" in config:
                info.append(f"<b>APPID de Steam:</b> {config['steam_appid']}")
                info.append(f"<b>Prefijo gestionado por Steam:</b> Sí")
            else:
                info.append(f"<b>Prefijo personalizado:</b> Sí")
        else: # Tipo Wine
            wine_dir = config.get('wine_dir', 'Sistema (PATH)')
            info.extend([
                f"<b>Directorio de Wine:</b> {wine_dir}"
            ])

        info.extend([
            f"<b>Arquitectura:</b> {config.get('arch', 'win64')}",
            f"<b>Prefijo:</b> <span style='color: #FFB347; font-weight: bold;'>{config.get('prefix', 'No especificado')}</span>"
        ])

        self.lbl_config_info.setText("<br>".join(info))

    def browse_prefix(self):
        """Abre un diálogo para seleccionar el directorio de prefijo."""
        key = "wine_prefix" if self.config_type.currentText() == "Wine" else "proton_prefix"
        path = self._get_directory_path("Seleccionar Directorio de Prefijo de Wine", key)
        if path:
            self.prefix_path.setText(path)

    def browse_wine(self):
        """Abre un diálogo para seleccionar el directorio de instalación de Wine."""
        path = self._get_directory_path("Seleccionar Directorio de Instalación de Wine (ej., bin/wine)", "wine_install")
        if path:
            self.wine_directory.setText(path)

    def browse_proton(self):
        """Abre un diálogo para seleccionar el directorio de instalación de Proton."""
        path = self._get_directory_path("Seleccionar Directorio de Instalación de Proton (ej., proton_dist/files)", "proton_install")
        if path:
            self.proton_directory.setText(path)

    def _get_directory_path(self, title="Seleccionar Directorio", config_key: str = "default") -> str | None: # MODIFICACIÓN 4
        """Helper para abrir un diálogo de selección de directorio.
           MODIFICACIÓN 4: Ahora usa config_key para gestionar la última ruta explorada."""
        dialog = QFileDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        # MODIFICACIÓN 4: Usar la última ruta guardada
        dialog.setDirectory(self.config_manager.get_last_browsed_dir(config_key))

        self.config_manager.apply_breeze_style_to_widget(dialog)

        if dialog.exec_() == QDialog.Accepted:
            selected_path = dialog.selectedFiles()[0]
            # MODIFICACIÓN 4: Guardar la nueva ruta explorada
            self.config_manager.set_last_browsed_dir(config_key, selected_path)
            return selected_path
        return None


    def test_configuration(self):
        """Prueba la configuración actual de Wine/Proton."""
        config_name_test = self.config_name.text().strip()
        if not config_name_test:
            QMessageBox.warning(self, "Advertencia", "Por favor, introduce un nombre para la configuración antes de probar.")
            return

        # Construir una configuración temporal basada en los campos actuales del formulario
        temp_config = {
            "type": "wine" if self.config_type.currentText() == "Wine" else "proton",
            "prefix": self.prefix_path.text().strip(),
            "arch": self.architecture_combo.currentText()
        }
        if temp_config["type"] == "proton":
            temp_config["proton_dir"] = self.proton_directory.text().strip()
            if self.radio_proton_steam_prefix.isChecked():
                appid = self.appid_line_edit.text().strip()
                if not appid.isdigit() or not appid:
                    QMessageBox.warning(self, "Error", "Para un prefijo de Steam, debes ingresar un APPID numérico válido.")
                    return
                steam_compat_data_root = Path.home() / ".local/share/Steam/steamapps/compatdata"
                temp_config["prefix"] = str(steam_compat_data_root / appid / "pfx")
                temp_config["steam_appid"] = appid
        elif self.wine_directory.text().strip(): # Si es Wine y hay un directorio especificado
            temp_config["wine_dir"] = self.wine_directory.text().strip()

        # Guardar una copia de las configuraciones actuales y modificar temporalmente
        original_configs = self.config_manager.configs.copy()
        temp_configs_dict = {k: v.copy() if isinstance(v, dict) else v for k, v in original_configs.get("configs", {}).items()}
        temp_configs_dict[config_name_test] = temp_config
        self.config_manager.configs["configs"] = temp_configs_dict
        self.config_manager.configs["last_used"] = config_name_test # Necesario para get_current_environment

        try:
            env = self.config_manager.get_current_environment(config_name_test)

            wine_executable = env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en la ruta especificada o en el PATH del sistema: {wine_executable}")

            # Ejecutar wine --version para probar la configuración
            process = subprocess.run(
                [wine_executable, "--version"],
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
                check=True # Levanta CalledProcessError si el código de retorno no es 0
            )
            version_output = process.stdout.strip()
            QMessageBox.information(
                self,
                "Prueba Exitosa",
                f"Configuración válida.\nVersión Detectada: {version_output}"
            )
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error de Prueba", f"Error de archivo: {str(e)}")
        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "Error de Prueba", "El comando Wine/Proton --version tardó demasiado en responder.")
        except subprocess.CalledProcessError as e:
            error_details = f"Código de Salida: {e.returncode}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            QMessageBox.critical(self, "Error de Prueba", f"El comando Wine/Proton --version falló.\nDetalles:\n{error_details}")
        except Exception as e:
            QMessageBox.critical(self, "Error de Prueba", f"Error inesperado durante la prueba: {str(e)}")
        finally:
            # Restaurar la configuración original
            self.config_manager.configs = original_configs
            self.config_manager.save_configs() # Asegurarse de que el estado guardado sea consistente

class VersionSearchThread(QThread):
    progress = pyqtSignal(int) # Emite el porcentaje de progreso de búsqueda
    new_release = pyqtSignal(str, str, str, object, str) # Emite (tipo, nombre_lanzamiento, version, assets, fecha_publicacion)
    error = pyqtSignal(str) # Emite mensajes de error

    def __init__(self, repo_type: str, repositories: list[dict]):
        super().__init__()
        self.repo_type = repo_type
        self.repositories = repositories

    def run(self):
        fetched_count = 0
        total_repos = len(self.repositories)

        for i, repo in enumerate(self.repositories):
            if not repo.get("enabled", True): # Ignorar repositorios deshabilitados
                fetched_count += 1
                self.progress.emit(int(fetched_count * 100 / total_repos))
                continue

            url = repo["url"]
            try:
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0 WineProtonManager'}) # Añadir User-Agent
                with urlopen(req, timeout=10) as response:
                    if response.getcode() != 200:
                        raise HTTPError(url, response.getcode(), response.reason, response.headers, None)

                    releases = json.loads(response.read().decode())

                    for release in releases:
                        if release.get("draft", False) or release.get("prerelease", False):
                            continue # Ignorar borradores y pre-lanzamientos

                        version = release["tag_name"]
                        # Filtrar assets para incluir solo los tipos de archivo relevantes
                        assets = [a for a in release["assets"] if any(a["name"].endswith(ext) for ext in ['.tar.gz', '.tar.xz', '.zip', '.tar.bz2', '.tar.zst'])]

                        if not assets:
                            continue # No hay assets descargables

                        release_name = release.get("name", version)
                        published_at = release.get("published_at", "")

                        self.new_release.emit(self.repo_type, release_name, version, assets, published_at)

            except HTTPError as e:
                self.error.emit(f"Error HTTP del repositorio '{repo['name']}': {e.code} - {e.reason}")
            except Exception as e:
                self.error.emit(f"Error obteniendo versiones de '{repo['name']}': {str(e)}")
            finally:
                fetched_count += 1
                self.progress.emit(int(fetched_count * 100 / total_repos))

class RepositoryDialog(QDialog):
    def __init__(self, repo_type: str, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.repo_type = repo_type
        self.config_manager = config_manager # Pasar config_manager para aplicar estilos
        self.setWindowTitle(f"Añadir Repositorio de {self.repo_type.capitalize()}")
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)

    def setup_ui(self):
        layout = QFormLayout()

        self.edit_name = QLineEdit()
        layout.addRow("Nombre del Repositorio:", self.edit_name)

        self.edit_url = QLineEdit()
        self.edit_url.setPlaceholderText("Ej: https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases")
        layout.addRow("URL de la API de GitHub:", self.edit_url)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def get_repository_info(self) -> tuple[str, str]:
        """Obtiene el nombre y la URL del repositorio ingresados."""
        name = self.edit_name.text().strip()
        url = self.edit_url.text().strip()

        if not name:
            raise ValueError("El nombre del repositorio no puede estar vacío.")
        if not url:
            raise ValueError("La URL de la API de GitHub no puede estar vacía.")
        if not url.startswith("https://api.github.com/repos/"):
            raise ValueError("URL de la API de GitHub inválida. Debe comenzar con 'https://api.github.com/repos/'.")

        return name, url

class SelectGroupsDialog(QDialog):
    def __init__(self, component_groups: dict[str, list[str]], config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.component_groups = component_groups
        self.config_manager = config_manager # Pasar config_manager para aplicar estilos
        self.setWindowTitle("Seleccionar Componentes de Winetricks")
        self.setMinimumSize(600, 550)
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)

    def setup_ui(self):
        layout = QVBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Componente", "Descripción"])
        self.tree.setColumnCount(2)
        self.tree.setSelectionMode(QTreeWidget.NoSelection) # No permitir selección de ítems
        self.tree.itemChanged.connect(self._handle_item_change) # Conectar la señal de cambio de estado de checkbox

        # Descripciones detalladas para componentes comunes de Winetricks
        self.component_descriptions = {
            "vb2run": "Runtime de Visual Basic 2.0 (Componente antiguo, para aplicaciones muy viejas).",
            "xinput": "XInput (API para controladores de juegos modernos)."
        }

        # MODIFICACIÓN 3: Aumentar tamaño de fuente en 3 puntos
        base_font = STYLE_BREEZE["font"]
        tree_font_size = base_font.pointSize() + 0
        font_for_tree = QFont(base_font.family(), tree_font_size)


        # Llenar el árbol con grupos y componentes
        for group_name, components in self.component_groups.items():
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, group_name)
            group_item.setFont(0, font_for_tree) # Aplicar la fuente al grupo
            # Marcar el ítem del grupo como chequeable con tres estados (Qt.PartiallyChecked)
            group_item.setFlags(group_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsTristate)
            group_item.setCheckState(0, Qt.PartiallyChecked) # Estado inicial

            for comp in components:
                child_item = QTreeWidgetItem(group_item)
                child_item.setText(0, comp)
                child_item.setFont(0, font_for_tree) # Aplicar la fuente al componente
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.Unchecked) # Por defecto desmarcado

                # Asignar descripción o una genérica
                description = self.component_descriptions.get(comp, "Componente estándar de Winetricks.")
                child_item.setText(1, description)
                child_item.setFont(1, font_for_tree) # Aplicar la fuente a la descripción

        self.tree.expandAll() # Expandir todos los grupos por defecto
        # Ajustar el tamaño de las columnas
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.tree)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def _handle_item_change(self, item: QTreeWidgetItem, column: int):
        """Maneja el estado de las casillas de verificación de los elementos del árbol (tres estados)."""
        # Desconectar temporalmente la señal para evitar recursión infinita
        try:
            self.tree.itemChanged.disconnect(self._handle_item_change)
        except TypeError: # Si ya está desconectada (por ejemplo, en la primera llamada)
            pass

        if item.flags() & Qt.ItemIsTristate: # Si es un ítem de grupo (tristate)
            if item.checkState(0) == Qt.Checked:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, Qt.Checked)
            elif item.checkState(0) == Qt.Unchecked:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, Qt.Unchecked)
        else: # Si es un ítem hijo
            parent = item.parent()
            if parent:
                checked_children = 0
                for i in range(parent.childCount()):
                    if parent.child(i).checkState(0) == Qt.Checked:
                        checked_children += 1

                if checked_children == 0:
                    parent.setCheckState(0, Qt.Unchecked)
                elif checked_children == parent.childCount():
                    parent.setCheckState(0, Qt.Checked)
                else:
                    parent.setCheckState(0, Qt.PartiallyChecked)
        # Reconectar la señal
        self.tree.itemChanged.connect(self._handle_item_change)


    def get_selected_components(self) -> list[str]:
        """Devuelve una lista de los componentes de Winetricks seleccionados."""
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
    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager # Pasar config_manager para aplicar estilos
        self.setWindowTitle("Añadir Programa Personalizado")
        # MODIFICACIÓN 2: Establecer tamaño fijo
        self.setFixedSize(650, 140) # Establecer un tamaño fijo
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)

    def setup_ui(self):
        layout = QFormLayout()
        self.edit_name = QLineEdit()
        layout.addRow("Nombre del Programa:", self.edit_name)

        self.edit_path = QLineEdit()
        self.btn_path = QPushButton("Explorar...")
        self.btn_path.setAutoDefault(False)
        self.btn_path.clicked.connect(self.browse_program)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.edit_path)
        path_layout.addWidget(self.btn_path)
        layout.addRow("Ruta del Instalador o Comando Winetricks:", path_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def browse_program(self):
        """Abre un diálogo para seleccionar el programa o script."""
        # MODIFICACIÓN 4: Usar la última carpeta explorada para programas
        default_dir = self.config_manager.get_last_browsed_dir("programs")

        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog) # Usar diálogo nativo de Qt para un control más consistente
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Ejecutables de Windows (*.exe *.msi);;Scripts de Winetricks (*.wtr);;Todos los Archivos (*)")
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        dialog.setDirectory(str(default_dir))

        self.config_manager.apply_breeze_style_to_widget(dialog) # Aplicar estilo al diálogo de archivo

        if dialog.exec_():
            selected_file = dialog.selectedFiles()
            if selected_file:
                self.edit_path.setText(selected_file[0])
                # MODIFICACIÓN 4: Guardar la nueva ruta explorada
                self.config_manager.set_last_browsed_dir("programs", str(Path(selected_file[0]).parent))


    def get_program_info(self) -> dict:
        """Obtiene la información del programa ingresado."""
        name = self.edit_name.text().strip()
        path = self.edit_path.text().strip()

        if not name:
            raise ValueError("Debes especificar un nombre para el programa.")

        program_type = "winetricks" # Valor por defecto si no se puede determinar por extensión

        path_obj = Path(path)
        if path.lower().endswith(('.exe', '.msi')):
            if not path_obj.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {path}")
            program_type = "exe"
            path = str(path_obj.absolute()) # Guardar la ruta absoluta
        elif path.lower().endswith('.wtr'):
            if not path_obj.exists():
                raise FileNotFoundError(f"Archivo de script no encontrado: {path}")
            program_type = "wtr"
            path = str(path_obj.absolute()) # Guardar la ruta absoluta
        else:
            # Si no es .exe, .msi o .wtr, se asume que es un comando de winetricks (ej. "vcrun2019")
            program_type = "winetricks"

        return {
            "name": name,
            "path": path, # path puede ser un nombre de componente o una ruta de archivo
            "type": program_type
        }

class ManageProgramsDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager # Pasar config_manager para aplicar estilos
        self.setWindowTitle("Gestionar Programas Guardados")
        self.setMinimumSize(650, 450)
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)
        self.selected_programs_to_load = [] # Para almacenar programas seleccionados al cargar

    def setup_ui(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nombre", "Comando/Ruta", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows) # Seleccionar filas completas
        self.table.setSelectionMode(QTableWidget.MultiSelection) # Permitir multiselección
        self.load_programs() # Cargar los programas al iniciar el diálogo
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_load_selected = QPushButton("Cargar Selección")
        self.btn_load_selected.setAutoDefault(False)
        self.btn_load_selected.clicked.connect(self.load_selection)
        btn_layout.addWidget(self.btn_load_selected)

        self.btn_delete = QPushButton("Eliminar Selección")
        self.btn_delete.setAutoDefault(False)
        self.btn_delete.clicked.connect(self.delete_programs)
        btn_layout.addWidget(self.btn_delete)

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setAutoDefault(False)
        self.btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_programs(self):
        """Carga y muestra la lista de programas personalizados en la tabla."""
        self.table.setRowCount(0) # Limpiar tabla antes de cargar
        programs = self.config_manager.get_custom_programs()
        self.table.setRowCount(len(programs))

        for row, program in enumerate(programs):
            name_item = QTableWidgetItem(program.get('name', 'N/A'))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable) # No editable
            self.table.setItem(row, 0, name_item)

            path_item = QTableWidgetItem(program.get('path', 'N/A'))
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, path_item)

            type_text = program.get("type", "winetricks").upper()
            type_item = QTableWidgetItem(type_text)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

    def load_selection(self):
        """Carga los programas seleccionados en la lista de instalación principal."""
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())))
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron programas para cargar.")
            return

        all_programs = self.config_manager.get_custom_programs()

        current_config_name = self.config_manager.configs.get("last_used")
        config = self.config_manager.get_config(current_config_name)
        if not config or "prefix" not in config:
            QMessageBox.critical(self, "Error de Configuración", "No hay un prefijo de Wine/Proton activo para verificar instalaciones.")
            return

        prefix_path = config["prefix"]
        installed_items_in_prefix = self.config_manager.get_installed_winetricks(prefix_path)

        programs_to_add = []
        for row in selected_rows:
            program_info = all_programs[row]
            item_already_installed = False

            # Verificar si el programa ya está registrado como instalado en el prefijo
            if program_info["type"] == "winetricks":
                if program_info["path"] in installed_items_in_prefix:
                    item_already_installed = True
            elif program_info["type"] == "exe":
                exe_filename = Path(program_info["path"]).name
                if exe_filename in installed_items_in_prefix:
                    item_already_installed = True
            elif program_info["type"] == "wtr":
                wtr_filename = Path(program_info["path"]).name

                if wtr_filename in installed_items_in_prefix: # Esto asume que el nombre del script se registra.
                    item_already_installed = True

            if item_already_installed:
                reply = QMessageBox.question(self, "Programa ya Instalado",
                                             f"El programa '{program_info['name']}' ya está registrado como instalado en este prefijo ({current_config_name}). ¿Deseas agregarlo a la lista de instalación de todos modos?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    continue # No añadir if user chooses not to

            programs_to_add.append(program_info)

        self.selected_programs_to_load = programs_to_add
        self.accept() # Cierra el diálogo y devuelve QDialog.Accepted

    def delete_programs(self):
        """Elimina los programas seleccionados de la lista guardada."""
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())), reverse=True) # Eliminar desde el final para evitar problemas de índice
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron programas para eliminar.")
            return

        program_names_to_delete = [self.table.item(row, 0).text() for row in selected_rows]

        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar {len(program_names_to_delete)} programa(s) guardado(s)?\n\n" + "\n".join(program_names_to_delete),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count = 0
            for name in program_names_to_delete:
                if self.config_manager.delete_custom_program(name):
                    deleted_count += 1

            if deleted_count > 0:
                self.load_programs() # Recargar la tabla después de eliminar
                QMessageBox.information(self, "Éxito", f"{deleted_count} programa(s) eliminado(s) exitosamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar ningún programa.")

    def get_selected_programs_to_load(self) -> list[dict]:
        """Devuelve los programas seleccionados para cargar."""
        return self.selected_programs_to_load

# --- Ventana Principal ---
class InstallerApp(QWidget):
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.installer_thread = None
        self.backup_thread = None
        self.installation_progress_dialog = None
        self.backup_progress_dialog = None

        self.items_for_installation: list[dict] = [] # Almacena {name, path, type, current_status}

        # Cargar ajustes de sesión al inicio
        self.silent_mode = self.config_manager.get_silent_install()
        self.force_mode = self.config_manager.get_force_winetricks_install()
        self.ask_for_backup_before_action = self.config_manager.get_ask_for_backup_before_action()

        self.apply_theme_at_startup() # Aplicar el tema global de la app
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self) # Reaplicar estilos a todos los widgets de la ventana principal
        self.setMinimumSize(1000, 700)
        self.update_installation_button_state() # Actualizar estado inicial de botones

    def apply_theme_at_startup(self):
        """Aplica el tema inicial de la aplicación a la QApplication."""
        theme = self.config_manager.get_theme()
        palette = QApplication.palette() # Iniciar con la paleta actual de la app
        style_settings = STYLE_BREEZE

        if theme == "dark":
            palette.setColor(QPalette.Window, style_settings["dark_palette"]["window"])
            palette.setColor(QPalette.WindowText, style_settings["dark_palette"]["window_text"])
            palette.setColor(QPalette.Base, style_settings["dark_palette"]["base"])
            palette.setColor(QPalette.Text, style_settings["dark_palette"]["text"])
            palette.setColor(QPalette.Button, style_settings["dark_palette"]["button"])
            palette.setColor(QPalette.ButtonText, style_settings["dark_palette"]["button_text"])
            palette.setColor(QPalette.Highlight, style_settings["dark_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, style_settings["dark_palette"]["highlight_text"])
            palette.setColor(QPalette.ToolTipBase, style_settings["dark_palette"]["base"])
            palette.setColor(QPalette.ToolTipText, style_settings["dark_palette"]["text"])
        else:
            palette.setColor(QPalette.Window, style_settings["light_palette"]["window"])
            palette.setColor(QPalette.WindowText, style_settings["light_palette"]["window_text"])
            palette.setColor(QPalette.Base, style_settings["light_palette"]["base"])
            palette.setColor(QPalette.Text, style_settings["light_palette"]["text"])
            palette.setColor(QPalette.Button, style_settings["light_palette"]["button"])
            palette.setColor(QPalette.ButtonText, style_settings["light_palette"]["button_text"])
            palette.setColor(QPalette.Highlight, style_settings["light_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, style_settings["light_palette"]["highlight_text"])
            palette.setColor(QPalette.ToolTipBase, style_settings["light_palette"]["base"])
            palette.setColor(QPalette.ToolTipText, style_settings["light_palette"]["text"])

        QApplication.setPalette(palette)
        # La fuente de QApplication ya se establece en el main, no es necesario aquí.

    def setup_ui(self):
        """Configura la interfaz de usuario de la ventana principal."""
        self.setWindowTitle("WineProton Manager")
        self.resize(self.config_manager.get_window_size())
        self.setWindowIcon(QIcon.fromTheme("wine")) # Icono desde el tema del sistema

        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QHBoxLayout(content)

        content_layout.addWidget(self.create_left_panel(), 1) # Panel izquierdo, más pequeño
        content_layout.addWidget(self.create_right_panel(), 2) # Panel derecho, más grande
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def create_left_panel(self) -> QWidget:
        """Crea y devuelve el panel izquierdo de la interfaz."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Grupo de Configuración del Entorno Actual
        config_group = QGroupBox("Configuración del Entorno Actual")
        config_layout = QVBoxLayout()
        self.lbl_config = QLabel()
        self.lbl_config.setWordWrap(True)
        self.update_config_info() # Cargar info al inicio

        self.btn_manage_environments = QPushButton("Gestionar Entornos")
        self.btn_manage_environments.setAutoDefault(False)
        self.btn_manage_environments.clicked.connect(self.configure_environments)
        config_layout.addWidget(self.lbl_config)
        config_layout.addWidget(self.btn_manage_environments)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Grupo de Acciones de Instalación
        actions_group = QGroupBox("Acciones de Instalación")
        actions_layout = QVBoxLayout()

        # Subgrupo de Componentes de Winetricks
        components_group = QGroupBox("Componentes de Winetricks")
        components_layout = QVBoxLayout()
        self.btn_select_components = QPushButton("Seleccionar Componentes de Winetricks")
        self.btn_select_components.setAutoDefault(False)
        self.btn_select_components.clicked.connect(self.select_components)
        components_layout.addWidget(self.btn_select_components)
        components_group.setLayout(components_layout)
        actions_layout.addWidget(components_group)

        # Subgrupo de Programas Personalizados
        custom_group = QGroupBox("Programas Personalizados")
        custom_layout = QVBoxLayout()
        self.btn_add_custom = QPushButton("Añadir Programa/Script")
        self.btn_add_custom.setAutoDefault(False)
        self.btn_add_custom.clicked.connect(self.add_custom_program)
        custom_layout.addWidget(self.btn_add_custom)

        self.btn_manage_custom = QPushButton("Cargar/Eliminar Programas Guardados")
        self.btn_manage_custom.setAutoDefault(False)
        self.btn_manage_custom.clicked.connect(self.manage_custom_programs)
        custom_layout.addWidget(self.btn_manage_custom)
        custom_group.setLayout(custom_layout)
        actions_layout.addWidget(custom_group)

        # Subgrupo de Opciones de Instalación
        options_group = QGroupBox("Opciones de Instalación")
        options_layout = QVBoxLayout()
        self.checkbox_silent_session = QCheckBox("Habilitar modo silencioso para esta instalación Winetricks (-q)")
        self.checkbox_silent_session.setChecked(self.silent_mode)
        self.checkbox_silent_session.stateChanged.connect(self.update_silent_mode_session)
        options_layout.addWidget(self.checkbox_silent_session)

        self.checkbox_force_winetricks_session = QCheckBox("Forzar instalación de Winetricks para esta instalación (--force)")
        self.checkbox_force_winetricks_session.setChecked(self.force_mode)
        self.checkbox_force_winetricks_session.stateChanged.connect(self.update_force_mode_session)
        options_layout.addWidget(self.checkbox_force_winetricks_session)

        options_group.setLayout(options_layout)
        actions_layout.addWidget(options_group)

        # Botones de iniciar/cancelar instalación
        self.btn_install = QPushButton("Iniciar Instalación")
        self.btn_install.setAutoDefault(False)
        self.btn_install.clicked.connect(self.start_installation)
        self.btn_install.setEnabled(False) # Deshabilitado hasta que haya ítems

        self.btn_cancel = QPushButton("Cancelar Instalación")
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.clicked.connect(self.cancel_installation)
        self.btn_cancel.setEnabled(False) # Deshabilitado hasta que haya una instalación en curso

        actions_layout.addWidget(self.btn_install)
        actions_layout.addWidget(self.btn_cancel)

        # Grupo de Herramientas del Prefijo
        tools_group = QGroupBox("Herramientas del Prefijo")
        tools_layout = QHBoxLayout()

        left_column = QVBoxLayout()
        self.btn_shell = QPushButton("Terminal")
        self.btn_shell.setAutoDefault(False)
        self.btn_shell.clicked.connect(self.open_shell)
        left_column.addWidget(self.btn_shell)

        self.btn_prefix_folder = QPushButton("Carpeta del Prefijo")
        self.btn_prefix_folder.setAutoDefault(False)
        self.btn_prefix_folder.clicked.connect(self.open_prefix_folder)
        left_column.addWidget(self.btn_prefix_folder)

        self.backup_prefix_button = QPushButton("Backup Prefijo")
        self.backup_prefix_button.setAutoDefault(False)
        self.backup_prefix_button.clicked.connect(self.perform_backup)
        left_column.addWidget(self.backup_prefix_button)

        right_column = QVBoxLayout()
        self.btn_winetricks_gui = QPushButton("Winetricks GUI")
        self.btn_winetricks_gui.setAutoDefault(False)
        self.btn_winetricks_gui.clicked.connect(self.open_winetricks)
        right_column.addWidget(self.btn_winetricks_gui)

        self.btn_winecfg = QPushButton("Winecfg")
        self.btn_winecfg.setAutoDefault(False)
        self.btn_winecfg.clicked.connect(self.open_winecfg)
        right_column.addWidget(self.btn_winecfg)

        self.btn_explorer = QPushButton("Explorer")
        self.btn_explorer.setAutoDefault(False)
        self.btn_explorer.clicked.connect(self.open_explorer)
        right_column.addWidget(self.btn_explorer)

        tools_layout.addLayout(left_column)
        tools_layout.addLayout(right_column)
        tools_group.setLayout(tools_layout)
        actions_layout.addWidget(tools_group)

        actions_layout.addStretch() # Empujar los elementos hacia arriba
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        return panel

    def create_right_panel(self) -> QWidget:
        """Crea y devuelve el panel derecho (lista de instalación)."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.lbl_status = QLabel("Lista de elementos a instalar:")
        layout.addWidget(self.lbl_status)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Seleccionar", "Nombre", "Tipo", "Estado"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.items_table.verticalHeader().setVisible(False) # Ocultar los números de fila
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows) # Seleccionar filas completas
        self.items_table.setSelectionMode(QTableWidget.SingleSelection) # Permitir solo una selección para mover
        self.items_table.itemChanged.connect(self.on_table_item_changed) # Conectar para manejar el checkbox
        layout.addWidget(self.items_table)

        btn_layout = QHBoxLayout()
        self.btn_clear_list = QPushButton("Limpiar Lista")
        self.btn_clear_list.setAutoDefault(False)
        self.btn_clear_list.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.btn_clear_list)

        self.btn_delete_selection = QPushButton("Eliminar Selección")
        self.btn_delete_selection.setAutoDefault(False)
        self.btn_delete_selection.clicked.connect(self.delete_selected_from_table)
        btn_layout.addWidget(self.btn_delete_selection)

        self.btn_move_up = QPushButton("Mover Arriba")
        self.btn_move_up.setAutoDefault(False)
        self.btn_move_up.clicked.connect(self.move_item_up)
        btn_layout.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("Mover Abajo")
        self.btn_move_down.setAutoDefault(False)
        self.btn_move_down.clicked.connect(self.move_item_down)
        btn_layout.addWidget(self.btn_move_down)

        layout.addLayout(btn_layout)
        return panel

    def on_table_item_changed(self, item: QTableWidgetItem):
        """Maneja los cambios en las casillas de verificación de la tabla y actualiza el estado interno.
           MODIFICACIÓN 1: Al volver a tildar un programa, se restablece a "Pendiente"."""
        # Desconectar temporalmente para evitar llamadas recursivas
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass

        if item.column() == 0: # Si el cambio es en la columna del checkbox
            row = item.row()
            status_item = self.items_table.item(row, 3) # Obtener el ítem de estado

            if status_item:
                if item.checkState() == Qt.Checked:
                    new_status = "Pendiente"
                    status_item.setForeground(QColor(STYLE_BREEZE["dark_palette"]["text"] if self.config_manager.get_theme() == "dark" else STYLE_BREEZE["light_palette"]["text"]))
                else: # Qt.Unchecked
                    new_status = "Omitido"
                    status_item.setForeground(QColor("darkorange"))

                status_item.setText(new_status)
                if 0 <= row < len(self.items_for_installation):
                    self.items_for_installation[row]['current_status'] = new_status
            # else: print(f"DEBUG: El elemento de estado es None para la fila {row}.")

        self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar la señal
        self.update_installation_button_state() # Actualizar estado del botón Instalar

    def update_silent_mode_session(self, state: int):
        """Actualiza el modo silencioso para la sesión actual."""
        self.silent_mode = state == Qt.Checked

    def update_force_mode_session(self, state: int):
        """Actualiza el modo forzado para la sesión actual."""
        self.force_mode = state == Qt.Checked

    def closeEvent(self, event):
        """Guarda el tamaño de la ventana al cerrar."""
        self.config_manager.save_window_size(self.size())
        super().closeEvent(event)

    def configure_environments(self):
        """Abre el diálogo para configurar entornos de Wine/Proton."""
        dialog = ConfigDialog(self.config_manager, self)
        dialog.update_save_settings_button_state()
        dialog.config_saved.connect(self.handle_config_saved_and_restart) # Conectar a la nueva función de reinicio
        dialog.exec_()
        self.update_config_info() # Asegurarse de actualizar la info al cerrar el diálogo

    def handle_config_saved_and_restart(self):
        """
        Maneja la señal de que la configuración ha sido guardada.
        Cierra la aplicación actual y la reinicia.
        """
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)


    def update_config_info(self):
        """Actualiza la información del entorno actual en la GUI."""
        current_config_name = self.config_manager.configs.get("last_used", "Wine-System")
        config = self.config_manager.get_config(current_config_name)

        if not config:
            self.lbl_config.setText("No se ha seleccionado ninguna configuración o la configuración es inválida.")
            return

        try:
            env = self.config_manager.get_current_environment(current_config_name)
            version = env.get("PROTON_VERSION") if config.get("type") == "proton" else env.get("WINE_VERSION", "Desconocida")
            wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "N/A")

            # Construir el texto de información con formato HTML
            text = [
                f"<b>Configuración Actual:</b> {current_config_name}",
                f"<b>Tipo:</b> {'Proton' if config.get('type') == 'proton' else 'Wine'}",
                f"<b>Versión Detectada:</b> <span style='color: {COLOR_BREEZE_PRIMARY}; font-weight: bold;'>{version}</span>",
            ]

            if config.get('type') == 'proton':
                text.extend([
                    f"<b>Wine en Proton:</b> <span style='color: {COLOR_BREEZE_PRIMARY}; font-weight: bold;'>{wine_version_in_proton}</span>",
                    f"<b>Directorio de Proton:</b> {config.get('proton_dir', 'No especificado')}"
                ])
                if "steam_appid" in config:
                    text.append(f"<b>APPID de Steam:</b> {config['steam_appid']}")
                    text.append(f"<b>Prefijo gestionado por Steam:</b> Sí")
                else:
                    text.append(f"<b>Prefijo personalizado:</b> Sí")
            else: # Tipo Wine
                wine_dir = config.get('wine_dir', 'Sistema (PATH)')
                text.extend([
                    f"<b>Directorio de Wine:</b> {wine_dir}"
                ])

            text.extend([
                f"<b>Arquitectura:</b> {config.get('arch', 'win64')}",
                f"<b>Prefijo:</b> <span style='color: #FFB347; font-weight: bold;'>{config.get('prefix', 'No especificado')}</span>"
            ])

            self.lbl_config.setText("<br>".join(text))
        except FileNotFoundError as e:
            self.lbl_config.setText(f"ERROR: {str(e)}<br>Por favor, revisa la configuración.")
            QMessageBox.critical(self, "Error de Configuración", str(e))
        except Exception as e:
            self.lbl_config.setText(f"ERROR: No se pudo obtener información de configuración: {str(e)}")

    def add_custom_program(self):
        """Abre el diálogo para añadir un nuevo programa/script personalizado."""
        dialog = CustomProgramDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                program_info = dialog.get_program_info()

                # Evitar duplicados en la lista de instalación actual
                current_paths_in_table = [item['path'] for item in self.items_for_installation]
                if program_info['path'] in current_paths_in_table:
                    QMessageBox.warning(self, "Duplicado", f"El programa '{program_info['name']}' ya está en la lista de instalación.")
                    return

                # Verificar si ya está "instalado" en el prefijo actual (registrado en el log)
                current_config_name = self.config_manager.configs["last_used"]
                config = self.config_manager.get_config(current_config_name)

                installed_items = []
                if config and "prefix" in config:
                    installed_items = self.config_manager.get_installed_winetricks(config["prefix"])

                # Lógica para preguntar si ya está instalado y si aún así desea añadirlo
                already_registered = False
                if program_info["type"] == "winetricks" and program_info["path"] in installed_items:
                    already_registered = True
                elif program_info["type"] == "exe":
                    exe_filename = Path(program_info["path"]).name
                    # La lógica de detección de EXE instalado es básica; podría mejorarse con hashes o nombres más robustos.
                    # Aquí asume que si el nombre del ejecutable está en el .ini, ya está "instalado".
                    if exe_filename in installed_items:
                        already_registered = True
                elif program_info["type"] == "wtr":
                    wtr_filename = Path(program_info["path"]).name

                    if wtr_filename in installed_items: # Esto asume que el nombre del script se registra.
                        already_registered = True

                if already_registered:
                    reply = QMessageBox.question(self, "Programa ya Instalado/Ejecutado",
                                                 f"El programa/componente '{program_info['name']}' ya está registrado como instalado en este prefijo. ¿Deseas agregarlo a la lista de instalación de todos modos?",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.No: return

                self.config_manager.add_custom_program(program_info) # Guardar en la configuración persistente
                self.add_item_to_table(program_info) # Añadir a la tabla de instalación de la UI
                self.update_installation_button_state() # Actualizar estado del botón Instalar

            except ValueError as e:
                QMessageBox.warning(self, "Entrada Inválida", str(e))
            except FileNotFoundError as e:
                QMessageBox.warning(self, "Archivo no Encontrado", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al añadir programa: {str(e)}")

    def add_item_to_table(self, program_data: dict):
        """Añade un elemento a la tabla de instalación."""
        # Desconectar temporalmente para evitar on_table_item_changed inesperadas
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass

        row_count = self.items_table.rowCount()
        self.items_table.insertRow(row_count)

        # Columna 0: Checkbox
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checkbox_item.setCheckState(Qt.Checked) # Por defecto marcado para instalar
        self.items_table.setItem(row_count, 0, checkbox_item)

        # Columna 1: Nombre
        name_item = QTableWidgetItem(program_data["name"])
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable) # No editable
        self.items_table.setItem(row_count, 1, name_item)

        # Columna 2: Tipo
        type_text = program_data["type"].upper()
        type_item = QTableWidgetItem(type_text)
        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row_count, 2, type_item)

        # Columna 3: Estado
        status_item = QTableWidgetItem("Pendiente")
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row_count, 3, status_item)

        program_data['current_status'] = "Pendiente" # Añadir estado al diccionario interno
        self.items_for_installation.append(program_data) # Añadir al modelo interno

        self.update_installation_button_state()
        # Reconectar la señal
        self.items_table.itemChanged.connect(self.on_table_item_changed)

    def manage_custom_programs(self):
        """Abre el diálogo para gestionar (cargar/eliminar) programas personalizados."""
        dialog = ManageProgramsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted: # Si el diálogo se cerró con "Aceptar"
            selected_programs = dialog.get_selected_programs_to_load()
            for program_info in selected_programs:
                # Añadir solo si no está ya en la lista de instalación actual para evitar duplicados
                if not any(item['path'] == program_info['path'] and item['type'] == program_info['type'] for item in self.items_for_installation):
                    self.add_item_to_table(program_info)
            self.update_installation_button_state()

    def select_components(self):
        """Abre el diálogo para seleccionar componentes de Winetricks."""
        # Definición de grupos de componentes de Winetricks
        component_groups = {
            "Librerías de Visual Basic": ["vb2run", "vb3run", "vb4run", "vb5run", "vb6run"],
            "Librerías de Visual C++": [
                "vcrun6", "vcrun6sp6", "vcrun2003", "vcrun2005", "vcrun2008",
                "vcrun2019", "vcrun2022"
            ],
            "Framework .NET": [
                "dotnet11", "dotnet11sp1", "dotnet20", "dotnet20sp1", "dotnet20sp2",
                "dotnetdesktop6", "dotnetdesktop7", "dotnetdesktop8", "dotnetdesktop9"
            ],
            "DirectX y Multimedia": [
                "d3dcompiler_42", "d3dcompiler_43", "d3dcompiler_46", "d3dcompiler_47",
                "xact_x64", "xaudio29", "xinput", "xna31", "xna40"
            ],
            "Códecs Multimedia": [
                "allcodecs", "avifil32", "binkw32", "cinepak", "dirac", "ffdshow",
                "quicktime76", "wmp9", "wmp10", "wmp11", "wmv9vcm", "xvid"
            ],
            "Componentes del Sistema": [
                "amstream", "atmlib", "cabinet", "cmd", "comctl32", "comctl32ocx",
                "wininet_win2k", "wmi", "wsh57", "xmllite"
            ],
            "Controladores y Utilidades": [
                "art2k7min", "art2kmin", "cnc_ddraw", "d2gl", "d3drm", "dpvoice",
                "physx", "powershell", "powershell_core"
            ],
            "Fuentes": [
                "allfonts", "andale", "arial", "baekmuk", "calibri", "cambria",
                "wenquanyi", "wenquanyizenhei"
            ]
        }

        dialog = SelectGroupsDialog(component_groups, self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_components = dialog.get_selected_components()

            current_config_name = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config_name)
            installed_components = []
            if config and "prefix" in config:
                installed_components = self.config_manager.get_installed_winetricks(config["prefix"])

            for comp_name in selected_components:
                # Comprobar si ya está en la lista de instalación
                if any(item.get('path') == comp_name and item.get('type') == 'winetricks' for item in self.items_for_installation):
                    QMessageBox.warning(self, "Duplicado", f"El componente '{comp_name}' ya está en la lista de instalación.")
                    continue

                # Comprobar si ya está registrado como instalado en el prefijo
                if comp_name in installed_components:
                    reply = QMessageBox.question(self, "Componente ya instalado",
                                                 f"El componente '{comp_name}' ya está registrado como instalado en este prefijo. ¿Deseas agregarlo a la lista de instalación de todos modos?",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.No:
                        continue # No añadir si el usuario elige no hacerlo

                # Añadir a la tabla de instalación
                self.add_item_to_table({"name": comp_name, "path": comp_name, "type": "winetricks"})
            self.update_installation_button_state() # Actualizar estado del botón Instalar

    def cancel_installation(self):
        """Detiene la instalación actual."""
        if self.installer_thread and self.installer_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirmar Cancelación",
                "¿Estás seguro de que quieres cancelar la instalación en curso? Esto puede dejar el prefijo en un estado inconsistente.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.installer_thread.stop() # Enviar señal de parada al hilo
                self.installer_thread.wait(5000) # Esperar a que el hilo termine (hasta 5 segundos)
                if self.installer_thread.isRunning():
                    print("Advertencia: El hilo de instalación no terminó a tiempo.")

                QMessageBox.information(self, "Cancelado", "La instalación ha sido cancelada por el usuario.")

                # Actualizar el estado de los ítems en la tabla que aún no han sido procesados o están en curso
                for row, item_data in enumerate(self.items_for_installation):
                    status_item = self.items_table.item(row, 3)
                    checkbox_item = self.items_table.item(row, 0)
                    if item_data['current_status'] == "Instalando":
                        item_data['current_status'] = "Cancelado"
                        if status_item:
                            status_item.setText("Cancelado")
                            status_item.setForeground(QColor("red"))
                        if checkbox_item:
                            checkbox_item.setCheckState(Qt.Checked) # Dejar marcado si se canceló
                    elif item_data['current_status'] == "Pendiente":
                        item_data['current_status'] = "Omitido"
                        if status_item:
                            status_item.setText("Omitido")
                            status_item.setForeground(QColor("darkorange"))
                        if checkbox_item:
                            checkbox_item.setCheckState(Qt.Unchecked) # Desmarcar si se omitió

                if self.installation_progress_dialog:
                    self.installation_progress_dialog.set_status("Cancelado")

                self.installation_finished() # Llamar al manejador de finalización para restablecer la UI
        else:
            QMessageBox.information(self, "Información", "No hay ninguna instalación en progreso para cancelar.")

    def clear_list(self):
        """Borra la tabla y el modelo de datos interno."""
        reply = QMessageBox.question(self, "Confirmar", "¿Estás seguro de que quieres borrar toda la lista de instalación?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Desconectar para evitar que itemChanged se dispare durante la limpieza
            try:
                self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            except TypeError:
                pass

            self.items_table.setRowCount(0) # Limpiar la tabla de la UI
            self.items_for_installation.clear() # Limpiar el modelo de datos interno
            self.update_installation_button_state() # Actualizar estado del botón Instalar

            # Reconectar la señal
            self.items_table.itemChanged.connect(self.on_table_item_changed)

    def delete_selected_from_table(self):
        """Elimina los elementos seleccionados de la tabla y el modelo interno."""
        # Obtener filas seleccionadas y ordenarlas de mayor a menor para evitar problemas de índice al eliminar
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())), reverse=True)

        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron elementos para eliminar.")
            return

        program_names_to_delete = [self.items_table.item(row, 1).text() for row in selected_rows]

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Estás seguro de que quieres eliminar {len(selected_rows)} elemento(s) de la lista de instalación?\n\n" + "\n".join(program_names_to_delete),
                                     QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Desconectar para evitar que itemChanged se dispare durante la eliminación
            try:
                self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            except TypeError:
                pass

            for row in selected_rows:
                if 0 <= row < len(self.items_for_installation):
                    del self.items_for_installation[row] # Eliminar del modelo interno
                self.items_table.removeRow(row) # Eliminar de la tabla de la UI

            self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar
            self.update_installation_button_state()

    def move_item_up(self):
        """Mueve el elemento seleccionado en la tabla una posición hacia arriba."""
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())))

        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Advertencia", "Selecciona solo un elemento para mover.")
            return

        current_row = selected_rows[0]
        if current_row > 0: # Solo si no es la primera fila
            # Desconectar temporalmente para evitar problemas con itemChanged
            try:
                self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            except TypeError:
                pass

            # Intercambiar elementos en la tabla de la UI
            self.swap_table_rows(current_row, current_row - 1)

            # Intercambiar elementos en el modelo interno
            self.items_for_installation[current_row], self.items_for_installation[current_row - 1] = \
                self.items_for_installation[current_row - 1], self.items_for_installation[current_row]

            self.items_table.selectRow(current_row - 1) # Mantener la selección en el ítem movido
            self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar

    def move_item_down(self):
        """Mueve el elemento seleccionado en la tabla una posición hacia abajo."""
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())))

        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Advertencia", "Selecciona solo un elemento para mover.")
            return

        current_row = selected_rows[0]
        if current_row < self.items_table.rowCount() - 1: # Solo si no es la última fila
            # Desconectar temporalmente
            try:
                self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            except TypeError:
                pass

            # Intercambiar elementos en la tabla de la UI
            self.swap_table_rows(current_row, current_row + 1)

            # Intercambiar elementos en el modelo interno
            self.items_for_installation[current_row], self.items_for_installation[current_row + 1] = \
                self.items_for_installation[current_row + 1], self.items_for_installation[current_row]

            self.items_table.selectRow(current_row + 1) # Mantener la selección
            self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar

    def swap_table_rows(self, row1: int, row2: int):
        """Intercambia dos filas en la tabla."""
        # Se necesita deshabilitar la señal itemChanged antes de llamar a esto
        row1_items = [self.items_table.takeItem(row1, col) for col in range(self.items_table.columnCount())]
        row2_items = [self.items_table.takeItem(row2, col) for col in range(self.items_table.columnCount())]

        for col in range(self.items_table.columnCount()):
            self.items_table.setItem(row2, col, row1_items[col])
            self.items_table.setItem(row1, col, row2_items[col])

    def update_installation_button_state(self):
        """Habilita/deshabilita los botones de acción según el estado de la aplicación."""
        any_checked = False
        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 0).checkState() == Qt.Checked:
                any_checked = True

        is_installer_running = self.installer_thread is not None and self.installer_thread.isRunning()
        is_backup_running = self.backup_thread is not None and self.backup_thread.isRunning()

        # Botones de instalación
        self.btn_install.setEnabled(any_checked and not is_installer_running and not is_backup_running)
        # MODIFICACIÓN 1: El botón de cancelar siempre está habilitado si la instalación está en curso
        self.btn_cancel.setEnabled(is_installer_running)

        can_modify_list = not is_installer_running and not is_backup_running
        self.btn_select_components.setEnabled(can_modify_list)
        self.btn_add_custom.setEnabled(can_modify_list)
        self.btn_manage_custom.setEnabled(can_modify_list)
        self.btn_clear_list.setEnabled(can_modify_list)
        self.btn_delete_selection.setEnabled(can_modify_list)
        self.btn_move_up.setEnabled(can_modify_list)
        self.btn_move_down.setEnabled(can_modify_list)

        can_use_prefix_tools = not is_backup_running
        self.btn_shell.setEnabled(can_use_prefix_tools)
        self.btn_prefix_folder.setEnabled(can_use_prefix_tools)
        self.btn_winetricks_gui.setEnabled(can_use_prefix_tools)
        self.btn_winecfg.setEnabled(can_use_prefix_tools)
        self.btn_explorer.setEnabled(can_use_prefix_tools)
        self.backup_prefix_button.setEnabled(can_use_prefix_tools) # Incluir el botón de backup aquí también

    def start_installation(self):
        """Inicia el proceso de instalación de los elementos seleccionados."""
        # Filtrar solo los elementos que están marcados para instalar
        items_to_process = [
            item_data for row, item_data in enumerate(self.items_for_installation)
            if self.items_table.item(row, 0).checkState() == Qt.Checked
        ]

        if not items_to_process:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron elementos para instalar. Marca los elementos que deseas instalar.")
            return

        for row in range(self.items_table.rowCount()):
            item_data = self.items_for_installation[row]
            checkbox_item = self.items_table.item(row, 0)
            status_item = self.items_table.item(row, 3)

            if checkbox_item.checkState() == Qt.Checked:
                item_data['current_status'] = "Pendiente"
                if status_item:
                    status_item.setText("Pendiente")
                    theme = self.config_manager.get_theme()
                    text_color = STYLE_BREEZE["dark_palette"]["text"] if theme == "dark" else STYLE_BREEZE["light_palette"]["text"]
                    status_item.setForeground(QColor(text_color))
            else:
                item_data['current_status'] = "Omitido"
                if status_item:
                    status_item.setText("Omitido")
                    status_item.setForeground(QColor("darkorange"))


        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_start_installation())
        else:
            self._continue_start_installation()

    def _continue_start_installation(self):
        """Continúa con la instalación después de la posible solicitud de backup."""
        current_config_name = self.config_manager.configs.get("last_used")
        config = self.config_manager.get_config(current_config_name)

        if not config:
            QMessageBox.critical(self, "Error", "No se ha seleccionado ninguna configuración de Wine/Proton o es inválida.")
            return

        items_to_process_data_for_thread = [
            (item_data['path'], item_data['type'], item_data['name'])
            for item_data in self.items_for_installation
            if item_data['current_status'] == "Pendiente"
        ]

        if not items_to_process_data_for_thread:
            QMessageBox.warning(self, "Advertencia", "No hay elementos seleccionados con estado 'Pendiente' para instalar.")
            return

        prefix_path = Path(config["prefix"])
        if not prefix_path.exists():
            reply = QMessageBox.question(
                self, "Prefijo No Encontrado",
                f"El prefijo de Wine/Proton en '{config['prefix']}' no existe. ¿Deseas crearlo ahora? Esto inicializará el prefijo.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    self._create_prefix(config, current_config_name, prefix_path)
                    QMessageBox.information(self, "Prefijo Creado", "El prefijo de Wine/Proton ha sido creado exitosamente.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo crear el prefijo:\n{str(e)}")
                    return
            else:
                return # No continuar si el usuario no quiere crear el prefijo

        try:
            env = self.config_manager.get_current_environment(current_config_name)
        except Exception as e:
            QMessageBox.critical(self, "Error de Entorno", f"No se pudo configurar el entorno para la instalación:\n{str(e)}")
            return

        # Mostrar diálogo de progreso de instalación
        first_item_name_for_dialog = items_to_process_data_for_thread[0][2] if items_to_process_data_for_thread else "elementos"
        self.installation_progress_dialog = InstallationProgressDialog(first_item_name_for_dialog, self.config_manager, self)

        # Iniciar el hilo de instalación
        self.installer_thread = InstallerThread(
            items_to_process_data_for_thread,
            env,
            silent_mode=self.silent_mode,
            force_mode=self.force_mode,
            winetricks_path=self.config_manager.get_winetricks_path(),
            config_manager=self.config_manager
        )

        # Conectar señales del hilo a slots de la UI
        self.installer_thread.progress.connect(self.update_progress)
        self.installer_thread.finished.connect(self.installation_finished)
        # [MODIFICACIÓN 1] Manejar errores de ítems individualmente, y errores fatales globales.
        self.installer_thread.error.connect(self.show_global_installation_error) # Para errores que detienen todo
        self.installer_thread.item_error.connect(self.show_item_installation_error) # Para errores de ítems que continúan
        self.installer_thread.canceled.connect(self.on_installation_canceled)
        self.installer_thread.console_output.connect(self.installation_progress_dialog.append_log)

        # Deshabilitar botones que modifican la lista o inician nueva instalación
        self.update_installation_button_state()

        # Deshabilitar interacción con checkboxes de la tabla durante la instalación
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass
        for row in range(self.items_table.rowCount()):
            checkbox_item = self.items_table.item(row, 0)
            if checkbox_item:
                checkbox_item.setFlags(checkbox_item.flags() & ~Qt.ItemIsUserCheckable & ~Qt.ItemIsEnabled)
                # Cambiar estado visual del primer ítem a "Instalando" si es Pendiente
                if self.items_for_installation[row]['current_status'] == "Pendiente":
                    self.items_table.item(row, 3).setText("Instalando")
                    self.items_for_installation[row]['current_status'] = "Instalando"
                    self.items_table.item(row, 3).setForeground(QColor("blue"))
        self.items_table.itemChanged.connect(self.on_table_item_changed)

        # MODIFICACIÓN 1: Mostrar el diálogo de progreso después de configurar todo, no bloquear la UI principal
        self.installation_progress_dialog.show()
        self.installer_thread.start()

    def _create_prefix(self, config: dict, config_name: str, prefix_path: Path):
        """Crea un nuevo prefijo de Wine/Proton y lo inicializa con wineboot."""
        prefix_path.mkdir(parents=True, exist_ok=True, mode=0o755)

        # Temporalmente asignar la config para que get_current_environment funcione
        original_configs = self.config_manager.configs.copy()
        temp_configs_dict = {k: v.copy() if isinstance(v, dict) else v for k, v in original_configs.get("configs", {}).items()}
        temp_configs_dict[config_name] = config
        self.config_manager.configs["configs"] = temp_configs_dict
        self.config_manager.configs["last_used"] = config_name

        env = self.config_manager.get_current_environment(config_name)

        wine_executable = env.get("WINE")
        if not wine_executable or not Path(wine_executable).is_file():
            # Restaurar configs antes de levantar el error
            self.config_manager.configs = original_configs
            self.config_manager.save_configs()
            raise FileNotFoundError(f"Ejecutable de Wine no encontrado: {wine_executable}")

        progress_dialog = QProgressDialog("Inicializando Prefijo de Wine/Proton...", "", 0, 0, self)
        progress_dialog.setWindowTitle("Inicialización del Prefijo")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.setFixedSize(450, 150)
        self.config_manager.apply_breeze_style_to_widget(progress_dialog)
        progress_dialog.show()

        try:
            process = subprocess.Popen(
                [wine_executable, "wineboot"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            log_output = ""
            for line in process.stdout:
                log_output += line
                progress_dialog.setLabelText(f"Inicializando Prefijo de Wine/Proton...\n{line.strip()}")
                QApplication.processEvents()
            process.wait(timeout=60) # Tiempo de espera para wineboot

            self.config_manager.write_to_log("Creación del Prefijo", f"Salida de Wineboot para {config_name}:\n{log_output}")

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "wineboot", output=log_output)

        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception("La inicialización del prefijo de Wine/Proton agotó el tiempo de espera.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"No se pudo inicializar el prefijo de Wine/Proton. Código de salida: {e.returncode}\nSalida: {e.output}")
        finally:
            progress_dialog.close()
            # Asegurarse de restaurar el estado original de configs
            self.config_manager.configs = original_configs
            self.config_manager.save_configs()

    def update_progress(self, name: str, status: str):
        """Actualiza el estado de un elemento en la tabla y en el modelo interno."""
        found_in_model = False
        for item_data in self.items_for_installation:
            if item_data['name'] == name:
                item_data['current_status'] = status
                found_in_model = True
                break

        if self.installation_progress_dialog and self.installation_progress_dialog.isVisible():
            # Actualizar el label principal del diálogo de progreso
            self.installation_progress_dialog.set_status(f"Instalando {name}: {status}")

        # Actualizar el ítem de estado en la tabla
        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 1).text() == name:
                status_item = self.items_table.item(row, 3)
                if status_item:
                    status_item.setText(status)
                    # Colorear según el estado
                    if "Error" in status:
                        status_item.setForeground(QColor(255, 0, 0)) # Rojo
                    elif "Finalizado" in status:
                        status_item.setForeground(QColor(0, 128, 0)) # Verde
                    elif "Omitido" in status:
                        status_item.setForeground(QColor("darkorange")) # Naranja
                    elif "Instalando" in status:
                        status_item.setForeground(QColor("blue")) # Azul
                    else:
                        theme = self.config_manager.get_theme()
                        text_color = STYLE_BREEZE["dark_palette"]["text"] if theme == "dark" else STYLE_BREEZE["light_palette"]["text"]
                        status_item.setForeground(QColor(text_color)) # Color por defecto
                # else: print(f"DEBUG: El elemento de estado es None para la fila {row}, nombre '{name}'.")
                break

    def on_installation_canceled(self, item_name: str):
        """Actualiza el estado de un elemento cuando la instalación es cancelada."""
        for item_data in self.items_for_installation:
            if item_data['name'] == item_name:
                item_data['current_status'] = "Cancelado"
                break

        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 1).text() == item_name:
                status_item = self.items_table.item(row, 3)
                checkbox_item = self.items_table.item(row, 0)
                if status_item:
                    status_item.setText("Error") # Marcar como error en la UI al cancelar
                    status_item.setForeground(QColor(255, 0, 0))
                if checkbox_item:
                    checkbox_item.setFlags(checkbox_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled) # Habilitar checkbox
                    checkbox_item.setCheckState(Qt.Checked) # Dejar marcado si se canceló
                break

        if self.installation_progress_dialog:
            self.installation_progress_dialog.set_status("Cancelado")

    def installation_finished(self):
        """
        MODIFICACIÓN 1: Maneja el estado final de la instalación, actualizando la GUI y mostrando un resumen.
        Limpia la lista de selección, pero mantiene los estados de los ítems.
        Los ítems "Finalizado" y "Omitido" se desmarcan. Los "Error" o "Cancelado" se mantienen marcados.
        """
        installed_count = 0
        failed_count = 0
        skipped_count = 0

        # Desconectar temporalmente para evitar problemas de eventos
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass

        for row in range(self.items_table.rowCount()):
            item_data = self.items_for_installation[row]
            current_status = item_data['current_status']
            checkbox_item = self.items_table.item(row, 0)
            status_item = self.items_table.item(row, 3)

            if "Finalizado" in current_status:
                installed_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Unchecked) # Desmarcar
                if status_item:
                    status_item.setForeground(QColor(0, 128, 0)) # Verde
            elif "Error" in current_status or "Cancelado" in current_status:
                failed_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Checked) # Mantener marcado
                if status_item:
                    status_item.setForeground(QColor(255, 0, 0)) # Rojo
            elif "Omitido" in current_status:
                skipped_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Unchecked) # Desmarcar
                if status_item:
                    status_item.setForeground(QColor("darkorange")) # Naranja

            # Re-habilitar los checkboxes para edición después de la instalación
            if checkbox_item:
                checkbox_item.setFlags(checkbox_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

        self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar

        # Restablecer el estado de los botones
        self.update_installation_button_state()

        if self.installation_progress_dialog:
            self.installation_progress_dialog.set_status("Finalizado")

        QMessageBox.information(
            self,
            "Instalación Completada",
            f"Resumen de la Instalación:\n\n"
            f"• Instalado exitosamente: {installed_count}\n"
            f"• Fallido o Cancelado: {failed_count}\n"
            f"• Omitido (no seleccionado inicialmente): {skipped_count}\n\n"
            f"Los elementos se han desmarcado o dejado marcados según el resultado." # Mensaje actualizado
        )
        self.installer_thread = None # Asegurarse de limpiar la referencia al hilo

    def show_global_installation_error(self, message: str):
        """[MODIFICACIÓN 1] Muestra un mensaje de error crítico que detiene *toda* la instalación."""
        if self.installation_progress_dialog:
            self.installation_progress_dialog.append_log(f"ERROR FATAL: {message}")
            self.installation_progress_dialog.set_status("Error Crítico")

        QMessageBox.critical(self, "Error Crítico de Instalación", message + "\nLa instalación se ha detenido.")
        self.update_installation_button_state() # Restablecer botones

        # Re-habilitar los checkboxes para edición
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass
        for row in range(self.items_table.rowCount()):
            checkbox_item = self.items_table.item(row, 0)
            if checkbox_item:
                checkbox_item.setFlags(checkbox_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar

        self.installer_thread = None # Asegurarse de limpiar la referencia al hilo

    def show_item_installation_error(self, item_name: str, error_message: str):
        """[MODIFICACIÓN 1] Maneja errores de ítems individuales (la instalación continúa)."""
        if self.installation_progress_dialog:
            self.installation_progress_dialog.append_log(f"ERROR para '{item_name}': {error_message}")
            # El diálogo de progreso principal seguirá mostrando "Instalando [siguiente item]"

    def _get_backup_destination_path(self, current_config_name: str, source_to_backup: Path, is_full_backup: bool) -> Path | None:
        """
        Determina la ruta de destino correcta para el backup.
        Si is_full_backup es True, creará una subcarpeta con timestamp.
        Si es incremental, intentará usar la ruta del último backup completo para *esa* configuración.
        """
        base_backup_path_for_config = self.config_manager.backup_dir / current_config_name
        base_backup_path_for_config.mkdir(parents=True, exist_ok=True)

        if is_full_backup:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            # El destino final incluye el nombre de la carpeta a copiar (source_to_backup.name)
            return base_backup_path_for_config / f"{source_to_backup.name}_backup_{timestamp}"
        else:
            # Para backup incremental, el destino es la última ruta de backup completo guardada para *esta* configuración.
            last_full_backup_path_str = self.config_manager.get_last_full_backup_path(current_config_name) # MODIFICACIÓN: Pasar config_name
            if last_full_backup_path_str and Path(last_full_backup_path_str).is_dir():
                return Path(last_full_backup_path_str)
            return None # Indicar que no hay un backup completo previo para incremental para esta configuración

    def perform_backup(self):
        """
        Inicia el proceso de backup para el prefijo actual.
        Presenta un diálogo con opciones para backup Rsync (Incremental) o Backup Completo (Nuevo con timestamp).
        """
        current_config_name = self.config_manager.configs.get("last_used")
        config = self.config_manager.get_config(current_config_name)

        if not config or "prefix" not in config:
            QMessageBox.warning(self, "No hay prefijo", "No hay un prefijo de Wine/Proton configurado para hacer backup.")
            return

        source_prefix_path = Path(config["prefix"])
        if config.get("steam_appid"):
            steam_compat_data_root = Path.home() / ".local/share/Steam/steamapps/compatdata"
            source_to_backup = steam_compat_data_root / config["steam_appid"]
        else:
            source_to_backup = source_prefix_path

        if not source_to_backup.exists():
            QMessageBox.warning(self, "Prefijo no existe", f"El directorio de origen para backup '{source_to_backup}' no existe.")
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Opciones de Backup")
        msg_box.setText(f"¿Qué tipo de backup deseas realizar para el prefijo '{source_to_backup.name}' de la configuración '{current_config_name}'?")
        msg_box.setIcon(QMessageBox.Question)

        btn_rsync = msg_box.addButton("Rsync (Incremental)", QMessageBox.ActionRole)
        btn_full_backup = msg_box.addButton("Backup Completo (Nuevo)", QMessageBox.ActionRole)
        btn_cancel = msg_box.addButton("Cancelar", QMessageBox.RejectRole)

        msg_box.setDefaultButton(btn_rsync)
        self.config_manager.apply_breeze_style_to_widget(msg_box)

        msg_box.exec_()

        clicked_button = msg_box.clickedButton()

        if clicked_button == btn_rsync:
            destination_path = self._get_backup_destination_path(current_config_name, source_to_backup, is_full_backup=False)
            if not destination_path or not destination_path.is_dir():
                QMessageBox.warning(self, "No hay Backup Completo Previo",
                                    "No se encontró un backup completo previo para realizar un backup incremental para esta configuración. "
                                    "Por favor, realiza un 'Backup Completo (Nuevo)' primero.")
                return
            self._start_backup_process(source_to_backup, destination_path, is_full_backup=False, config_name=current_config_name, prompt_callback=None) # MODIFICACIÓN: Pasar config_name
        elif clicked_button == btn_full_backup:
            destination_path = self._get_backup_destination_path(current_config_name, source_to_backup, is_full_backup=True)
            self._start_backup_process(source_to_backup, destination_path, is_full_backup=True, config_name=current_config_name, prompt_callback=None) # MODIFICACIÓN: Pasar config_name
        elif clicked_button == btn_cancel:
            QMessageBox.information(self, "Backup Cancelado", "La operación de backup ha sido cancelada.")

    def prompt_for_backup(self, callback_func):
        """
        Muestra un diálogo preguntando si se desea hacer un backup antes de una acción.
        Ahora ofrece las mismas opciones (Rsync/Completo) que el backup manual, sin "Cancelar Acción".
        """
        current_config_name = self.config_manager.configs.get("last_used")
        config = self.config_manager.get_config(current_config_name)

        if not config or "prefix" not in config:
            callback_func() # No hay prefijo, continuar sin backup
            return

        source_prefix_path = Path(config["prefix"])
        if config.get("steam_appid"):
            steam_compat_data_root = Path.home() / ".local/share/Steam/steamapps/compatdata"
            source_to_backup = steam_compat_data_root / config["steam_appid"]
        else:
            source_to_backup = source_prefix_path

        if not source_to_backup.exists():
            callback_func() # Prefijo no existe, continuar sin backup
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Realizar Backup Antes de Continuar")
        msg_box.setText(f"Se recomienda realizar un backup del prefijo '{source_to_backup.name}' de la configuración '{current_config_name}' antes de continuar con la operación.")

        btn_rsync = msg_box.addButton("Rsync (Incremental)", QMessageBox.YesRole)
        btn_full_backup = msg_box.addButton("Backup Completo (Nuevo)", QMessageBox.YesRole)
        btn_no_backup = msg_box.addButton("No hacer Backup y Continuar", QMessageBox.NoRole)

        msg_box.setDefaultButton(btn_rsync)
        self.config_manager.apply_breeze_style_to_widget(msg_box)

        msg_box.exec_()

        clicked_button = msg_box.clickedButton()

        if clicked_button == btn_rsync:
            destination_path = self._get_backup_destination_path(current_config_name, source_to_backup, is_full_backup=False)
            if not destination_path or not destination_path.is_dir():
                QMessageBox.warning(self, "No hay Backup Completo Previo",
                                    "No se encontró un backup completo previo para realizar un backup incremental para esta configuración. "
                                    "Por favor, realiza un 'Backup Completo (Nuevo)' primero o selecciona 'No hacer Backup y Continuar'.")
                callback_func() # Continuar con la acción original si el rsync no es posible
                return
            self._start_backup_process(source_to_backup, destination_path, is_full_backup=False, config_name=current_config_name, prompt_callback=callback_func) # MODIFICACIÓN: Pasar config_name
        elif clicked_button == btn_full_backup:
            destination_path = self._get_backup_destination_path(current_config_name, source_to_backup, is_full_backup=True)
            self._start_backup_process(source_to_backup, destination_path, is_full_backup=True, config_name=current_config_name, prompt_callback=callback_func) # MODIFICACIÓN: Pasar config_name
        elif clicked_button == btn_no_backup:
            callback_func() # Continuar con la operación original sin backup

    def _start_backup_process(self, source_to_backup: Path, destination_path: Path, is_full_backup: bool, config_name: str, prompt_callback=None): # MODIFICACIÓN: Añadir config_name
        """Método auxiliar para iniciar el hilo de backup."""
        self.backup_progress_dialog = QProgressDialog("Preparando backup...", "", 0, 100, self)
        self.backup_progress_dialog.setWindowTitle("Progreso del Backup")
        self.backup_progress_dialog.setWindowModality(Qt.WindowModal)
        self.backup_progress_dialog.setCancelButton(None)
        self.backup_progress_dialog.setRange(0, 0)
        self.backup_progress_dialog.setFixedSize(450, 150)
        self.config_manager.apply_breeze_style_to_widget(self.backup_progress_dialog)
        self.backup_progress_dialog.show()

        self.backup_thread = BackupThread(source_to_backup, destination_path, self.config_manager, is_full_backup, config_name) # MODIFICACIÓN: Pasar config_name
        self.backup_thread.progress_update.connect(self.update_backup_progress_dialog)
        if prompt_callback:
            # MODIFICACIÓN: Ajustar el lambda para recibir el nuevo parámetro config_name
            self.backup_thread.finished.connect(lambda success, msg, path, current_conf_name: self.on_prompted_backup_finished(success, msg, path, current_conf_name, prompt_callback))
        else:
            # MODIFICACIÓN: Ajustar el lambda para recibir el nuevo parámetro config_name
            self.backup_thread.finished.connect(lambda success, msg, path, current_conf_name: self.on_manual_backup_finished(success, msg, path, current_conf_name))
        self.backup_thread.start()
        self.update_installation_button_state()

    def on_prompted_backup_finished(self, success: bool, message: str, final_backup_path: str, config_name: str, callback_func): # MODIFICACIÓN: Añadir config_name
        """Callback para backups iniciados por un prompt."""
        self.backup_progress_dialog.close()
        self.backup_thread = None
        self.update_installation_button_state()

        if success:
            QMessageBox.information(self, "Backup Completo", message)
            callback_func()
        else:
            reply = QMessageBox.question(self, "Backup Fallido",
                                         f"{message}\n\n¿Deseas continuar con la operación original a pesar de que el backup falló?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                callback_func()
            else:
                QMessageBox.information(self, "Operación Cancelada", "La operación ha sido cancelada debido a un error en el backup.")

    def update_backup_progress_dialog(self, message: str):
        """Actualiza el progreso del diálogo de backup."""
        self.backup_progress_dialog.setLabelText(f"Backup en progreso...\n{message}")
        QApplication.processEvents()

    def on_manual_backup_finished(self, success: bool, message: str, final_backup_path: str, config_name: str): # MODIFICACIÓN: Añadir config_name
        """Callback para backups iniciados por el botón manual."""
        self.backup_progress_dialog.close()
        self.backup_thread = None
        self.update_installation_button_state()
        if success:
            QMessageBox.information(self, "Backup Completo", message)
        else:
            QMessageBox.critical(self, "Error de Backup", message)

    def open_winetricks(self):
        """Abre la GUI de Winetricks para el prefijo actual."""
        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_open_winetricks())
        else:
            self._continue_open_winetricks()

    def _continue_open_winetricks(self):
        """Abre la GUI de Winetricks para el prefijo actual."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            winetricks_path = self.config_manager.get_winetricks_path()

            # Esto se ejecuta en un subproceso no bloqueante
            subprocess.Popen([winetricks_path, "--gui"], env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) # Redirigir salida a DEVNULL
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Winetricks: {str(e)}")

    def open_shell(self):
        """Abre una terminal (Konsole) con el entorno de Wine/Proton configurado."""
        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_open_shell())
        else:
            self._continue_open_shell()

    def _continue_open_shell(self):
        """Continúa abriendo la terminal después de la posible solicitud de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            # Abre Konsole, heredando el entorno. Puede ser 'xterm', 'gnome-terminal', etc.
            subprocess.Popen(["konsole"], env=env)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la terminal: {str(e)}")

    def open_prefix_folder(self):
        """Abre la carpeta del prefijo de Wine/Proton en el explorador de archivos."""
        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_open_prefix_folder())
        else:
            self._continue_open_prefix_folder()

    def _continue_open_prefix_folder(self):
        """Continúa abriendo la carpeta del prefijo después de la posible solicitud de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config_name)

            if config and "prefix" in config:
                prefix_path = Path(config["prefix"])
                if prefix_path.exists():
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(prefix_path)))
                else:
                    QMessageBox.warning(self, "Advertencia", f"El prefijo '{prefix_path}' no existe. Por favor, asegúrate de que esté configurado o créalo.")
            else:
                QMessageBox.warning(self, "Advertencia", "No hay ningún prefijo configurado para el entorno actual.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la carpeta del prefijo: {str(e)}")

    def open_explorer(self):
        """Ejecuta wine explorer para el prefijo actual."""
        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_open_explorer())
        else:
            self._continue_open_explorer()

    def _continue_open_explorer(self):
        """Continúa abriendo el explorador de Wine después de la posible solicitud de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config_name)

            if config and "prefix" in config:
                prefix_path = Path(config["prefix"])
                if prefix_path.exists():
                    env = self.config_manager.get_current_environment(current_config_name)
                    wine_executable = env.get("WINE")

                    if not wine_executable or not Path(wine_executable).is_file():
                        raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")

                    subprocess.Popen([wine_executable, "explorer"], env=env,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    QMessageBox.warning(self, "Advertencia", f"El prefijo '{prefix_path}' no existe. Por favor, asegúrate de que esté configurado o créalo.")
            else:
                QMessageBox.warning(self, "Advertencia", "No hay ningún prefijo configurado para el entorno actual.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el Explorador de Wine: {str(e)}")

    def open_winecfg(self):
        """Ejecuta winecfg para el prefijo actual."""
        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_open_winecfg())
        else:
            self._continue_open_winecfg()

    def _continue_open_winecfg(self):
        """Continúa abriendo winecfg después de la posible solicitud de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)

            wine_executable = env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")

            subprocess.Popen([wine_executable, "winecfg"], env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Winecfg: {str(e)}")

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