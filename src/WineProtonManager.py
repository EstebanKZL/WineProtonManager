#!/usr/bin/env python3
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
from functools import partial # Importar partial para conexiones de señal mas limpias

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QCheckBox, QDialog, QDialogButtonBox,
    QMessageBox, QGroupBox, QComboBox, QLineEdit, QFileDialog,
    QTabWidget, QFormLayout, QScrollArea, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTreeWidget, QTreeWidgetItem, QProgressDialog, QProgressBar,
    QInputDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDir, QSize, QUrl, QTimer
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QDesktopServices

# --- Configuracion de Estilo ---
# Colores centralizados para facil modificacion.
COLOR_PRIMARY = "#3daee9"   # Azul de Steam Deck
COLOR_ACCENT = "#5dbff2"    # Azul mas claro para hover
COLOR_PRESSED = "#2980b9"  # Azul mas oscuro para presionado
COLOR_DISABLED_BG_LIGHT = "#d0d0d0"
COLOR_DISABLED_TEXT_LIGHT = "#9e9e9e"
COLOR_BORDER_LIGHT = "#cccccc"

COLOR_DARK_TEXT = "#FFFFFF"
COLOR_DARK_WINDOW = "#31363b"
COLOR_DARK_WINDOW_TEXT = "#FFFFFF"
COLOR_DARK_BASE = "#232629"
COLOR_DARK_BUTTON = "#40464d"
COLOR_DARK_BUTTON_TEXT = "#FFFFFF"
COLOR_DARK_HIGHLIGHT = "#3daee9" # Tambien Azul de Steam Deck
COLOR_DARK_HIGHLIGHT_TEXT = "#FFFFFF"
COLOR_DARK_BORDER = "#5c636a"

COLOR_LIGHT_WINDOW = "#F7F8F9"
COLOR_LIGHT_WINDOW_TEXT = "#212529"
COLOR_LIGHT_BASE = "#FFFFFF"
COLOR_LIGHT_TEXT = "#212529"
COLOR_LIGHT_BUTTON = "#F7F8F9"
COLOR_LIGHT_BUTTON_TEXT = "#212529"
COLOR_LIGHT_HIGHLIGHT = "#3daee9" # Azul de Steam Deck
COLOR_LIGHT_HIGHLIGHT_TEXT = "#FFFFFF"
COLOR_LIGHT_BORDER = "#BFC4C9"


STYLE_STEAM_DECK = {
    "font": QFont("Noto Sans", 11),
    "title_font": QFont("Noto Sans", 14, QFont.Bold),
    "button_style": f"""
        QPushButton {{
            background-color: {COLOR_PRIMARY};
            color: {COLOR_DARK_TEXT};
            border: 1px solid {COLOR_PRIMARY};
            border-radius: 6px;
            padding: 6px 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_ACCENT};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_DISABLED_BG_LIGHT};
            color: {COLOR_DISABLED_TEXT_LIGHT};
            border: 1px solid {COLOR_BORDER_LIGHT};
        }}
    """,
    "dark_button_style": f"""
        QPushButton {{
            background-color: {COLOR_PRIMARY}; /* Azul tambien en tema oscuro */
            color: {COLOR_DARK_BUTTON_TEXT};
            border: 1px solid {COLOR_PRIMARY}; /* Borde azul tambien en tema oscuro */
            border-radius: 6px;
            padding: 6px 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_ACCENT}; /* Azul mas claro para hover */
        }}
        QPushButton:pressed {{
            background-color: {COLOR_PRESSED}; /* Azul mas oscuro para presionado */
        }}
        QPushButton:disabled {{
            background-color: #555b61; /* Gris para deshabilitado */
            color: #b0b0b0;
            border: 1px solid #6a6f75;
        }}
    """,
    "light_palette": {
        "window": QColor(COLOR_LIGHT_WINDOW),
        "window_text": QColor(COLOR_LIGHT_WINDOW_TEXT),
        "base": QColor(COLOR_LIGHT_BASE),
        "text": QColor(COLOR_LIGHT_TEXT),
        "button": QColor(COLOR_LIGHT_BUTTON),
        "button_text": QColor(COLOR_LIGHT_BUTTON_TEXT),
        "highlight": QColor(COLOR_LIGHT_HIGHLIGHT),
        "highlight_text": Qt.white
    },
    "dark_palette": {
        "window": QColor(COLOR_DARK_WINDOW),
        "window_text": QColor(COLOR_DARK_WINDOW_TEXT),
        "base": QColor(COLOR_DARK_BASE),
        "text": QColor(COLOR_DARK_TEXT),
        "button": QColor(COLOR_DARK_BUTTON),
        "button_text": QColor(COLOR_DARK_BUTTON_TEXT),
        "highlight": QColor(COLOR_DARK_HIGHLIGHT),
        "highlight_text": Qt.white
    },
    "table_style": f"""
        QTableWidget {{
            background-color: {COLOR_LIGHT_BASE};
            alternate-background-color: #f9f9fa;
            gridline-color: #d0d0d0;
            border: 1px solid #c4c9cc;
        }}
        QTableWidget::item {{
            padding: 6px;
        }}
        QTableWidget::item:selected {{
            background-color: {COLOR_PRIMARY};
            color: white;
        }}
        QHeaderView::section {{
            background-color: #f1f3f4;
            padding: 8px;
            border: 1px solid #c4c9cc;
            font-weight: bold;
        }}
    """,
    "dark_table_style": f"""
        QTableWidget {{
            background-color: {COLOR_DARK_WINDOW};
            alternate-background-color: #2b3035;
            gridline-color: #555b61;
            border: 1px solid {COLOR_DARK_BORDER};
        }}
        QTableWidget::item {{
            padding: 6px;
            color: {COLOR_DARK_TEXT};
        }}
        QTableWidget::item:selected {{
            background-color: {COLOR_PRIMARY};
            color: white;
        }}
        QHeaderView::section {{
            background-color: {COLOR_DARK_BUTTON};
            padding: 8px;
            border: 1px solid {COLOR_DARK_BORDER};
            font-weight: bold;
            color: {COLOR_DARK_TEXT};
        }}
    """,
    "groupbox_style": f"""
        QGroupBox {{
            border: 1px solid {COLOR_LIGHT_BORDER};
            border-radius: 6px;
            margin-top: 20px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            font-weight: bold;
            color: {COLOR_LIGHT_WINDOW_TEXT};
        }}
    """,
    "dark_groupbox_style": f"""
        QGroupBox {{
            border: 1px solid {COLOR_DARK_BORDER};
            border-radius: 6px;
            margin-top: 20px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            font-weight: bold;
            color: {COLOR_DARK_TEXT};
        }}
    """
}

# Deshabilitar verificacion SSL para casos especificos (descargas, APIs).
# Esto debe usarse con precaucion, solo si las fuentes son de confianza.
ssl._create_default_https_context = ssl._create_unverified_context

