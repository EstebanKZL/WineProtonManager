import sys
import os
import subprocess
import json
import re
import time
import shutil
from pathlib import Path

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

# Importar estilos para aplicar
from styles import STYLE_BREEZE, COLOR_BREEZE_PRIMARY, COLOR_BREEZE_ACCENT

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