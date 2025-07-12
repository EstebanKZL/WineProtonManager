import sys
import os
import subprocess
import json
import re
import time
from pathlib import Path

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget
from PyQt5.QtCore import QSize


# Importar estilos para aplicar
from styles import STYLE_BREEZE, COLOR_BREEZE_PRIMARY, apply_breeze_style_to_widget

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

        self.wine_download_dir = self.config_dir / "Wine"
        self.proton_download_dir = self.config_dir / "Proton"
        self.wine_download_dir.mkdir(exist_ok=True)
        self.proton_download_dir.mkdir(exist_ok=True)
        self.programs_dir = self.config_dir / "Programas"
        self.programs_dir.mkdir(exist_ok=True)

        self.backup_dir = self.config_dir / "Backup"
        self.backup_dir.mkdir(exist_ok=True)

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
            "automatic_backup_enabled": False,
            "ask_for_backup_before_action": True
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
            self.configs["settings"].setdefault(key, value)

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
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error cargando el archivo de configuración {self.config_file}: {e}. Se usará la configuración por defecto.")
            return {}

    def save_configs(self):
        """Guarda las configuraciones en el archivo JSON con manejo de errores."""
        try:
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
        # El guardado se hará solo cuando el usuario haga clic en "Guardar Ajustes" en el diálogo de configuración
        # self.save_configs() # [MODIFICACIÓN 3] Comentado para evitar el guardado inmediato.

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

    def set_automatic_backup_enabled(self, enabled: bool):
        """Establece si el backup automático está habilitado y guarda la configuración."""
        self.configs.setdefault("settings", {})["automatic_backup_enabled"] = enabled
        self.save_configs()

    def get_automatic_backup_enabled(self) -> bool:
        """Obtiene si el backup automático está habilitado. Por defecto es False."""
        return self.configs.get("settings", {}).get("automatic_backup_enabled", False)

    def set_ask_for_backup_before_action(self, enabled: bool):
        """Establece si se pregunta por backup antes de una acción y guarda la configuración."""
        self.configs.setdefault("settings", {})["ask_for_backup_before_action"] = enabled
        self.save_configs()

    def get_ask_for_backup_before_action(self) -> bool:
        """Obtiene si se pregunta por backup antes de una acción. Por defecto es True."""
        return self.configs.get("settings", {}).get("ask_for_backup_before_action", True)

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
        """Obtiene la lista de componentes de winetricks instalados en un prefijo."""
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
        """Guarda el tamaño de la ventana."""
        self.configs.setdefault("settings", {})["window_size"] = [size.width(), size.height()]
        self.save_configs()

    def get_window_size(self) -> QSize:
        """Obtiene el tamaño de ventana guardado. Por defecto es 900x650."""
        size = self.configs.get("settings", {}).get("window_size", [900, 650])
        return QSize(size[0], size[1])

    def get_log_path(self, program_name: str) -> Path:
        """Obtiene la ruta al archivo de registro para un programa específico."""
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

    def get_backup_log_path(self) -> Path:
        """Obtiene la ruta al archivo de registro de backup."""
        current_config_name = self.configs.get("last_used", "default")
        log_sub_dir = self.log_dir / current_config_name
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

    def apply_breeze_style_to_widget(self, widget: QWidget):
        """Aplica el estilo Breeze a un widget y sus hijos de forma recursiva."""
        apply_breeze_style_to_widget(widget, self)
