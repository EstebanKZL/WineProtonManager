import os
import json
import re
import time
import subprocess
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QFileDialog, QMessageBox, QTableWidget, QPushButton
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QSize

from styles import STYLE_STEAM_DECK # Import the style constants

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

    def apply_theme_to_dialog(self, dialog: QDialog | QFileDialog | QWidget):
        """Aplica el tema actual (claro/oscuro) a un dialogo o widget de Qt."""
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
        # Asegurar que los botones en QFileDialog y otros dialogos tambien usen el estilo
        for btn in dialog.findChildren(QPushButton):
            btn.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme == "dark" else STYLE_STEAM_DECK["button_style"])
        
        # Apply font to all children widgets in the dialog
        for widget in dialog.findChildren(QWidget):
            widget.setFont(STYLE_STEAM_DECK["font"])

        # Special handling for QTableWidget to apply the correct theme style
        for table_widget in dialog.findChildren(QTableWidget):
            table_widget.setStyleSheet(STYLE_STEAM_DECK["dark_table_style"] if theme == "dark" else STYLE_STEAM_DECK["table_style"])