class ConfigManager:
    """
    Gestor optimizado para configuraciones persistentes, incluyendo rutas, temas y repositorios.
    Asegura la estructura basica de configuracion al inicio.
    """
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "WineProtonManager"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_dir = self.config_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.wine_download_dir = self.config_dir / "Wine"
        self.proton_download_dir = self.config_dir / "Proton"
        self.wine_download_dir.mkdir(exist_ok=True)
        self.proton_download_dir.mkdir(exist_ok=True)
        self.programs_dir = self.config_dir / "Programas"
        self.programs_dir.mkdir(exist_ok=True)
        
        self.configs = self._load_configs()
        self._ensure_default_config()

    def _ensure_default_config(self):
        """Asegura que existan configuraciones basicas, inicializandolas si faltan."""
        default_settings = {
            "winetricks_path": str(Path(__file__).parent / "AppDir" / "usr" / "bin" / "winetricks"),
            "config_path": str(self.config_file),
            "theme": "dark",
            "window_size": [900, 650],
            "silent_install": True, # Global silent install for winetricks components
            "force_winetricks_install": False # New setting for --force
        }
        
        default_repositories = {
            "proton": [
                {"name": "GloriousEggroll Proton", "url": "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases", "enabled": True}
            ],
            "wine": [
                {"name": "Kron4ek Wine Builds", "url": "https://api.github.com/repos/Kron4ek/Wine-Builds/releases", "enabled": True}
            ]
        }

        # Usar setdefault para evitar sobrescribir si ya existen
        self.configs.setdefault("configs", {})
        self.configs.setdefault("last_used", "Wine-System")
        self.configs.setdefault("settings", default_settings)
        self.configs.setdefault("repositories", default_repositories)
        self.configs.setdefault("custom_programs", []) # Asegurar que custom_programs exista

        # Merge default settings, but keep existing values if they are present
        for key, value in default_settings.items():
            self.configs["settings"].setdefault(key, value)

        if "Wine-System" not in self.configs["configs"]:
            self.configs["configs"]["Wine-System"] = {
                "type": "wine",
                "prefix": str(Path.home() / ".wine"),
                "arch": "win64"
            }
            
        self.save_configs()

    def _load_configs(self):
        """Carga las configuraciones desde el archivo JSON. Devuelve un diccionario vacio si falla o no existe."""
        if not self.config_file.exists():
            return {}
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error cargando el archivo de configuracion {self.config_file}: {e}. Se usara la configuracion por defecto.")
            return {}

    def save_configs(self):
        """Guarda las configuraciones en el archivo JSON con manejo de errores."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error guardando el archivo de configuracion {self.config_file}: {e}")

    def get_config(self, config_name: str) -> dict | None:
        """Obtiene una configuracion especifica por nombre."""
        return self.configs.get("configs", {}).get(config_name)

    def get_current_environment(self, config_name: str) -> dict:
        """
        Obtiene las variables de entorno para la configuracion dada.
        Valida la existencia de los ejecutables clave de Wine/Proton.
        """
        config = self.get_config(config_name)
        if not config:
            raise ValueError(f"Configuracion '{config_name}' no encontrada.")

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

            env["PROTON_DIR"] = str(proton_dir)
            version_file = proton_dir / "version"
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    env["PROTON_VERSION"] = f.read().strip()
            
            try:
                result = subprocess.run([wine_executable, "--version"], env=env, capture_output=True, text=True, check=True, timeout=5)
                env["WINE_VERSION_IN_PROTON"] = result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                env["WINE_VERSION_IN_PROTON"] = "N/A (Error obteniendo version o tiempo de espera agotado)"

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
                    env["WINE_VERSION"] = "N/A (Error obteniendo version o tiempo de espera agotado)"
            else: # Usar Wine del sistema
                try:
                    # Comprobar si el comando 'wine' existe en PATH
                    subprocess.run(["which", "wine"], capture_output=True, text=True, check=True, timeout=5)
                    # Obtener version de wine
                    result = subprocess.run(["wine", "--version"], capture_output=True, text=True, check=True, timeout=5)
                    env["WINE_VERSION"] = result.stdout.strip()
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    env["WINE_VERSION"] = "N/A (Wine no encontrado en el sistema o version no detectable)"
        
        # Actualizar PATH solo si hay una ruta especifica
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
        # Asegurar que todos los programas tengan un tipo, para compatibilidad
        for program in programs:
            program.setdefault("type", "winetricks") # 'winetricks' como tipo por defecto
        return programs
        
    def add_custom_program(self, program_info: dict):
        """Anade un programa personalizado a la configuracion."""
        # Se asume que las validaciones de duplicados se hacen en la GUI antes de llamar a esto.
        # Aqui solo se anade al diccionario y se guarda.
        self.configs.setdefault("custom_programs", []).append(program_info)
        self.save_configs()

    def set_theme(self, theme: str):
        """Establece el tema (claro/oscuro) y guarda la configuracion."""
        self.configs.setdefault("settings", {})["theme"] = theme
        self.save_configs()

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
            
        return "winetricks" # Fallback al comando del sistema

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
            QMessageBox.warning(None, "Ruta Invalida", "La ruta de Winetricks no es valida o no existe.")
            return False

    def set_silent_install(self, enabled: bool):
        """Establece si la instalacion silenciosa esta habilitada y guarda la configuracion."""
        self.configs.setdefault("settings", {})["silent_install"] = enabled
        self.save_configs()
        
    def get_silent_install(self) -> bool:
        """Obtiene si la instalacion silenciosa esta habilitada. Por defecto es True."""
        return self.configs.get("settings", {}).get("silent_install", True)
    
    def set_force_winetricks_install(self, enabled: bool):
        """Establece si la instalacion forzada de Winetricks esta habilitada y guarda la configuracion."""
        self.configs.setdefault("settings", {})["force_winetricks_install"] = enabled
        self.save_configs()

    def get_force_winetricks_install(self) -> bool:
        """Obtiene si la instalacion forzada de Winetricks esta habilitada. Por defecto es False."""
        return self.configs.get("settings", {}).get("force_winetricks_install", False)

    def delete_config(self, config_name: str) -> bool:
        """Elimina una configuracion guardada, ajustando 'last_used' si es necesario."""
        if config_name in self.configs.get("configs", {}):
            del self.configs["configs"][config_name]
            if self.configs["last_used"] == config_name:
                self.configs["last_used"] = "Wine-System" if "Wine-System" in self.configs["configs"] else ""
            self.save_configs()
            return True
        return False

    def get_installed_winetricks(self, prefix_path: str) -> list[str]:
        """Obtiene la lista de componentes de winetricks instalados en un prefijo."""
        # Se asume que el registro de wineprotonmanager anota las instalaciones
        # en el formato "installed <component_name>" o "installed <exe_filename>".
        wineprotonmanager_log = Path(prefix_path) / "wineprotonmanager.log"
        installed = set()
        if wineprotonmanager_log.exists():
            try:
                with open(wineprotonmanager_log, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        match = re.search(r"installed\s+(\S+)", line)
                        if match:
                            installed.add(match.group(1))
            except Exception as e:
                print(f"Error leyendo el registro de winetricks: {e}")
        return list(installed)

    def save_window_size(self, size: QSize):
        """Guarda el tamano de la ventana."""
        self.configs.setdefault("settings", {})["window_size"] = [size.width(), size.height()]
        self.save_configs()
        
    def get_window_size(self) -> QSize:
        """Obtiene el tamano de ventana guardado. Por defecto es 900x650."""
        size = self.configs.get("settings", {}).get("window_size", [900, 650])
        return QSize(size[0], size[1])
        
    def get_log_path(self, program_name: str) -> Path:
        """Obtiene la ruta al archivo de registro para un programa especifico."""
        current_config_name = self.configs.get("last_used", "default")
        log_sub_dir = self.log_dir / current_config_name
        log_sub_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r'[^\w\-_.]', '_', program_name)
        return log_sub_dir / f"{safe_name}.log"
        
    def write_to_log(self, program_name: str, message: str):
        """Escribe un mensaje con marca de tiempo en el registro del programa."""
        log_path = self.get_log_path(program_name)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except IOError as e:
            print(f"Error escribiendo en el log {log_path}: {e}")
            
    def get_repositories(self, type_: str) -> list[dict]:
        """Obtiene repositorios para Wine o Proton."""
        return self.configs.get("repositories", {}).get(type_, [])
        
    def add_repository(self, type_: str, name: str, url: str) -> bool:
        """Anade un nuevo repositorio, evitando duplicados."""
        repos = self.configs.setdefault("repositories", {}).setdefault(type_, [])
        if not any(r["url"] == url for r in repos):
            repos.append({"name": name, "url": url, "enabled": True})
            self.save_configs()
            return True
        return False
        
    def delete_repository(self, type_: str, index: int) -> bool:
        """Elimina un repositorio por indice."""
        if "repositories" in self.configs and type_ in self.configs["repositories"]:
            if 0 <= index < len(self.configs["repositories"][type_]):
                del self.configs["repositories"][type_][index]
                self.save_configs()
                return True
        return False
        
    def toggle_repository(self, type_: str, index: int, enabled: bool) -> bool:
        """Habilita/deshabilita un repositorio por indice."""
        if "repositories" in self.configs and type_ in self.configs["repositories"]:
            if 0 <= index < len(self.configs["repositories"][type_]):
                self.configs["repositories"][type_][index]["enabled"] = enabled
                self.save_configs()
                return True
        return False

    def apply_theme_to_dialog(self, dialog: QDialog | QFileDialog):
        """Aplica el tema actual (claro/oscuro) a un dialogo de Qt."""
        theme = self.get_theme()
        palette = QPalette()
        if theme == "dark":
            palette.setColor(QPalette.Window, STYLE_STEAM_DECK["dark_palette"]["window"])
            palette.setColor(QPalette.WindowText, STYLE_STEAM_DECK["dark_palette"]["window_text"])
            palette.setColor(QPalette.Base, STYLE_STEAM_DECK["dark_palette"]["base"])
            palette.setColor(QPalette.Text, STYLE_STEAM_DECK["dark_palette"]["text"])
            palette.setColor(QPalette.Button, STYLE_STEAM_DECK["dark_palette"]["button"])
            palette.setColor(QPalette.ButtonText, STYLE_STEAM_DECK["dark_palette"]["button_text"])
            palette.setColor(QPalette.Highlight, STYLE_STEAM_DECK["dark_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, STYLE_STEAM_DECK["dark_palette"]["highlight_text"])
        else:
            palette = QApplication.style().standardPalette()
        dialog.setPalette(palette)
        # Asegurar que los botones en QFileDialog tambien usen el estilo
        for btn in dialog.findChildren(QPushButton):
            btn.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme == "dark" else STYLE_STEAM_DECK["button_style"])

# --- Hilos de Operacion ---
class DownloadThread(QThread):
    progress = pyqtSignal(int) # % de progreso
    finished = pyqtSignal(str) # Ruta al archivo descargado
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
            with urlopen(req, timeout=30) as response: # Anadido tiempo de espera para urlopen
                if response.getcode() != 200:
                    raise HTTPError(self.url, response.getcode(), response.reason, response.headers, None)
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192
                
                # Pre-comprobacion de espacio en disco
                free_space = shutil.disk_usage(self.destination.parent).free
                # Estimacion conservadora: se necesita al menos el doble del tamano del archivo.
                # Puede ajustarse si se sabe mas sobre la compresion.
                required_space = total_size * 2 if total_size > 0 else 500 * 1024 * 1024 # 500MB si es desconocido
                
                if free_space < required_space:
                    raise IOError(f"Espacio en disco insuficiente en {self.destination.parent}. Requerido: {required_space / (1024*1024):.1f} MB, Disponible: {free_space / (1024*1024):.1f} MB")

                # Eliminar archivo parcial si existe para evitar conflictos
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
                
                if not self._is_running: # Si se detuvo a mitad de la descarga
                    if self.destination.exists():
                        try:
                            self.destination.unlink()
                        except OSError:
                            pass # Ignorar errores durante la limpieza
                    self.config_manager.write_to_log(self.name, f"Descarga de {self.name} cancelada.")
                    return # Salir del hilo limpiamente
                
                self.finished.emit(str(self.destination))
                self.config_manager.write_to_log(self.name, f"Descarga de {self.name} completada.")
                
        except HTTPError as e:
            msg = f"Error HTTP descargando {self.url}: {e.code} - {e.reason}"
            self.config_manager.write_to_log(self.name, f"ERROR: {msg}")
            self.error.emit(msg)
        except Exception as e:
            msg = f"Error inesperado durante la descarga de {self.name}: {str(e)}"
            self.config_manager.write_to_log(self.name, f"ERROR: {msg}")
            if self.destination.exists():
                try:
                    self.destination.unlink() # Limpiar archivo parcial
                except OSError:
                    pass # Ignorar errores durante la limpieza
            self.error.emit(msg)
            
    def stop(self):
        self._is_running = False

class DecompressionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int) # Puede implementarse para un progreso mas granular
    
    def __init__(self, archive_path: str, config_manager: ConfigManager, name: str):
        super().__init__()
        self.archive_path = Path(archive_path)
        self.config_manager = config_manager
        self.name = name
        self.target_dir = None
        self._is_running = True

    def _set_permissions_recursively(self, path: Path):
        """Aplica permisos 0o755 (rwx para propietario, rx para grupo/otros) recursivamente."""
        if not path.exists():
            return
            
        try:
            # Otorgar permisos de ejecucion para archivos y directorios
            if path.is_dir():
                os.chmod(path, 0o755)
                for item in path.iterdir():
                    self._set_permissions_recursively(item)
            elif path.is_file():
                # Asegurarse de que sea ejecutable si 'bin' esta en su ruta
                if "bin" in path.parts or "wine" in path.name.lower() or "wineserver" in path.name.lower():
                    os.chmod(path, 0o755)
                else: # Archivos normales
                    os.chmod(path, 0o644) # rw-r--r--
        except OSError as e:
            self.config_manager.write_to_log(self.name, f"Advertencia: No se pudieron establecer permisos en {path}: {e}")

    def run(self):
        self.config_manager.write_to_log(self.name, f"Iniciando descompresion de {self.archive_path}")
        try:
            if not self.archive_path.exists():
                raise FileNotFoundError(f"El archivo {self.archive_path} no existe.")

            dest_dir_root = self.archive_path.parent # Directorio donde se guardara Wine/Proton
            
            # Identificar el nombre base para el directorio de destino
            # Ejemplo: proton-ge-8-25.tar.gz -> proton-ge-8-25
            base_name = self.archive_path.stem
            if self.archive_path.suffix in ['.gz', '.xz', '.zip']:
                base_name = Path(base_name).stem # Eliminar el segundo sufijo si es tar.gz/tar.xz
            
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
                elif self.archive_path.suffix in ['.gz', '.xz', '.bz2', '.zst'] or self.archive_path.name.endswith(('.tar.gz', '.tar.xz')):
                    # Manejar multiples formatos tar
                    mode = "r:" + self.archive_path.suffix[1:] # e.g., ".gz" -> "r:gz"
                    if self.archive_path.name.endswith('.tar.gz'):
                        mode = "r:gz"
                    elif self.archive_path.name.endswith('.tar.xz'):
                        mode = "r:xz"
                    
                    with tarfile.open(self.archive_path, mode) as tar:
                        tar.extractall(path=temp_unzip_dir, filter='data') # Usar filter='data' por seguridad
                else:
                    raise ValueError(f"Formato de archivo no compatible para descompresion: {self.archive_path.suffix}")

                # Encontrar el directorio principal dentro del archivo (comun en lanzamientos de Proton/Wine)
                # Si solo hay un directorio en la raiz de temp_unzip_dir, mover ese directorio
                extracted_contents = list(temp_unzip_dir.iterdir())
                if len(extracted_contents) == 1 and extracted_contents[0].is_dir():
                    source_dir_to_move = extracted_contents[0]
                else:
                    source_dir_to_move = temp_unzip_dir # Mover todo el contenido del directorio temporal

                # Mover el contenido extraido al destino final
                self.config_manager.write_to_log(self.name, f"Moviendo {source_dir_to_move} a {self.target_dir}")
                shutil.move(str(source_dir_to_move), str(self.target_dir))
                
                # Establecer permisos despues de mover, si el sistema de archivos lo soporta
                self._set_permissions_recursively(self.target_dir)

            # Eliminar archivo comprimido despues de una descompresion exitosa
            try:
                self.archive_path.unlink()
                self.config_manager.write_to_log(self.name, f"Archivo comprimido {self.archive_path} eliminado.")
            except OSError as e:
                self.config_manager.write_to_log(self.name, f"Advertencia: No se pudo eliminar el archivo comprimido {self.archive_path}: {e}")

            self.finished.emit(str(self.target_dir))
            self.config_manager.write_to_log(self.name, f"Descompresion de {self.name} completada. Ruta: {self.target_dir}")

        except Exception as e:
            msg = f"Error descomprimiendo {self.name}: {str(e)}"
            self.config_manager.write_to_log(self.name, f"ERROR: {msg}")
            if self.target_dir and self.target_dir.exists():
                try:
                    shutil.rmtree(self.target_dir, ignore_errors=True)
                    self.config_manager.write_to_log(self.name, f"Directorio incompleto {self.target_dir} eliminado despues del error.")
                except OSError as cleanup_error:
                    self.config_manager.write_to_log(self.name, f"Error limpiando {self.target_dir}: {cleanup_error}")
            self.error.emit(msg)

    def stop(self):
        self._is_running = False

class InstallerThread(QThread):
    progress = pyqtSignal(str, str) # (item_name: str, status: str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    canceled = pyqtSignal(str) # Nombre del item que fue cancelado
    
    def __init__(self, items_to_install: list[tuple[str, str, str]], env: dict, silent_mode: bool, force_mode: bool, winetricks_path: str, config_manager: ConfigManager):
        # IMPORTANT: items_to_install needs to be modified to include the 'name'
        # It should now be a list of tuples: (path_to_exe_or_winetricks_name, type_str, user_defined_name)
        super().__init__()
        self.items_to_install = items_to_install
        self.env = env
        self.silent_mode = silent_mode
        self.force_mode = force_mode 
        self.winetricks_path = winetricks_path
        self.config_manager = config_manager
        self._is_running = True
        self.current_process = None

    def run(self):
        try:
            self._check_konsole_availability()
        except EnvironmentError as e:
            self.error.emit(str(e))
            return

        # Iterate through the new tuple format: (path_or_name, type, user_name)
        for idx, (item_path_or_name, item_type, user_defined_name) in enumerate(self.items_to_install):
            if not self._is_running:
                # Use user_defined_name for canceled signal as well
                self.canceled.emit(user_defined_name)
                break
            
            # Use the user_defined_name consistently for all progress updates and logging
            display_name_for_progress = user_defined_name

            self.progress.emit(display_name_for_progress, f"{display_name_for_progress}: Instalando...")
            self.config_manager.write_to_log(display_name_for_progress, f"Iniciando instalacion: {item_path_or_name} (Tipo: {item_type}, Silencioso: {self.silent_mode}, Forzado: {self.force_mode})")
            
            temp_log_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as temp_log_file:
                    temp_log_path = Path(temp_log_file.name)
                
                if item_type == "exe":
                    self._install_exe(item_path_or_name, temp_log_path, display_name_for_progress)
                elif item_type == "winetricks":
                    self._install_winetricks(item_path_or_name, temp_log_path, display_name_for_progress)
                elif item_type == "wtr": 
                    self._install_winetricks_script(item_path_or_name, temp_log_path, display_name_for_progress)
                else:
                    raise ValueError(f"Tipo de instalacion no reconocido: {item_type}")
                
                self._register_successful_installation(display_name_for_progress)
                self.progress.emit(display_name_for_progress, f"{display_name_for_progress}: Finalizado")
                self.config_manager.write_to_log(display_name_for_progress, f"Instalacion de {display_name_for_progress} completada exitosamente.")
                
            except Exception as e:
                self._handle_installation_error(e, display_name_for_progress, temp_log_path)
                break 
            finally:
                if temp_log_path and temp_log_path.exists():
                    try:
                        temp_log_path.unlink()
                        retcode_file = Path(str(temp_log_path) + ".retcode")
                        if retcode_file.exists():
                            retcode_file.unlink()
                    except OSError as e:
                        self.config_manager.write_to_log(display_name_for_progress, f"Advertencia: No se pudo eliminar el archivo temporal {temp_log_path}: {e}")

        self.finished.emit()

    def _check_konsole_availability(self):
        """Comprueba si Konsole esta disponible."""
        try:
            subprocess.run(["which", "konsole"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            raise EnvironmentError(
                "Konsole no esta instalado o no se encuentra en PATH. "
                "Es necesario para mostrar la consola de instalacion. "
                "Puedes instalarlo con: sudo apt install konsole"
            )

    def _install_exe(self, exe_path: str, temp_log_path: Path, display_name: str):
        """Ejecuta un archivo .exe usando Wine/Proton en una nueva ventana de Konsole."""
        exe_path = Path(exe_path)
        if not exe_path.exists():
            raise FileNotFoundError(f"El archivo EXE no existe: {exe_path}")
            
        wine_executable = self.env.get("WINE")
        if not wine_executable or not Path(wine_executable).is_file():
            raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")

        cmd = [
            "nohup", "konsole",
            "--nofork",
            "-e",
            "bash", "-c",
            f"'{wine_executable}' '{exe_path}' 2>&1 | tee '{temp_log_path}'; echo $? > '{temp_log_path}.retcode'; exit"
        ]
        
        self.config_manager.write_to_log(display_name, f"Comando EXE: {' '.join(cmd)}")
        self._execute_command_in_konsole(cmd, display_name, temp_log_path)

    def _install_winetricks(self, component_name: str, temp_log_path: Path, display_name: str):
        """Ejecuta un comando de winetricks en una nueva ventana de Konsole."""
        winetricks_executable = self.winetricks_path
        if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
            raise FileNotFoundError(f"Ejecutable de Winetricks no encontrado: {winetricks_executable}")

        silent_flag = "-q" if self.silent_mode else ""
        force_flag = "--force" if self.force_mode else "" 

        cmd = [
            "nohup", "konsole",
            "--nofork",
            "-e",
            "bash", "-c",
            f"'{winetricks_executable}' {silent_flag} {force_flag} '{component_name}' 2>&1 | tee '{temp_log_path}'; echo $? > '{temp_log_path}.retcode'; exit"
        ]
        cmd = [c for c in cmd if c]
        
        self.config_manager.write_to_log(display_name, f"Comando Winetricks: {' '.join(cmd)}")
        self._execute_command_in_konsole(cmd, display_name, temp_log_path)

    def _install_winetricks_script(self, script_path: str, temp_log_path: Path, display_name: str):
        """Ejecuta un script personalizado de Winetricks (.wtr) en una nueva ventana de Konsole."""
        script_path = Path(script_path)
        if not script_path.exists():
            raise FileNotFoundError(f"El archivo de script de Winetricks no existe: {script_path}")

        winetricks_executable = self.winetricks_path
        if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
            raise FileNotFoundError(f"Ejecutable de Winetricks no encontrado: {winetricks_executable}")
            
        silent_flag = "-q" if self.silent_mode else "" 
        force_flag = "--force" if self.force_mode else "" 

        cmd = [
            "nohup", "konsole",
            "--nofork",
            "-e",
            "bash", "-c",
            f"'{winetricks_executable}' {silent_flag} {force_flag} '{script_path}' 2>&1 | tee '{temp_log_path}'; echo $? > '{temp_log_path}.retcode'; exit"
        ]
        cmd = [c for c in cmd if c]
        
        self.config_manager.write_to_log(display_name, f"Comando de script Winetricks: {' '.join(cmd)}")
        self._execute_command_in_konsole(cmd, display_name, temp_log_path)

    def _execute_command_in_konsole(self, cmd: list[str], display_name: str, temp_log_path: Path):
        """Ejecuta un comando y espera su finalizacion, procesando el codigo de retorno."""
        self.current_process = subprocess.Popen(
            cmd,
            env=self.env,
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setpgrp 
        )
        self.current_process.wait()

        return_code_file = Path(str(temp_log_path) + ".retcode")
        retcode = -1 
        if return_code_file.exists():
            try:
                with open(return_code_file, 'r') as f:
                    retcode = int(f.read().strip())
            except Exception as e:
                self.config_manager.write_to_log(display_name, f"Advertencia: No se pudo leer el codigo de retorno del subshell: {e}")

        log_content = ""
        if temp_log_path.exists():
            try:
                with open(temp_log_path, 'r', encoding='utf-8', errors='replace') as f:
                    log_content = f.read()
            except Exception as e:
                self.config_manager.write_to_log(display_name, f"Advertencia: No se pudo leer el log temporal {temp_log_path}: {e}")
        
        self.config_manager.write_to_log(display_name, "=== INICIO DEL LOG DEL PROCESO ===")
        self.config_manager.write_to_log(display_name, log_content)
        self.config_manager.write_to_log(display_name, f"Codigo de retorno del proceso: {retcode}")
        self.config_manager.write_to_log(display_name, "=== FIN DEL LOG DEL PROCESO ===\n")

        if retcode != 0:
            raise subprocess.CalledProcessError(retcode, cmd, output=log_content)

    def _register_successful_installation(self, display_name: str):
        """Registra una instalacion exitosa en el log del prefijo."""
        prefix_path = Path(self.env["WINEPREFIX"])
        log_file = prefix_path / "wineprotonmanager.log"
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} installed {display_name}\n")
        except IOError as e:
            self.config_manager.write_to_log(display_name, f"Advertencia: No se pudo escribir en el log del prefijo {log_file}: {e}")

    def _handle_installation_error(self, error: Exception, display_name: str, temp_log_path: Path | None):
        """Maneja y notifica errores durante la instalacion."""
        error_msg = f"Error instalando {display_name}:\n"
        if isinstance(error, subprocess.CalledProcessError):
            error_msg += f"Comando fallido: {' '.join(error.cmd)}\nCodigo de Salida: {error.returncode}\nSalida/Error: {error.output or error.stderr}"
        else:
            error_msg += str(error)
            
        self.config_manager.write_to_log(display_name, f"ERROR DURANTE LA INSTALACION: {error_msg}")
        self.progress.emit(display_name, f"{display_name}: Error") # Actualizar estado en GUI
        self.error.emit(f"Error fatal durante la instalacion de {display_name}. "
                        f"Consulta el registro para mas detalles: {self.config_manager.get_log_path(display_name)}\n"
                        f"Mensaje de error: {str(error)}")
            
    def stop(self):
        """Detiene la instalacion, incluyendo el proceso de Konsole."""
        self._is_running = False
        if self.current_process and self.current_process.poll() is None:
            try:
                os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGINT)
                self.current_process.wait(timeout=2)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGTERM)
                    self.current_process.wait(timeout=2)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    try:
                        os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGKILL)
                    except ProcessLookupError:
                        pass

# --- Dialogos de Aplicacion ---
class ConfigDialog(QDialog):
    config_saved = pyqtSignal()
    
    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Configuracion de Entorno")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.apply_steamdeck_style()
        self.load_configs() # Cargar configuraciones aqui para asegurar que la lista este poblada

    def apply_steamdeck_style(self):
        self.setFont(STYLE_STEAM_DECK["font"]) # Aplicar fuente de estilo global a todo el dialogo.
        theme = self.config_manager.get_theme()
        
        # 1. Iterar sobre todos los widgets hijos para aplicar estilos generales
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                # Aplicar el estilo de boton correcto (azul en oscuro, etc.)
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme == "dark" else STYLE_STEAM_DECK["button_style"])
                widget.setFont(STYLE_STEAM_DECK["font"]) # Asegurar que el texto del boton tenga la fuente
            elif isinstance(widget, QGroupBox):
                widget.setFont(STYLE_STEAM_DECK["title_font"]) # Titulo de grupo en negrita
                # Aplicar el estilo de grupo correcto (bordes, color de titulo)
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_groupbox_style"] if theme == "dark" else STYLE_STEAM_DECK["groupbox_style"])
            elif isinstance(widget, QLabel):
                widget.setFont(STYLE_STEAM_DECK["font"]) # Asegurar que las etiquetas tambien tengan la fuente
            elif isinstance(widget, QComboBox) or isinstance(widget, QLineEdit):
                widget.setFont(STYLE_STEAM_DECK["font"]) # Asegurar que combos y lineedits tengan la fuente
        
        # 2. Aplicar estilo especifico para QListWidgets (listas de repositorios y versiones)
        # Esto ya incluye negrita y tamano consistente.
        list_style_template = """
            QListWidget {{
                background-color: {};
                color: {};
                border: 1px solid {};
                font-size: {}px; /* Aumentaremos este valor */
                font-weight: bold; /* Letra en negrita */
            }}
            QListWidget::item {{
                padding: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {};
                color: white;
            }}
        """

        # Aumentamos el tamano de la fuente base para las listas.
        # Por ejemplo, si STYLE_STEAM_DECK["font"] es 10, podemos usar 12 o 13 para las listas.
        base_font_size = STYLE_STEAM_DECK["font"].pointSize()
        list_font_size = base_font_size + 6 # Aumentar en 2 puntos, ajusta si es necesario.

        if theme == "dark":
            list_bg = COLOR_DARK_WINDOW
            list_text = COLOR_DARK_TEXT
            list_border = COLOR_DARK_BORDER
            list_highlight = COLOR_PRIMARY
        else:
            list_bg = COLOR_LIGHT_BASE
            list_text = COLOR_LIGHT_TEXT
            list_border = COLOR_LIGHT_BORDER
            list_highlight = COLOR_PRIMARY

        unified_list_style = list_style_template.format(
            list_bg, list_text, list_border, list_font_size, list_highlight # Usar list_font_size aqui
        )

        self.list_repos_proton.setStyleSheet(unified_list_style)
        self.list_repos_wine.setStyleSheet(unified_list_style)
        self.list_versions_proton.setStyleSheet(unified_list_style)
        self.list_versions_wine.setStyleSheet(unified_list_style)
        
        # La lista principal de configuracion podria tener otro estilo si se desea,
        # pero aqui la mantenemos con el estilo de tabla para consistencia con QTableWidget
        self.list_config.setStyleSheet(STYLE_STEAM_DECK["dark_table_style"] if theme == "dark" else STYLE_STEAM_DECK["table_style"])


    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        self.current_tab = QWidget()
        self.setup_current_config_tab()
        self.tabs.addTab(self.current_tab, "Configuraciones Guardadas")

        self.new_tab = QWidget()
        self.setup_new_config_tab()
        self.tabs.addTab(self.new_tab, "Crear/Editar Configuracion")

        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Ajustes Generales")

        self.downloads_tab = QWidget()
        self.setup_downloads_tab()
        self.tabs.addTab(self.downloads_tab, "Descargas de Versiones")

        layout.addWidget(self.tabs)
        
        # Botones en la parte inferior del dialogo
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.button(QDialogButtonBox.Close).setAutoDefault(False)
        self.button_box.accepted.connect(self.accept) # Conectar OK si es necesario, pero Close es mas apropiado para ConfigDialog
        self.button_box.rejected.connect(self.reject)
        self.button_box.clicked.connect(self.close) # Usar clicked para Close
        layout.addWidget(self.button_box)
        
        self.setLayout(layout)

    def setup_current_config_tab(self):
        layout = QVBoxLayout()
        self.list_config = QListWidget()
        self.list_config.itemDoubleClicked.connect(self.edit_config)
        self.list_config.itemSelectionChanged.connect(self.update_displayed_config_info)
        layout.addWidget(self.list_config)

        btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("Eliminar Configuracion")
        self.btn_delete.setAutoDefault(False)
        self.btn_delete.clicked.connect(self.delete_config)
        btn_layout.addWidget(self.btn_delete)

        self.btn_set_default = QPushButton("Establecer por Defecto")
        self.btn_set_default.setAutoDefault(False)
        self.btn_set_default.clicked.connect(self.set_default_config)
        btn_layout.addWidget(self.btn_set_default)

        layout.addLayout(btn_layout)

        self.lbl_config_info = QLabel("Selecciona una configuracion para ver los detalles")
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

        self.wine_directory = QLineEdit()
        self.btn_wine = QPushButton("Explorar...")
        self.btn_wine.setAutoDefault(False)
        self.btn_wine.clicked.connect(self.browse_wine)
        wine_layout = QHBoxLayout()
        wine_layout.addWidget(self.wine_directory)
        wine_layout.addWidget(self.btn_wine)

        self.wine_group = QGroupBox("Configuracion de Wine Personalizada")
        wine_inner_layout = QFormLayout()
        wine_inner_layout.addRow("Directorio de instalacion de Wine:", wine_layout)
        self.wine_group.setLayout(wine_inner_layout)

        self.proton_directory = QLineEdit()
        self.btn_proton = QPushButton("Explorar...")
        self.btn_proton.setAutoDefault(False)
        self.btn_proton.clicked.connect(self.browse_proton)
        proton_layout = QHBoxLayout()
        proton_layout.addWidget(self.proton_directory)
        proton_layout.addWidget(self.btn_proton)

        self.proton_group = QGroupBox("Configuracion de Proton Personalizada")
        proton_inner_layout = QFormLayout()
        proton_inner_layout.addRow("Directorio de instalacion de Proton:", proton_layout)
        self.proton_group.setLayout(proton_inner_layout)

        layout.addRow(self.wine_group)
        layout.addRow(self.proton_group)
        
        buttons_layout = QHBoxLayout()
        self.btn_test = QPushButton("Probar Configuracion")
        self.btn_test.setAutoDefault(False)
        self.btn_test.clicked.connect(self.test_configuration)
        buttons_layout.addWidget(self.btn_test)
        
        self.btn_save_config = QPushButton("Guardar Configuracion")
        self.btn_save_config.setAutoDefault(False)
        self.btn_save_config.clicked.connect(self.save_new_config)
        buttons_layout.addWidget(self.btn_save_config)
        layout.addRow(buttons_layout)

        self.update_config_field_visibility() # Inicializar visibilidad
        self.new_tab.setLayout(layout)

    def setup_downloads_tab(self):
        layout = QVBoxLayout()
        
        self.download_tabs = QTabWidget()
        
        self.proton_tab = QWidget()
        self.setup_proton_download_tab()
        self.download_tabs.addTab(self.proton_tab, "Proton")
        
        self.wine_tab = QWidget()
        self.setup_wine_download_tab()
        self.download_tabs.addTab(self.wine_tab, "Wine")
        
        layout.addWidget(self.download_tabs)
        self.downloads_tab.setLayout(layout)

    def download_selected_proton_version(self):
        selected_item = self.list_versions_proton.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleccion Invalida", "Por favor, selecciona una version de Proton para descargar.")
            return

        assets = selected_item.data(Qt.UserRole)
        
        # Dialogo para seleccionar el asset especifico (ej., version tar.gz)
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Archivo Proton")
        layout = QVBoxLayout()
        
        label = QLabel("Selecciona el archivo especifico para descargar:")
        layout.addWidget(label)
        
        version_combo = QComboBox()
        for asset in assets:
            name = asset["name"]
            size = asset.get("size", 0) / (1024 * 1024)  # Convertir a MB
            version_combo.addItem(f"{name} ({size:.1f} MB)", asset)
        layout.addWidget(version_combo)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.setFont(STYLE_STEAM_DECK["font"]) # Aplicar fuente al dialogo
        self.config_manager.apply_theme_to_dialog(dialog) # Aplicar tema al dialogo
        

        if dialog.exec_() == QDialog.Accepted:
            selected_asset = version_combo.currentData()
            download_url = selected_asset["browser_download_url"]
            filename = selected_asset["name"]
            destination = self.config_manager.proton_download_dir / filename
            
            self.download_file(download_url, destination, f"Proton {selected_item.text()}")

    def setup_proton_download_tab(self):
        layout = QVBoxLayout()
        
        self.group_proton_repos = QGroupBox("Repositorios de Proton")
        repo_layout = QVBoxLayout()
        
        self.list_repos_proton = QListWidget()
        self.list_repos_proton.setSelectionMode(QListWidget.SingleSelection)
        self.load_proton_repositories()
        repo_layout.addWidget(self.list_repos_proton)
        
        repo_btn_layout = QHBoxLayout()
        
        self.btn_add_proton_repo = QPushButton("Anadir")
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
        layout.addWidget(self.group_proton_repos)
        
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
        layout.addWidget(self.group_proton_versions)
        
        self.proton_tab.setLayout(layout)
        
    def setup_wine_download_tab(self):
        layout = QVBoxLayout()
        
        self.group_wine_repos = QGroupBox("Repositorios de Wine")
        repo_layout = QVBoxLayout()
        
        self.list_repos_wine = QListWidget()
        self.list_repos_wine.setSelectionMode(QListWidget.SingleSelection)
        self.load_wine_repositories()
        repo_layout.addWidget(self.list_repos_wine)
        
        repo_btn_layout = QHBoxLayout()
        
        self.btn_add_wine_repo = QPushButton("Anadir")
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
        self.list_repos_proton.clear()
        repos = self.config_manager.get_repositories("proton")
        for repo in repos:
            item = QListWidgetItem(repo["name"])
            item.setData(Qt.UserRole, repo["url"])
            item.setCheckState(Qt.Checked if repo.get("enabled", True) else Qt.Unchecked)
            self.list_repos_proton.addItem(item)
            
    def load_wine_repositories(self):
        self.list_repos_wine.clear()
        repos = self.config_manager.get_repositories("wine")
        for repo in repos:
            item = QListWidgetItem(repo["name"])
            item.setData(Qt.UserRole, repo["url"])
            item.setCheckState(Qt.Checked if repo.get("enabled", True) else Qt.Unchecked)
            self.list_repos_wine.addItem(item)
            
    def add_repository_dialog(self, repo_type: str):
        dialog = RepositoryDialog(repo_type, self)
        # Aplicar el tema al diálogo del repositorio
        self.config_manager.apply_theme_to_dialog(dialog)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                name, url = dialog.get_repository_info()
                if self.config_manager.add_repository(repo_type, name, url):
                    if repo_type == "proton":
                        self.load_proton_repositories()
                    else:
                        self.load_wine_repositories()
                    QMessageBox.information(self, "Repositorio Anadido", f"Repositorio '{name}' anadido exitosamente.")
                else:
                    QMessageBox.warning(self, "Duplicado", f"El repositorio '{name}' ya existe.")
            except ValueError as e:
                QMessageBox.warning(self, "Entrada Invalida", str(e))

    def add_proton_repository(self):
        self.add_repository_dialog("proton")
            
    def add_wine_repository(self):
        self.add_repository_dialog("wine")
            
    def delete_repository_dialog(self, repo_type: str):
        list_widget = self.list_repos_proton if repo_type == "proton" else self.list_repos_wine
        selected_row = list_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona un repositorio para eliminar.")
            return
            
        repo_name = list_widget.item(selected_row).text()
        reply = QMessageBox.question(self, "Confirmar Eliminacion", 
                                     f"Estas seguro de que quieres eliminar el repositorio '{repo_name}'?",
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
        list_widget = self.list_versions_proton if repo_type == "proton" else self.list_versions_wine
        list_widget.clear()
        enabled_repos = [repo for repo in self.config_manager.get_repositories(repo_type) if repo.get("enabled", True)]
        
        if not enabled_repos:
            QMessageBox.information(self, "No hay Repositorios", f"No hay repositorios de {repo_type.capitalize()} activos. Por favor, anade o habilita uno.")
            return

        self.progress_dialog = QProgressDialog(f"Buscando versiones de {repo_type.capitalize()}...", "Cancelar", 0, len(enabled_repos), self)
        self.progress_dialog.setWindowTitle("Actualizando Versiones")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setCancelButton(None) # No permitir cancelar la busqueda

        self.version_search_thread = VersionSearchThread(repo_type, enabled_repos)
        self.version_search_thread.progress.connect(self.progress_dialog.setValue)
        self.version_search_thread.new_release.connect(self._add_release_to_list)
        self.version_search_thread.finished.connect(self.progress_dialog.close)
        self.version_search_thread.error.connect(lambda msg: QMessageBox.warning(self, "Error Obteniendo Versiones", msg))
        
        self.version_search_thread.start()
        self.progress_dialog.exec_()


    def update_proton_versions(self):
        self.update_versions("proton")

    def update_wine_versions(self):
        self.update_versions("wine")
        
    def _add_release_to_list(self, repo_type: str, release_name: str, version: str, assets: list, published_at: str):
        """Anade un lanzamiento a la lista correspondiente (Wine o Proton)."""
        list_widget = self.list_versions_proton if repo_type == "proton" else self.list_versions_wine
        item = QListWidgetItem(release_name)
        item.setData(Qt.UserRole, assets) # Guardar los assets para la descarga
        
        tooltip = f"<b>Version:</b> {version}<br/>" \
                  f"<b>Fecha:</b> {published_at.split('T')[0]}<br/>" \
                  f"<b>Archivos:</b> {len(assets)}"
        item.setToolTip(tooltip)
        
        list_widget.addItem(item)


    def download_selected_wine_version(self):
        selected_item = self.list_versions_wine.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleccion Invalida", "Por favor, selecciona una version de Wine para descargar.")
            return

        assets = selected_item.data(Qt.UserRole)
        
        # Dialogo para seleccionar el asset especifico
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Archivo Wine")
        layout = QVBoxLayout()
        
        label = QLabel("Selecciona el archivo especifico para descargar:")
        layout.addWidget(label)
        
        version_combo = QComboBox()
        for asset in assets:
            name = asset["name"]
            size = asset.get("size", 0) / (1024 * 1024)  # Convertir a MB
            version_combo.addItem(f"{name} ({size:.1f} MB)", asset)
        layout.addWidget(version_combo)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.setFont(STYLE_STEAM_DECK["font"]) # Aplicar fuente al dialogo
        self.config_manager.apply_theme_to_dialog(dialog) # Aplicar tema al dialogo

        if dialog.exec_() == QDialog.Accepted:
            selected_asset = version_combo.currentData()
            download_url = selected_asset["browser_download_url"]
            filename = selected_asset["name"]
            destination = self.config_manager.wine_download_dir / filename
            
            self.download_file(download_url, destination, f"Wine {selected_item.text()}")
            
    def download_file(self, url: str, destination: Path, name: str):
        self.progress_dialog = QProgressDialog(f"Descargando {name}...", "Cancelar", 0, 100, self)
        self.progress_dialog.setWindowTitle("Descargando")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(False) # Mantener abierto hasta finalizar
        
        self.download_progress_bar = QProgressBar(self.progress_dialog)
        self.download_progress_bar.setRange(0, 100)
        self.progress_dialog.setBar(self.download_progress_bar)
        
        self.download_thread = DownloadThread(url, destination, name, self.config_manager)
        self.download_thread.progress.connect(self.download_progress_bar.setValue)
        self.download_thread.finished.connect(partial(self.on_download_finished, name=name))
        self.download_thread.error.connect(self.show_download_error)
        self.progress_dialog.canceled.connect(self.download_thread.stop)
        
        self.download_thread.start()
        self.progress_dialog.exec_()
        
    def show_download_error(self, error_msg: str):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error de Descarga", error_msg)

    def on_download_finished(self, filepath: str, name: str):
        self.progress_dialog.setLabelText(f"Descomprimiendo {name}...")
        self.progress_dialog.setMaximum(0) # Modo indeterminado para la descompresion
        
        self.decompression_thread = DecompressionThread(filepath, self.config_manager, name)
        self.decompression_thread.finished.connect(partial(self.on_decompression_finished, name=name))
        self.decompression_thread.error.connect(self.show_decompression_error)
        self.decompression_thread.start()

    def show_decompression_error(self, error_msg: str):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error de Descompresion", error_msg)

    def on_decompression_finished(self, path: str, name: str):
        self.progress_dialog.close()
        QMessageBox.information(self, "Exito", f"Descarga y descompresion de {name} completadas.\nInstalado en: {path}")

    def save_new_config(self):
        try:
            config_name = self.config_name.text().strip()
            if not config_name:
                QMessageBox.warning(self, "Error", "Debes especificar un nombre para la configuracion.")
                return

            # Obtener el elemento actual para la comprobacion de edicion, manejando de forma segura la no seleccion
            current_item_name = self.list_config.currentItem().text().replace(" (Default)", "").strip() if self.list_config.currentItem() else ""

            if config_name in self.config_manager.configs.get("configs", {}) and config_name != current_item_name:
                QMessageBox.warning(self, "Nombre Duplicado", f"Ya existe una configuracion con el nombre '{config_name}'. Por favor, elige otro nombre o edita la existente.")
                return

            config_type = "wine" if self.config_type.currentText() == "Wine" else "proton"
            architecture = self.architecture_combo.currentText()
            prefix = self.prefix_path.text().strip()

            if not prefix:
                QMessageBox.warning(self, "Error", "Debes especificar un prefijo.")
                return

            config_data = {
                "type": config_type,
                "prefix": prefix,
                "arch": architecture
            }

            if config_type == "proton":
                proton_directory = self.proton_directory.text().strip()
                if not proton_directory:
                    QMessageBox.warning(self, "Error", "Debes especificar el directorio de Proton.")
                    return
                config_data["proton_dir"] = proton_directory
            else: # Wine
                wine_directory = self.wine_directory.text().strip()
                if wine_directory: # wine_directory es opcional, si esta vacio, se usara el Wine del sistema
                    config_data["wine_dir"] = wine_directory

            # Si se esta editando, eliminar la configuracion antigua antes de guardar la nueva
            if current_item_name and current_item_name != config_name:
                self.config_manager.delete_config(current_item_name)
                
            self.config_manager.configs.setdefault("configs", {})[config_name] = config_data
            self.config_manager.save_configs()
            
            QMessageBox.information(self, "Guardado", f"Configuracion '{config_name}' guardada exitosamente.")
            self.load_configs() # Recargar la lista de configuraciones
            self.config_saved.emit() # Notificar a la ventana principal
            self.tabs.setCurrentIndex(0) # Volver a la pestana de configuraciones
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando configuracion: {str(e)}")

    def setup_settings_tab(self):
        layout = QFormLayout()
        self.edit_winetricks_path = QLineEdit(self.config_manager.get_winetricks_path())
        self.btn_winetricks = QPushButton("Explorar...")
        self.btn_winetricks.setAutoDefault(False)
        self.btn_winetricks.clicked.connect(self.browse_winetricks)

        winetricks_layout = QHBoxLayout()
        winetricks_layout.addWidget(self.edit_winetricks_path)
        winetricks_layout.addWidget(self.btn_winetricks)
        layout.addRow("Ruta de Winetricks:", winetricks_layout)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro"])
        current_theme = self.config_manager.get_theme()
        self.theme_combo.setCurrentText("Oscuro" if current_theme == "dark" else "Claro")
        layout.addRow("Tema de Interfaz:", self.theme_combo)

        # Global silent install checkbox
        self.checkbox_silent_global = QCheckBox("Habilitar modo silencioso por defecto (-q)")
        self.checkbox_silent_global.setChecked(self.config_manager.get_silent_install())
        layout.addRow(self.checkbox_silent_global)
        
        # New checkbox for forcing Winetricks installation
        self.checkbox_force_winetricks = QCheckBox("Forzar instalacion de Winetricks (--force)")
        self.checkbox_force_winetricks.setChecked(self.config_manager.get_force_winetricks_install())
        layout.addRow(self.checkbox_force_winetricks)

        self.btn_save_settings = QPushButton("Guardar Ajustes")
        self.btn_save_settings.setAutoDefault(False)
        self.btn_save_settings.clicked.connect(self.save_settings)
        layout.addWidget(self.btn_save_settings)
        self.settings_tab.setLayout(layout)
        
    def save_settings(self):
        try:
            winetricks_path_ok = self.config_manager.set_winetricks_path(self.edit_winetricks_path.text().strip())
            
            theme = "dark" if self.theme_combo.currentText() == "Oscuro" else "light"
            self.config_manager.set_theme(theme)
            
            self.config_manager.set_silent_install(self.checkbox_silent_global.isChecked())
            self.config_manager.set_force_winetricks_install(self.checkbox_force_winetricks.isChecked())
            
            if winetricks_path_ok:
                QMessageBox.information(self, "Guardado", "Ajustes guardados exitosamente.\nLos cambios de tema se aplicaran despues de reiniciar la aplicacion.")
            # Si winetricks_path_ok es False, el mensaje de error ya se ha mostrado por set_winetricks_path
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando ajustes: {str(e)}")
            
    def browse_winetricks(self):
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog) # Mejor control visual
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Ejecutables (*);;Todos los Archivos (*)")
        dialog.setDirectory(str(Path.home())) # Empezar en home
        
        # Corrección: Llama al método desde self.config_manager
        self.config_manager.apply_theme_to_dialog(dialog)
        
        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                self.edit_winetricks_path.setText(selected[0])

    def load_configs(self):
        self.list_config.clear()
        configs = self.config_manager.configs.get("configs", {})
        last_used = self.config_manager.configs.get("last_used", "")
        
        # Ordenar las claves para asegurar un orden de visualizacion consistente, excepto la predeterminada
        sorted_config_names = sorted(configs.keys())
        if last_used in sorted_config_names:
            sorted_config_names.remove(last_used)
            sorted_config_names.insert(0, last_used)

        for name in sorted_config_names:
            item = QListWidgetItem(name)
            if name == last_used:
                item.setText(f"{name} (Por Defecto)")
            self.list_config.addItem(item)
            if name == last_used:
                self.list_config.setCurrentItem(item) # Seleccionar la predeterminada
                
        self.update_displayed_config_info()

    def edit_config(self, item: QListWidgetItem):
        config_name_display = item.text()
        # Eliminar "(Por Defecto)" para obtener el nombre real
        config_name = config_name_display.replace(" (Por Defecto)", "").strip()
        
        config = self.config_manager.get_config(config_name)
        if not config:
            QMessageBox.warning(self, "Error", "Configuracion no encontrada o corrupta.")
            return

        self.tabs.setCurrentIndex(1) # Ir a la pestana de nueva configuracion
        self.config_name.setText(config_name)
        
        self.config_type.setCurrentText("Proton" if config.get("type") == "proton" else "Wine")
        self.prefix_path.setText(config.get("prefix", ""))
        self.architecture_combo.setCurrentText(config.get("arch", "win64"))

        if config.get("type") == "proton":
            self.proton_directory.setText(config.get("proton_dir", ""))
            self.wine_directory.setText("")
        else:
            self.wine_directory.setText(config.get("wine_dir", ""))
            self.proton_directory.setText("")
        
        self.update_config_field_visibility() # Asegurar que los campos correctos esten visibles

    def delete_config(self):
        selected = self.list_config.currentItem()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Selecciona una configuracion para eliminar.")
            return

        config_name_display = selected.text()
        config_name = config_name_display.replace(" (Por Defecto)", "").strip()

        if config_name == "Wine-System":
            QMessageBox.warning(self, "Error", "No se puede eliminar la configuracion 'Wine-System' ya que es la predeterminada del sistema.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Eliminacion",
            f"Estas seguro de que quieres eliminar la configuracion '{config_name}'? Esto no eliminara el prefijo o los archivos de Wine/Proton asociados.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.config_manager.delete_config(config_name):
                self.load_configs()
                QMessageBox.information(self, "Exito", f"Configuracion '{config_name}' eliminada.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la configuracion.")

    def set_default_config(self):
        selected = self.list_config.currentItem()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Selecciona una configuracion para establecer como predeterminada.")
            return

        config_name = selected.text().replace(" (Por Defecto)", "").strip()
        self.config_manager.configs["last_used"] = config_name
        self.config_manager.save_configs()
        QMessageBox.information(self, "Exito", f"Configuracion '{config_name}' establecida como predeterminada.")
        self.load_configs() # Recargar para actualizar el texto "(Por Defecto)"
        self.config_saved.emit() # Notificar a la ventana principal

    def update_displayed_config_info(self):
        selected = self.list_config.currentItem()
        if not selected:
            self.lbl_config_info.setText("Selecciona una configuracion para ver los detalles.")
            return

        config_name = selected.text().replace(" (Por Defecto)", "").strip()
        config = self.config_manager.get_config(config_name)
        if not config:
            self.lbl_config_info.setText("Configuracion no encontrada o corrupta.")
            return

        try:
            env = self.config_manager.get_current_environment(config_name)
        except Exception as e:
            self.lbl_config_info.setText(f"Error cargando el entorno para '{config_name}': {e}")
            return

        version = env.get("PROTON_VERSION") if config.get("type") == "proton" else env.get("WINE_VERSION", "Desconocida")
        wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "N/A")

        info = [
            f"<b>Configuracion Actual:</b> {config_name}",
            f"<b>Tipo:</b> {'Proton' if config['type'] == 'proton' else 'Wine'}",
            f"<b>Version Detectada:</b> <span style='color: #27ae60; font-weight: bold;'>{version}</span>",
        ]

        if config['type'] == 'proton':
            info.extend([
                f"<b>Wine en Proton:</b> <span style='color: #27ae60; font-weight: bold;'>{wine_version_in_proton}</span>",
                f"<b>Directorio de Proton:</b> {config.get('proton_dir', 'No especificado')}"
            ])
        else:
            wine_dir = config.get('wine_dir', 'Sistema (PATH)')
            info.extend([
                f"<b>Directorio de Wine:</b> {wine_dir}"
            ])

        info.extend([
            f"<b>Arquitectura:</b> {config.get('arch', 'win64')}",
            f"<b>Prefijo:</b> <span style='color: #FFB347; font-weight: bold;'>{config.get('prefix', 'No especificado')}</span>"
        ])

        self.lbl_config_info.setText("<br>".join(info))

    def update_config_field_visibility(self):
        is_proton = self.config_type.currentText() == "Proton"
        self.proton_group.setVisible(is_proton)
        self.wine_group.setVisible(not is_proton)

    def browse_prefix(self):
        path = self._get_directory_path("Seleccionar Directorio de Prefijo de Wine")
        if path:
            self.prefix_path.setText(path)

    def browse_wine(self):
        path = self._get_directory_path("Seleccionar Directorio de Instalacion de Wine (ej., bin/wine)")
        if path:
            self.wine_directory.setText(path)

    def browse_proton(self):
        path = self._get_directory_path("Seleccionar Directorio de Instalacion de Proton (ej., proton_dist/files)")
        if path:
            self.proton_directory.setText(path)

    def _get_directory_path(self, title="Seleccionar Directorio") -> str | None:
        dialog = QFileDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        dialog.setDirectory(str(Path.home())) # Directorio inicial
        
        # Corrección: Llama al método desde self.config_manager
        self.config_manager.apply_theme_to_dialog(dialog)
        
        if dialog.exec_() == QDialog.Accepted:
            return dialog.selectedFiles()[0]
        return None

    def test_configuration(self):
        config_name_test = self.config_name.text().strip()
        if not config_name_test:
            QMessageBox.warning(self, "Advertencia", "Por favor, introduce un nombre para la configuracion antes de probar.")
            return

        temp_config = {
            "type": "wine" if self.config_type.currentText() == "Wine" else "proton",
            "prefix": self.prefix_path.text().strip(),
            "arch": self.architecture_combo.currentText()
        }
        if temp_config["type"] == "proton":
            temp_config["proton_dir"] = self.proton_directory.text().strip()
        elif self.wine_directory.text().strip():
            temp_config["wine_dir"] = self.wine_directory.text().strip()
            
        # Guardar temporalmente para que get_current_environment pueda acceder
        original_configs = self.config_manager.configs.copy()
        # Crear una copia profunda de 'configs' para evitar modificar el original durante la configuracion de prueba
        temp_configs_dict = {k: v.copy() if isinstance(v, dict) else v for k, v in original_configs.get("configs", {}).items()}
        temp_configs_dict[config_name_test] = temp_config
        self.config_manager.configs["configs"] = temp_configs_dict
        self.config_manager.configs["last_used"] = config_name_test


        try:
            env = self.config_manager.get_current_environment(config_name_test)
            
            # Intentar ejecutar wine --version
            wine_executable = env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en la ruta especificada o en el PATH del sistema: {wine_executable}")

            # Ejecutar con un tiempo de espera para evitar bloqueos
            process = subprocess.run(
                [wine_executable, "--version"],
                env=env,
                capture_output=True,
                text=True,
                timeout=10, # Tiempo de espera de 10 segundos
                check=True # Lanzar CalledProcessError si el codigo de retorno no es 0
            )
            version_output = process.stdout.strip()
            QMessageBox.information(
                self,
                "Prueba Exitosa",
                f"Configuracion valida.\nVersion Detectada: {version_output}"
            )
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error de Prueba", f"Error de archivo: {str(e)}")
        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "Error de Prueba", "El comando Wine/Proton --version tardo demasiado en responder.")
        except subprocess.CalledProcessError as e:
            error_details = f"Codigo de Salida: {e.returncode}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            QMessageBox.critical(self, "Error de Prueba", f"El comando Wine/Proton --version fallo.\nDetalles:\n{error_details}")
        except Exception as e:
            QMessageBox.critical(self, "Error de Prueba", f"Error inesperado durante la prueba: {str(e)}")
        finally:
            # Restaurar la configuracion original
            self.config_manager.configs = original_configs
            self.config_manager.save_configs()


class VersionSearchThread(QThread):
    progress = pyqtSignal(int)
    new_release = pyqtSignal(str, str, str, object, str) # type, name, version, assets, published_at
    error = pyqtSignal(str)

    def __init__(self, repo_type: str, repositories: list[dict]):
        super().__init__()
        self.repo_type = repo_type
        self.repositories = repositories

    def run(self):
        fetched_count = 0
        total_repos = len(self.repositories)

        for i, repo in enumerate(self.repositories):
            if not repo.get("enabled", True):
                continue
            
            url = repo["url"]
            try:
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(req, timeout=10) as response: # Anadir tiempo de espera a la solicitud
                    if response.getcode() != 200:
                        raise HTTPError(url, response.getcode(), response.reason, response.headers, None)
                    
                    releases = json.loads(response.read().decode())
                    
                    for release in releases:
                        if release.get("draft", False) or release.get("prerelease", False):
                            continue # Ignorar borradores y pre-lanzamientos
                        
                        version = release["tag_name"]
                        # Filtrar assets relevantes (tar.gz, tar.xz, zip)
                        assets = [a for a in release["assets"] if any(a["name"].endswith(ext) for ext in ['.tar.gz', '.tar.xz', '.zip'])]
                        
                        if not assets:
                            continue
                            
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
    def __init__(self, repo_type: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.repo_type = repo_type
        self.setWindowTitle(f"Anadir Repositorio de {self.repo_type.capitalize()}")
        self.setup_ui()
        self.apply_steamdeck_style()

    def apply_steamdeck_style(self):
        self.setFont(STYLE_STEAM_DECK["font"])
        # Comprobar la paleta de la aplicacion actual para determinar si el tema oscuro esta activo
        theme_is_dark = QApplication.palette().color(QPalette.Window).name() == QColor(STYLE_STEAM_DECK["dark_palette"]["window"]).name()

        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme_is_dark else STYLE_STEAM_DECK["button_style"])
            elif isinstance(widget, QLabel):
                widget.setFont(STYLE_STEAM_DECK["font"])

    def setup_ui(self):
        layout = QFormLayout()

        self.edit_name = QLineEdit()
        layout.addRow("Nombre del Repositorio:", self.edit_name)

        self.edit_url = QLineEdit()
        layout.addRow("URL de la API de GitHub:", self.edit_url)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def get_repository_info(self) -> tuple[str, str]:
        name = self.edit_name.text().strip()
        url = self.edit_url.text().strip()

        if not name:
            raise ValueError("El nombre del repositorio no puede estar vacio.")
        if not url:
            raise ValueError("La URL de la API de GitHub no puede estar vacia.")
        if not url.startswith("https://api.github.com/repos/"):
            raise ValueError("URL de la API de GitHub invalida. Debe comenzar con 'https://api.github.com/repos/'.")

        return name, url

class SelectGroupsDialog(QDialog):
    def __init__(self, component_groups: dict[str, list[str]], config_manager: ConfigManager, parent: QWidget | None = None): # Añadir config_manager
        super().__init__(parent)
        self.component_groups = component_groups
        self.config_manager = config_manager # Guardar la instancia de config_manager
        self.setWindowTitle("Seleccionar Componentes de Winetricks")
        self.setMinimumSize(500, 450)
        self.setup_ui()
        self.apply_steamdeck_style()

    def apply_steamdeck_style(self):
        self.setFont(STYLE_STEAM_DECK["font"])
        # Comprobar la paleta de la aplicacion actual para determinar si el tema oscuro esta activo
        theme_is_dark = self.config_manager.get_theme() == "dark" # Usar el config_manager

        # Estilo para QTreeWidget (fondo blanco, texto negro para mejor legibilidad de los componentes)
        base_font_size = STYLE_STEAM_DECK["font"].pointSize()
        # Increase font size for the tree widget items
        tree_font_size = base_font_size + 3 # Adjust as needed

        # Determine colors based on theme for the tree widget
        if theme_is_dark:
            tree_bg_color = "#31363b"  # Dark window background
            tree_text_color = "#FFFFFF" # White text
            tree_border_color = "#5c636a" # Dark border
            tree_header_bg_color = "#40464d" # Dark button for header
            tree_header_text_color = "#FFFFFF" # White text for header
        else:
            tree_bg_color = "#FFFFFF"  # White background
            tree_text_color = "#212529" # Dark text
            tree_border_color = "#d0d0d0" # Light border
            tree_header_bg_color = "#f1f3f4" # Light gray for header
            tree_header_text_color = "#212529" # Dark text for header


        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {tree_bg_color};
                color: {tree_text_color};
                border: 1px solid {tree_border_color};
                font-size: {tree_font_size}px;
            }}
            QTreeWidget::item {{
                padding: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {COLOR_PRIMARY};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {tree_header_bg_color};
                padding: 8px;
                border: 1px solid {tree_border_color};
                font-weight: bold;
                color: {tree_header_text_color}; /* Asegurar que el texto del encabezado sea legible */
            }}
        """)

        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme_is_dark else STYLE_STEAM_DECK["button_style"])
            elif isinstance(widget, QGroupBox):
                widget.setFont(STYLE_STEAM_DECK["title_font"])
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_groupbox_style"] if theme_is_dark else STYLE_STEAM_DECK["groupbox_style"])
            elif isinstance(widget, QLabel):
                widget.setFont(STYLE_STEAM_DECK["font"])
            
        # Aplicar paleta para el fondo y texto general del dialogo
        palette = QPalette()
        if theme_is_dark:
            palette.setColor(QPalette.Window, STYLE_STEAM_DECK["dark_palette"]["window"])
            palette.setColor(QPalette.WindowText, STYLE_STEAM_DECK["dark_palette"]["window_text"])
            palette.setColor(QPalette.Base, STYLE_STEAM_DECK["dark_palette"]["base"]) # Para fondos de entrada de texto, etc.
            palette.setColor(QPalette.Text, STYLE_STEAM_DECK["dark_palette"]["text"])
            palette.setColor(QPalette.Highlight, STYLE_STEAM_DECK["dark_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, STYLE_STEAM_DECK["dark_palette"]["highlight_text"])
        else:
            palette.setColor(QPalette.Window, STYLE_STEAM_DECK["light_palette"]["window"])
            palette.setColor(QPalette.WindowText, STYLE_STEAM_DECK["light_palette"]["window_text"])
            palette.setColor(QPalette.Base, STYLE_STEAM_DECK["light_palette"]["base"])
            palette.setColor(QPalette.Text, STYLE_STEAM_DECK["light_palette"]["text"])
            palette.setColor(QPalette.Highlight, STYLE_STEAM_DECK["light_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, STYLE_STEAM_DECK["light_palette"]["highlight_text"])
        self.setPalette(palette)
        # Forzar repintado para asegurar que los estilos se apliquen inmediatamente
        self.repaint()


    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Componente", "Descripcion"])
        self.tree.setColumnCount(2)
        self.tree.setSelectionMode(QTreeWidget.NoSelection) # Deshabilitar seleccion de fila, solo casillas
        self.tree.itemChanged.connect(self._handle_item_change) # Conectar para manejar el estado de tres estados
        
        self.component_descriptions = {
            "vb2run": "Tiempo de Ejecucion de Visual Basic 2.0", "vb3run": "Tiempo de Ejecucion de Visual Basic 3.0",
            "vb4run": "Tiempo de Ejecucion de Visual Basic 4.0", "vb5run": "Tiempo de Ejecucion de Visual Basic 5.0",
            "vb6run": "Tiempo de Ejecucion de Visual Basic 6.0",
            "vcrun6": "Tiempo de Ejecucion de Visual C++ 6.0 (SP6 recomendado)", "vcrun2005": "Tiempo de Ejecucion de Visual C++ 2005",
            "vcrun2008": "Tiempo de Ejecucion de Visual C++ 2008", "vcrun2010": "Tiempo de Ejecucion de Visual C++ 2010",
            "vcrun2012": "Tiempo de Ejecucion de Visual C++ 2012", "vcrun2013": "Tiempo de Ejecucion de Visual C++ 2013",
            "vcrun2015": "Tiempo de Ejecucion de Visual C++ 2015", "vcrun2017": "Tiempo de Ejecucion de Visual C++ 2017",
            "vcrun2019": "Tiempo de Ejecucion de Visual C++ 2019", "vcrun2022": "Tiempo de Ejecucion de Visual C++ 2022",
            "dotnet40": "Microsoft .NET Framework 4.0", "dotnet48": "Microsoft .NET Framework 4.8",
            "dxvk": "DXVK (DirectX a Vulkan)", "vkd3d": "VKD3D-Proton (DirectX 12 a Vulkan)",
            # Anadir mas descripciones segun se desee
        }
        
        for group_name, components in self.component_groups.items():
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, group_name)
            group_item.setFlags(group_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsTristate)
            group_item.setCheckState(0, Qt.PartiallyChecked) # Por defecto, en estado parcial
            
            for comp in components:
                child_item = QTreeWidgetItem(group_item)
                child_item.setText(0, comp)
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.Unchecked)
                
                description = self.component_descriptions.get(comp, "Componente estandar de Winetricks.")
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

    def _handle_item_change(self, item: QTreeWidgetItem, column: int):
        """Maneja el estado de las casillas de verificacion de los elementos del arbol (tres estados)."""
        if item.flags() & Qt.ItemIsTristate: # Es un nodo padre (grupo)
            # Bloquear temporalmente las senales para evitar llamadas recursivas al establecer estados de hijos
            self.tree.blockSignals(True)
            if item.checkState(0) == Qt.Checked:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, Qt.Checked)
            elif item.checkState(0) == Qt.Unchecked:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, Qt.Unchecked)
            self.tree.blockSignals(False)
        else: # Es un nodo hijo (componente individual)
            parent = item.parent()
            if parent:
                checked_children = 0
                for i in range(parent.childCount()):
                    if parent.child(i).checkState(0) == Qt.Checked:
                        checked_children += 1
                
                # Actualizar el estado del padre segun los hijos
                if checked_children == 0:
                    parent.setCheckState(0, Qt.Unchecked)
                elif checked_children == parent.childCount():
                    parent.setCheckState(0, Qt.Checked)
                else:
                    parent.setCheckState(0, Qt.PartiallyChecked)

    def get_selected_components(self) -> list[str]:
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
        self.config_manager = config_manager
        self.setWindowTitle("Anadir Programa Personalizado")
        self.setup_ui()
        self.apply_steamdeck_style()

    def apply_steamdeck_style(self):
        self.setFont(STYLE_STEAM_DECK["font"])
        theme = self.config_manager.get_theme()
        
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme == "dark" else STYLE_STEAM_DECK["button_style"])
            elif isinstance(widget, QGroupBox):
                widget.setFont(STYLE_STEAM_DECK["title_font"])
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_groupbox_style"] if theme == "dark" else STYLE_STEAM_DECK["groupbox_style"])
            elif isinstance(widget, QLabel):
                widget.setFont(STYLE_STEAM_DECK["font"])

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

        # Botones en la misma fila
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        self.setLayout(layout)

    def browse_program(self):
        default_dir = self.config_manager.programs_dir
        
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        # MODIFICATION START: Changed from QFileDialog.Directory to QFileDialog.ExistingFile
        dialog.setFileMode(QFileDialog.ExistingFile) 
        # MODIFICATION START: Added filters for common executable and script types
        dialog.setNameFilter("Windows Executables (*.exe *.msi);;Winetricks Scripts (*.wtr);;All Files (*)")
        # MODIFICATION END
        dialog.setDirectory(str(default_dir))
        
        # CORRECTED: Call apply_theme_to_dialog from the config_manager
        self.config_manager.apply_theme_to_dialog(dialog)

        if dialog.exec_():
            selected_file = dialog.selectedFiles()
            if selected_file:
                # selected_file[0] will now be the path to the selected file
                self.edit_path.setText(selected_file[0])

    def get_program_info(self) -> dict:
        name = self.edit_name.text().strip()
        path = self.edit_path.text().strip()
        
        if not name:
            raise ValueError("Debes especificar un nombre para el programa.")
            
        program_type = "winetricks" # Valor por defecto
        
        # Determinar el tipo de programa
        path_obj = Path(path)
        if path.lower().endswith(('.exe', '.msi')):
            if not path_obj.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {path}")
            program_type = "exe"
            path = str(path_obj.absolute()) # Asegurar ruta absoluta
        elif path.lower().endswith('.wtr'): # Nuevo tipo: script de winetricks
            if not path_obj.exists():
                raise FileNotFoundError(f"Archivo de script no encontrado: {path}")
            program_type = "wtr"
            path = str(path_obj.absolute())
        else: # Asumir que es un componente de winetricks (ej., vcrun2015)
            program_type = "winetricks"
            # La validacion para componentes de winetricks se realiza al ejecutar winetricks.
            
        return {
            "name": name,
            "path": path,
            "type": program_type
        }

class ManageProgramsDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Gestionar Programas Guardados")
        self.setMinimumSize(650, 450)
        self.setup_ui()
        self.apply_steamdeck_style()
        self.selected_programs_to_load = [] # Almacenar programas seleccionados para cargar

    def apply_steamdeck_style(self):
        self.setFont(STYLE_STEAM_DECK["font"])
        theme = self.config_manager.get_theme()
        
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme == "dark" else STYLE_STEAM_DECK["button_style"])
            elif isinstance(widget, QGroupBox):
                widget.setFont(STYLE_STEAM_DECK["title_font"])
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_groupbox_style"] if theme == "dark" else STYLE_STEAM_DECK["groupbox_style"])
            elif isinstance(widget, QLabel):
                widget.setFont(STYLE_STEAM_DECK["font"])
        
        self.table.setStyleSheet(STYLE_STEAM_DECK["dark_table_style"] if theme == "dark" else STYLE_STEAM_DECK["table_style"])

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nombre", "Comando/Ruta", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.load_programs()
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_load_selected = QPushButton("Cargar Seleccion")
        self.btn_load_selected.setAutoDefault(False)
        self.btn_load_selected.clicked.connect(self.load_selection)
        btn_layout.addWidget(self.btn_load_selected)

        self.btn_delete = QPushButton("Eliminar Seleccion")
        self.btn_delete.setAutoDefault(False)
        self.btn_delete.clicked.connect(self.delete_programs)
        btn_layout.addWidget(self.btn_delete)

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setAutoDefault(False)
        self.btn_close.clicked.connect(self.reject) # Usar reject para cerrar sin cargar
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_programs(self):
        self.table.setRowCount(0)
        programs = self.config_manager.get_custom_programs()
        self.table.setRowCount(len(programs))
        
        for row, program in enumerate(programs):
            name_item = QTableWidgetItem(program.get('name', 'N/A'))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            path_item = QTableWidgetItem(program.get('path', 'N/A'))
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, path_item)
            
            type_text = program.get("type", "winetricks").upper()
            type_item = QTableWidgetItem(type_text) # Mostrar EXE, WINETRICKS, WTR
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

    def load_selection(self):
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())))
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron programas para cargar.")
            return

        all_programs = self.config_manager.get_custom_programs()
        
        # Get current prefix details for checking installed programs
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

            if program_info["type"] == "winetricks":
                if program_info["path"] in installed_items_in_prefix:
                    item_already_installed = True
            elif program_info["type"] == "exe":
                exe_filename = Path(program_info["path"]).name
                if exe_filename in installed_items_in_prefix:
                    item_already_installed = True
            elif program_info["type"] == "wtr":
                wtr_filename = Path(program_info["path"]).name
                if wtr_filename in installed_items_in_prefix:
                    item_already_installed = True
            
            if item_already_installed:
                reply = QMessageBox.question(self, "Programa ya Instalado",
                                             f"El programa '{program_info['name']}' ya está registrado como instalado en este prefijo ({current_config_name}). ¿Deseas agregarlo a la lista de instalación de todos modos?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    continue # Skip this program

            programs_to_add.append(program_info)
        
        self.selected_programs_to_load = programs_to_add
        self.accept() # Close the dialog and return ACCEPTED

    def delete_programs(self):
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())), reverse=True)
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron programas para eliminar.")
            return

        program_names_to_delete = [self.table.item(row, 0).text() for row in selected_rows]

        reply = QMessageBox.question(
            self, "Confirmar Eliminacion",
            f"Estas seguro de que quieres eliminar {len(program_names_to_delete)} programa(s) guardado(s)?\n\n" + "\n".join(program_names_to_delete),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count = 0
            for name in program_names_to_delete:
                if self.config_manager.delete_custom_program(name):
                    deleted_count += 1
            
            if deleted_count > 0:
                self.load_programs() # Recargar la tabla despues de la eliminacion
                QMessageBox.information(self, "Exito", f"{deleted_count} programa(s) eliminado(s) exitosamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar ningun programa.")

    def get_selected_programs_to_load(self) -> list[dict]:
        return self.selected_programs_to_load

# --- Ventana Principal ---
class InstallerApp(QWidget):
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.installer_thread = None
        
        self.items_for_installation: list[dict] = []
        
        self.silent_mode = self.config_manager.get_silent_install()
        self.force_mode = self.config_manager.get_force_winetricks_install()

        self.apply_theme_at_startup()
        self.setup_ui()
        self.apply_steamdeck_style()
        self.setMinimumSize(1000, 700)

    def apply_theme_at_startup(self):
        theme = self.config_manager.get_theme()
        palette = QPalette()
        
        if theme == "dark":
            palette.setColor(QPalette.Window, STYLE_STEAM_DECK["dark_palette"]["window"])
            palette.setColor(QPalette.WindowText, STYLE_STEAM_DECK["dark_palette"]["window_text"])
            palette.setColor(QPalette.Base, STYLE_STEAM_DECK["dark_palette"]["base"])
            palette.setColor(QPalette.Text, STYLE_STEAM_DECK["dark_palette"]["text"])
            palette.setColor(QPalette.Button, STYLE_STEAM_DECK["dark_palette"]["button"])
            palette.setColor(QPalette.ButtonText, STYLE_STEAM_DECK["dark_palette"]["button_text"])
            palette.setColor(QPalette.Highlight, STYLE_STEAM_DECK["dark_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, STYLE_STEAM_DECK["dark_palette"]["highlight_text"])
        else:
            palette = QApplication.style().standardPalette()
            
        QApplication.setPalette(palette)

    def apply_steamdeck_style(self):
        self.setFont(STYLE_STEAM_DECK["font"])
        theme = self.config_manager.get_theme() 
        
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme == "dark" else STYLE_STEAM_DECK["button_style"])
            elif isinstance(widget, QGroupBox):
                widget.setFont(STYLE_STEAM_DECK["title_font"])
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_groupbox_style"] if theme == "dark" else STYLE_STEAM_DECK["groupbox_style"])
            elif isinstance(widget, QLabel):
                widget.setFont(STYLE_STEAM_DECK["font"])
        
        self.items_table.setStyleSheet(STYLE_STEAM_DECK["dark_table_style"] if theme == "dark" else STYLE_STEAM_DECK["table_style"])

    def setup_ui(self):
        self.setWindowTitle("WineProton Manager")
        self.resize(self.config_manager.get_window_size())
        self.setWindowIcon(QIcon.fromTheme("wine"))

        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QHBoxLayout(content)
        
        content_layout.addWidget(self.create_left_panel(), 1)
        content_layout.addWidget(self.create_right_panel(), 2)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        config_group = QGroupBox("Configuracion del Entorno Actual")
        config_layout = QVBoxLayout()
        self.lbl_config = QLabel()
        self.lbl_config.setWordWrap(True)
        self.update_config_info()
        
        self.btn_manage_environments = QPushButton("Gestionar Entornos...")
        self.btn_manage_environments.setAutoDefault(False)
        self.btn_manage_environments.clicked.connect(self.configure_environments)
        config_layout.addWidget(self.lbl_config)
        config_layout.addWidget(self.btn_manage_environments)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        actions_group = QGroupBox("Acciones de Instalacion")
        actions_layout = QVBoxLayout()
        
        components_group = QGroupBox("Componentes de Winetricks")
        components_layout = QVBoxLayout()
        self.btn_select_components = QPushButton("Seleccionar Componentes de Winetricks")
        self.btn_select_components.setAutoDefault(False)
        self.btn_select_components.clicked.connect(self.select_components)
        components_layout.addWidget(self.btn_select_components)
        components_group.setLayout(components_layout)
        actions_layout.addWidget(components_group)
        
        custom_group = QGroupBox("Programas Personalizados")
        custom_layout = QVBoxLayout()
        self.btn_add_custom = QPushButton("Anadir Programa/Script")
        self.btn_add_custom.setAutoDefault(False)
        self.btn_add_custom.clicked.connect(self.add_custom_program)
        custom_layout.addWidget(self.btn_add_custom)
        
        self.btn_manage_custom = QPushButton("Cargar/Eliminar Programas Guardados")
        self.btn_manage_custom.setAutoDefault(False)
        self.btn_manage_custom.clicked.connect(self.manage_custom_programs)
        custom_layout.addWidget(self.btn_manage_custom)
        custom_group.setLayout(custom_layout)
        actions_layout.addWidget(custom_group)
        
        options_group = QGroupBox("Opciones de Instalacion (solo para esta sesion)")
        options_layout = QVBoxLayout()
        self.checkbox_silent_session = QCheckBox("Habilitar modo silencioso para esta instalacion Winetricks (-q)")
        self.checkbox_silent_session.setChecked(self.silent_mode) 
        self.checkbox_silent_session.stateChanged.connect(self.update_silent_mode_session)
        options_layout.addWidget(self.checkbox_silent_session)
        
        self.checkbox_force_winetricks_session = QCheckBox("Forzar instalacion de Winetricks para esta instalacion (--force)")
        self.checkbox_force_winetricks_session.setChecked(self.force_mode) 
        self.checkbox_force_winetricks_session.stateChanged.connect(self.update_force_mode_session)
        options_layout.addWidget(self.checkbox_force_winetricks_session)
        
        options_group.setLayout(options_layout)
        actions_layout.addWidget(options_group)
        
        self.btn_install = QPushButton("Iniciar Instalacion")
        self.btn_install.setAutoDefault(False)
        self.btn_install.clicked.connect(self.start_installation)
        self.btn_install.setEnabled(False) 
        
        self.btn_cancel = QPushButton("Cancelar Instalacion")
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.clicked.connect(self.cancel_installation)
        self.btn_cancel.setEnabled(False) 
        
        actions_layout.addWidget(self.btn_install)
        actions_layout.addWidget(self.btn_cancel)
        
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

        right_column = QVBoxLayout()
        self.btn_winetricks_gui = QPushButton("Winetricks GUI")
        self.btn_winetricks_gui.setAutoDefault(False)
        self.btn_winetricks_gui.clicked.connect(self.open_winetricks)
        right_column.addWidget(self.btn_winetricks_gui)
        
        self.btn_winecfg = QPushButton("Winecfg")
        self.btn_winecfg.setAutoDefault(False)
        self.btn_winecfg.clicked.connect(self.open_winecfg)
        right_column.addWidget(self.btn_winecfg)
        
        self.btn_explorer = QPushButton("Explorador del Prefijo")
        self.btn_explorer.setAutoDefault(False)
        self.btn_explorer.clicked.connect(self.open_explorer)
        right_column.addWidget(self.btn_explorer)

        tools_layout.addLayout(left_column)
        tools_layout.addLayout(right_column)
        tools_group.setLayout(tools_layout)
        actions_layout.addWidget(tools_group)

        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        return panel

    def create_right_panel(self) -> QWidget:
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
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setSelectionMode(QTableWidget.SingleSelection) 
        self.items_table.itemChanged.connect(self.on_table_item_changed)
        layout.addWidget(self.items_table)
        
        btn_layout = QHBoxLayout()
        buttons = [
            ("Limpiar Lista", self.clear_list),
            ("Eliminar Seleccion", self.delete_selected_from_table),
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

    def on_table_item_changed(self, item: QTableWidgetItem):
        """Maneja los cambios en las casillas de verificacion de la tabla."""
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError: 
            pass

        if item.column() == 0: 
            row = item.row()
            status_item = self.items_table.item(row, 3)

            if status_item:
                # Only change status if it's currently "Pendiente" or "Omitido"
                # This prevents overwriting "Finalizado" or "Error" after installation.
                current_status_text = status_item.text()
                if current_status_text in ["Pendiente", "Omitido"]:
                    new_status = "Pendiente" if item.checkState() == Qt.Checked else "Omitido"
                    status_item.setText(new_status)
                    
                    if new_status == "Omitido":
                        status_item.setForeground(QColor("darkorange")) 
                    else:
                        theme = self.config_manager.get_theme()
                        status_item.setForeground(QColor(STYLE_STEAM_DECK["dark_palette"]["text"]) if theme == "dark" else QColor(STYLE_STEAM_DECK["light_palette"]["text"]))
            else:
                print(f"DEBUG: El elemento de estado es None para la fila {row}, columna 3 cuando la casilla de verificacion cambio. Saltando setText.")

        self.items_table.itemChanged.connect(self.on_table_item_changed)
        self.update_installation_button_state()

    def update_silent_mode_session(self, state: int):
        self.silent_mode = state == Qt.Checked

    def update_force_mode_session(self, state: int):
        self.force_mode = state == Qt.Checked

    def closeEvent(self, event):
        """Guarda el tamano de la ventana al cerrar."""
        self.config_manager.save_window_size(self.size())
        super().closeEvent(event)

    def configure_environments(self):
        """Abre el dialogo para configurar entornos de Wine/Proton."""
        dialog = ConfigDialog(self.config_manager, self)
        dialog.config_saved.connect(self.update_config_info)
        dialog.exec_()
        self.update_config_info() 

    def update_config_info(self):
        """Actualiza la informacion del entorno actual en la GUI."""
        current_config_name = self.config_manager.configs.get("last_used", "Wine-System")
        config = self.config_manager.get_config(current_config_name)

        if not config:
            self.lbl_config.setText("No se ha seleccionado ninguna configuracion o la configuracion es invalida.")
            return

        try:
            env = self.config_manager.get_current_environment(current_config_name)
            version = env.get("PROTON_VERSION") if config.get("type") == "proton" else env.get("WINE_VERSION", "Desconocida")
            wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "N/A")

            text = [
                f"<b>Configuracion Actual:</b> {current_config_name}",
                f"<b>Tipo:</b> {'Proton' if config.get('type') == 'proton' else 'Wine'}",
                f"<b>Version Detectada:</b> <span style='color: #27ae60; font-weight: bold;'>{version}</span>",
            ]

            if config.get('type') == 'proton':
                text.extend([
                    f"<b>Wine en Proton:</b> <span style='color: #27ae60; font-weight: bold;'>{wine_version_in_proton}</span>",
                    f"<b>Directorio de Proton:</b> {config.get('proton_dir', 'No especificado')}"
                ])
            else:
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
            self.lbl_config.setText(f"ERROR: {str(e)}<br>Por favor, revisa la configuracion.")
            QMessageBox.critical(self, "Error de Configuracion", str(e))
        except Exception as e:
            self.lbl_config.setText(f"ERROR: No se pudo obtener informacion de configuracion: {str(e)}")


    def add_custom_program(self):
        """Abre el dialogo para anadir un nuevo programa/script personalizado."""
        dialog = CustomProgramDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                program_info = dialog.get_program_info()
                
                current_paths_in_table = [item['path'] for item in self.items_for_installation]
                if program_info['path'] in current_paths_in_table:
                    QMessageBox.warning(self, "Duplicado", f"El programa '{program_info['name']}' ya esta en la lista de instalacion.")
                    return
                
                current_config_name = self.config_manager.configs["last_used"]
                config = self.config_manager.get_config(current_config_name)
                
                if config and "prefix" in config:
                    installed_items = self.config_manager.get_installed_winetricks(config["prefix"])
                    
                    if program_info["type"] == "winetricks" and program_info["path"] in installed_items:
                        reply = QMessageBox.question(self, "Componente ya instalado",
                                                     f"El componente '{program_info['path']}' ya esta registrado como instalado en este prefijo. Deseas agregarlo a la lista de instalacion de todos modos?",
                                                     QMessageBox.Yes | QMessageBox.No)
                        if reply == QMessageBox.No: return
                    
                    elif program_info["type"] == "exe":
                        exe_filename = Path(program_info["path"]).name
                        if exe_filename in installed_items:
                            reply = QMessageBox.question(self, "Programa ya instalado",
                                                         f"El programa '{exe_filename}' ya esta registrado como instalado en este prefijo. Deseas agregarlo a la lista de instalacion de todos modos?",
                                                         QMessageBox.Yes | QMessageBox.No)
                            if reply == QMessageBox.No: return
                    elif program_info["type"] == "wtr":
                        wtr_filename = Path(program_info["path"]).name
                        if wtr_filename in installed_items:
                             reply = QMessageBox.question(self, "Script ya ejecutado",
                                                          f"El script '{wtr_filename}' ya esta registrado como ejecutado en este prefijo. Deseas agregarlo a la lista de instalacion de todos modos?",
                                                          QMessageBox.Yes | QMessageBox.No)
                             if reply == QMessageBox.No: return
                
                self.config_manager.add_custom_program(program_info) 
                self.add_item_to_table(program_info) 
                self.update_installation_button_state()
                
            except ValueError as e:
                QMessageBox.warning(self, "Entrada Invalida", str(e))
            except FileNotFoundError as e:
                QMessageBox.warning(self, "Archivo no Encontrado", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al anadir programa: {str(e)}")

    def add_item_to_table(self, program_data: dict):
        """Añade un elemento a la tabla de instalación."""
        # Disconnect signal to prevent unintended triggers during programmatic changes
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass
        
        row_count = self.items_table.rowCount()
        self.items_table.insertRow(row_count)
        
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checkbox_item.setCheckState(Qt.Checked)
        self.items_table.setItem(row_count, 0, checkbox_item)
        
        name_item = QTableWidgetItem(program_data["name"])
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row_count, 1, name_item)
        
        type_text = program_data["type"].upper()
        type_item = QTableWidgetItem(type_text)
        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row_count, 2, type_item)
        
        status_item = QTableWidgetItem("Pendiente")
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row_count, 3, status_item)
        
        # Add 'status' directly to the program_data dictionary for the internal model
        program_data['current_status'] = "Pendiente" 
        self.items_for_installation.append(program_data)
        
        self.update_installation_button_state()

        # Reconnect the signal after all programmatic changes for the row are done
        self.items_table.itemChanged.connect(self.on_table_item_changed)

    def manage_custom_programs(self):
        """Abre el dialogo para gestionar (cargar/eliminar) programas personalizados."""
        dialog = ManageProgramsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_programs = dialog.get_selected_programs_to_load()
            for program_info in selected_programs:
                if program_info not in self.items_for_installation:
                    self.add_item_to_table(program_info)
            self.update_installation_button_state()

    def select_components(self):
        """Abre el dialogo para seleccionar componentes de Winetricks."""
        component_groups = {
            "Librerias de Visual Basic": ["vb2run", "vb3run", "vb4run", "vb5run", "vb6run"],
            "Tiempo de Ejecucion de Visual C++": [
                "vcrun6", "vcrun6sp6", "vcrun2003", "vcrun2005", "vcrun2008",
                "vcrun2010", "vcrun2012", "vcrun2013", "vcrun2015", "vcrun2017",
                "vcrun2019", "vcrun2022"
            ],
            "Framework .NET": [
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
            "Componentes del Sistema": [
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

        dialog = SelectGroupsDialog(component_groups, self.config_manager, self) 
        if dialog.exec_() == QDialog.Accepted:
            selected_components = dialog.get_selected_components()
            
            current_config_name = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config_name)
            installed_components = []
            if config and "prefix" in config:
                installed_components = self.config_manager.get_installed_winetricks(config["prefix"])
                
            for comp_name in selected_components:
                if any(item.get('path') == comp_name and item.get('type') == 'winetricks' for item in self.items_for_installation):
                    QMessageBox.warning(self, "Duplicado", f"El componente '{comp_name}' ya esta en la lista de instalacion.")
                    continue

                if comp_name in installed_components:
                    reply = QMessageBox.question(self, "Componente ya instalado",
                                                 f"El componente '{comp_name}' ya esta registrado como instalado en este prefijo. Deseas agregarlo a la lista de instalacion de todos modos?",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.No:
                        continue
                    
                self.add_item_to_table({"name": comp_name, "path": comp_name, "type": "winetricks"})
            self.update_installation_button_state()

    def cancel_installation(self):
        """
        Detiene la instalacion actual si hay un hilo instalador en ejecucion.
        Pide confirmacion al usuario antes de cancelar.
        """
        if self.installer_thread and self.installer_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirmar Cancelacion",
                "Estas seguro de que quieres cancelar la instalacion en curso?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.installer_thread.stop() 
                self.installer_thread.wait() 
                QMessageBox.information(self, "Cancelado", "La instalacion ha sido cancelada por el usuario.")
        else:
            QMessageBox.information(self, "Informacion", "No hay ninguna instalacion en progreso para cancelar.")

    def clear_list(self):
        """Borra la tabla y el modelo de datos interno, restableciendo los estados de los botones."""
        reply = QMessageBox.question(self, "Confirmar", "Estas seguro de que quieres borrar toda la lista de instalacion?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.items_table.setRowCount(0)
            self.items_for_installation.clear()
            self.update_installation_button_state()

    def delete_selected_from_table(self):
        """Elimina los elementos seleccionados de la tabla y el modelo de datos interno."""
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())), reverse=True)
        
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron elementos para eliminar.")
            return

        reply = QMessageBox.question(self, "Confirmar Eliminacion", 
                                     f"Estas seguro de que quieres eliminar {len(selected_rows)} elemento(s) de la lista de instalacion?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            
            for row in selected_rows:
                if 0 <= row < len(self.items_for_installation):
                    del self.items_for_installation[row]
                self.items_table.removeRow(row)
                
            self.items_table.itemChanged.connect(self.on_table_item_changed)
            self.update_installation_button_state()

    def move_item_up(self):
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())))
        
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Advertencia", "Selecciona solo un elemento para mover.")
            return

        current_row = selected_rows[0]
        if current_row > 0:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            self.swap_table_rows(current_row, current_row - 1)
            self.items_for_installation[current_row], self.items_for_installation[current_row - 1] = \
                self.items_for_installation[current_row - 1], self.items_for_installation[current_row]
            self.items_table.selectRow(current_row - 1)
            self.items_table.itemChanged.connect(self.on_table_item_changed)


    def move_item_down(self):
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())))
        
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Advertencia", "Selecciona solo un elemento para mover.")
            return

        current_row = selected_rows[0]
        if current_row < self.items_table.rowCount() - 1:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            self.swap_table_rows(current_row, current_row + 1)
            self.items_for_installation[current_row], self.items_for_installation[current_row + 1] = \
                self.items_for_installation[current_row + 1], self.items_for_installation[current_row]
            self.items_table.selectRow(current_row + 1)
            self.items_table.itemChanged.connect(self.on_table_item_changed)

    def swap_table_rows(self, row1: int, row2: int):
        row1_items = [self.items_table.takeItem(row1, col) for col in range(self.items_table.columnCount())]
        row2_items = [self.items_table.takeItem(row2, col) for col in range(self.items_table.columnCount())]

        for col in range(self.items_table.columnCount()):
            self.items_table.setItem(row2, col, row1_items[col])
            self.items_table.setItem(row1, col, row2_items[col])

    def update_installation_button_state(self):
        """Habilita/deshabilita el boton de instalacion si hay elementos marcados."""
        any_checked = False
        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 0).checkState() == Qt.Checked:
                any_checked = True
                break
        self.btn_install.setEnabled(any_checked)

    def start_installation(self):
        """Inicia el proceso de instalación de los elementos seleccionados."""
        current_config_name = self.config_manager.configs.get("last_used")
        config = self.config_manager.get_config(current_config_name)

        if not config:
            QMessageBox.critical(self, "Error", "No se ha seleccionado ninguna configuración de Wine/Proton o es inválida.")
            return

        items_to_process_data_for_thread = []
        for row in range(self.items_table.rowCount()):
            item_data = self.items_for_installation[row]
            checkbox_item = self.items_table.item(row, 0)

            if checkbox_item.checkState() == Qt.Checked:
                # IMPORTANT: Now pass the user_defined_name as the third element
                items_to_process_data_for_thread.append((item_data['path'], item_data['type'], item_data['name']))
                item_data['current_status'] = "Pendiente" 
                self.items_table.item(row, 3).setText("Pendiente") 
                self.items_table.item(row, 3).setForeground(QColor(STYLE_STEAM_DECK["dark_palette"]["text"]) if self.config_manager.get_theme() == "dark" else QColor(STYLE_STEAM_DECK["light_palette"]["text"]))
            else:
                item_data['current_status'] = "Omitido"
                self.items_table.item(row, 3).setText("Omitido")
                self.items_table.item(row, 3).setForeground(QColor("darkorange"))


        if not items_to_process_data_for_thread:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron elementos para instalar. Marca los elementos que deseas instalar.")
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
                return 

        try:
            env = self.config_manager.get_current_environment(current_config_name)
        except Exception as e:
            QMessageBox.critical(self, "Error de Entorno", f"No se pudo configurar el entorno para la instalación:\n{str(e)}")
            return
            
        self.installer_thread = InstallerThread(
            items_to_process_data_for_thread, # Pass the filtered and prepared list in new format
            env,
            silent_mode=self.silent_mode,
            force_mode=self.force_mode, 
            winetricks_path=self.config_manager.get_winetricks_path(),
            config_manager=self.config_manager
        )
        
        self.installer_thread.progress.connect(self.update_progress)
        self.installer_thread.finished.connect(self.installation_finished)
        self.installer_thread.error.connect(self.show_installation_error)
        self.installer_thread.canceled.connect(self.on_installation_canceled)

        self.btn_install.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_select_components.setEnabled(False)
        self.btn_add_custom.setEnabled(False)
        self.btn_manage_custom.setEnabled(False)
        
        self.installer_thread.start()

    def _create_prefix(self, config: dict, config_name: str, prefix_path: Path):
        """Crea un nuevo prefijo de Wine/Proton y lo inicializa."""
        prefix_path.mkdir(parents=True, exist_ok=True, mode=0o755)
        env = self.config_manager.get_current_environment(config_name)

        wine_executable = env.get("WINE")
        if not wine_executable or not Path(wine_executable).is_file():
            raise FileNotFoundError(f"Ejecutable de Wine no encontrado: {wine_executable}")

        progress_dialog = QProgressDialog("Inicializando Prefijo de Wine/Proton...", "Cancelar", 0, 0, self) 
        progress_dialog.setWindowTitle("Inicializacion del Prefijo")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None) 
        progress_dialog.show() 

        try:
            process = subprocess.Popen(
                ["konsole", "--noclose", "-e", wine_executable, "wineboot"],
                env=env,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True
            )
            log_output = ""
            for line in process.stdout:
                log_output += line
                QApplication.processEvents() 
            process.wait(timeout=60) 
            
            self.config_manager.write_to_log("Creacion del Prefijo", f"Salida de Wineboot para {config_name}:\n{log_output}")
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "wineboot", output=log_output)

        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception("La inicializacion del prefijo de Wine/Proton agoto el tiempo de espera.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"No se pudo inicializar el prefijo de Wine/Proton. Codigo de salida: {e.returncode}\nSalida: {e.output}")
        finally:
            progress_dialog.close()

    def update_progress(self, name: str, status: str):
        """Actualiza el estado de un elemento en la tabla y en el modelo interno."""
        # First, update the internal data model
        found_in_model = False
        for item_data in self.items_for_installation:
            # Match against the 'name' field in our internal model
            if item_data['name'] == name:
                item_data['current_status'] = status
                found_in_model = True
                break
        
        if not found_in_model:
            print(f"DEBUG: Item '{name}' not found in internal items_for_installation list for status update.")

        # Then, update the table's visual representation
        for row in range(self.items_table.rowCount()):
            # Match by the displayed name in the table
            if self.items_table.item(row, 1).text() == name:
                status_item = self.items_table.item(row, 3)
                if status_item: # Ensure item exists
                    status_item.setText(status)
                    if "Error" in status:
                        status_item.setForeground(QColor(255, 0, 0)) # Red
                    elif "Finalizado" in status:
                        status_item.setForeground(QColor(0, 128, 0)) # Green
                    elif "Cancelado" in status:
                        status_item.setForeground(QColor("orange")) # Orange
                    else: # Pending, Installing...
                        theme = self.config_manager.get_theme()
                        status_item.setForeground(QColor(STYLE_STEAM_DECK["dark_palette"]["text"]) if theme == "dark" else QColor(STYLE_STEAM_DECK["light_palette"]["text"]))
                else:
                    print(f"DEBUG: Status item is None for row {row}, name '{name}'.")
                break # Stop after finding and updating the item in the table

    def on_installation_canceled(self, item_name: str):
        """Actualiza el estado de un elemento cuando la instalación es cancelada."""
        # Update internal model
        for item_data in self.items_for_installation:
            if item_data['name'] == item_name:
                item_data['current_status'] = "Cancelado"
                break

        # Update table display
        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 1).text() == item_name:
                status_item = self.items_table.item(row, 3)
                checkbox_item = self.items_table.item(row, 0)
                if status_item:
                    status_item.setText("Cancelado")
                    status_item.setForeground(QColor("orange"))
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Checked) # Keep checked to allow re-attempt
                break

    def installation_finished(self):
        """Maneja el estado final de la instalación, actualizando la GUI y mostrando un resumen."""
        installed_count = 0
        failed_count = 0
        skipped_count = 0
        
        # Disconnect itemChanged signal to prevent unintended updates when updating checkboxes
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass

        # Iterate through the *internal data model* (self.items_for_installation)
        # to get accurate counts and update table checkboxes
        for row, item_data in enumerate(self.items_for_installation):
            current_status = item_data['current_status']
            checkbox_item = self.items_table.item(row, 0) # Get the checkbox for the corresponding row

            if "Finalizado" in current_status:
                installed_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Unchecked) # Desmarcar elementos exitosos
            elif "Error" in current_status or "Cancelado" in current_status:
                failed_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Checked) # Keep checkbox checked for failed/canceled items, so user can retry
            elif "Omitido" in current_status:
                skipped_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Unchecked) # Keep checkbox unchecked for skipped items

        # Reconnect the signal
        self.items_table.itemChanged.connect(self.on_table_item_changed)

        # Re-enable controls
        self.btn_install.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_select_components.setEnabled(True)
        self.btn_add_custom.setEnabled(True)
        self.btn_manage_custom.setEnabled(True)

        QMessageBox.information(
            self,
            "Instalacion Completada",
            f"Resumen de la Instalacion:\n\n"
            f"• Instalado exitosamente: {installed_count}\n"
            f"• Fallido o Cancelado: {failed_count}\n"
            f"• Omitido (no seleccionado): {skipped_count}\n\n"
            f"Los elementos instalados exitosamente han sido deseleccionados de la lista."
        )
        self.update_installation_button_state()

    def show_installation_error(self, message: str):
        """Muestra un mensaje de error critico durante la instalacion y restablece los controles."""
        QMessageBox.critical(self, "Error de Instalacion", message)
        # Asegurarse de que los botones se vuelvan a habilitar despues de un error
        self.btn_install.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_select_components.setEnabled(True)
        self.btn_add_custom.setEnabled(True)
        self.btn_manage_custom.setEnabled(True)
        self.update_installation_button_state()


    def open_winetricks(self):
        """Abre la GUI de Winetricks para el prefijo actual."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            winetricks_path = self.config_manager.get_winetricks_path()
            
            subprocess.Popen([winetricks_path, "--gui"], env=env)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Winetricks: {str(e)}")

    def open_shell(self):
        """Abre una terminal (Konsole) con el entorno de Wine/Proton configurado."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            subprocess.Popen(["konsole"], env=env)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la terminal: {str(e)}")
            
    def open_prefix_folder(self):
        """Abre la carpeta del prefijo de Wine/Proton en el explorador de archivos."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config_name)
            
            if config and "prefix" in config:
                prefix_path = Path(config["prefix"])
                if prefix_path.exists():
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(prefix_path)))
                else:
                    QMessageBox.warning(self, "Advertencia", f"El prefijo '{prefix_path}' no existe. Por favor, asegurate de que este configurado o crealo.")
            else:
                QMessageBox.warning(self, "Advertencia", "No hay ningun prefijo configurado para el entorno actual.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la carpeta del prefijo: {str(e)}")
            
    def open_explorer(self):
        """Ejecuta wine explorer para el prefijo actual."""
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
                    
                    subprocess.Popen([wine_executable, "explorer"], env=env)
                else:
                    QMessageBox.warning(self, "Advertencia", f"El prefijo '{prefix_path}' no existe. Por favor, asegurate de que este configurado o crealo.")
            else:
                QMessageBox.warning(self, "Advertencia", "No hay ningun prefijo configurado para el entorno actual.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el Explorador de Wine: {str(e)}")
            
    def open_winecfg(self):
        """Ejecuta winecfg para el prefijo actual."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            
            wine_executable = env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")
                
            subprocess.Popen([wine_executable, "winecfg"], env=env)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Winecfg: {str(e)}")


if __name__ == "__main__":
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    config_manager = ConfigManager()
    installer = InstallerApp(config_manager)
    
    # Ajustar el tamano de la ventana al tamano de la pantalla si es demasiado grande
    screen = app.primaryScreen().availableGeometry()
    window_size = config_manager.get_window_size()
    
    if window_size.width() > screen.width() * 0.9 or window_size.height() > screen.height() * 0.9:
        installer.resize(int(screen.width() * 0.8), int(screen.height() * 0.8))
    else:
        installer.resize(window_size)
        
    installer.show()
    sys.exit(app.exec_())