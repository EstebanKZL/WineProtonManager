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
from pathlib import Path
from urllib.request import urlopen, Request

from PyQt5.QtCore import Qt, QSize

class ConfigManager:
    ssl._create_default_https_context = ssl._create_unverified_context
    """Gestor optimizado de configuraciones persistentes"""
    def __init__(self):
        config_dir = Path.home() / ".config" / "WineProtonManager"
        self.config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear directorio de logs si no existe
        log_dir = config_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Directorios para descargas
        self.wine_download_dir = config_dir / "Wine"
        self.proton_download_dir = config_dir / "Proton"
        self.wine_download_dir.mkdir(exist_ok=True)
        self.proton_download_dir.mkdir(exist_ok=True)
        
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
            "theme": "dark",  # Cambiado a dark por defecto para estilo Steam Deck
            "window_size": [900, 650],
            "silent_install": True  # Modo silencioso activado por defecto
        })
        
        # Configuración de repositorios por defecto
        if "repositories" not in self.configs:
            self.configs["repositories"] = {
                "proton": [
                    {
                        "name": "GloriousEggroll Proton",
                        "url": "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases",
                        "enabled": True
                    }
                ],
                "wine": [
                    {
                        "name": "Kron4ek Wine Builds",
                        "url": "https://api.github.com/repos/Kron4ek/Wine-Builds/releases",
                        "enabled": True
                    }
                ]
            }
        
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
                "theme": "dark",  # Cambiado a dark por defecto
                "window_size": [900, 650],
                "silent_install": True
            },
            "repositories": {
                "proton": [
                    {
                        "name": "GloriousEggroll Proton",
                        "url": "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases",
                        "enabled": True
                    }
                ],
                "wine": [
                    {
                        "name": "Kron4ek Wine Builds",
                        "url": "https://api.github.com/repos/Kron4ek/Wine-Builds/releases",
                        "enabled": True
                    }
                ]
            }
        }
        
        if not self.config_file.exists():
            return default
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                loaded.setdefault("custom_programs", default["custom_programs"])
                loaded.setdefault("settings", default["settings"])
                loaded.setdefault("repositories", default["repositories"])
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
        return self.configs["settings"].get("theme", "dark")  # Cambiado a dark por defecto
        
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
        wineprotonmanager_log = Path(prefix_path) / "wineprotonmanager.log"
        if not wineprotonmanager_log.exists():
            return []
        
        try:
            with open(wineprotonmanager_log, 'r', encoding='utf-8') as f:
                installed = []
                for line in f.readlines():
                    if line.strip() and "installed" in line.lower():
                        # Extraer solo el nombre del componente
                        parts = line.strip().split()
                        if len(parts) > 1:
                            # Tomar el último elemento (nombre del componente)
                            installed.append(parts[-1])
                return installed
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
    
    def get_repositories(self, type_):
        """Obtiene los repositorios para Wine o Proton"""
        return self.configs["repositories"].get(type_, [])
    
    def add_repository(self, type_, name, url):
        """Añade un nuevo repositorio"""
        if "repositories" not in self.configs:
            self.configs["repositories"] = {"wine": [], "proton": []}
        
        self.configs["repositories"][type_].append({
            "name": name,
            "url": url,
            "enabled": True
        })
        self.save_configs()
    
    def remove_repository(self, type_, index):
        """Elimina un repositorio"""
        if "repositories" in self.configs and type_ in self.configs["repositories"]:
            if 0 <= index < len(self.configs["repositories"][type_]):
                del self.configs["repositories"][type_][index]
                self.save_configs()
                return True
        return False
    
    def toggle_repository(self, type_, index, enabled):
        """Activa/desactiva un repositorio"""
        if "repositories" in self.configs and type_ in self.configs["repositories"]:
            if 0 <= index < len(self.configs["repositories"][type_]):
                self.configs["repositories"][type_][index]["enabled"] = enabled
                self.save_configs()
                return True
        return False

    def decompress_archive(self, archive_path):
        """Descomprime un archivo manteniendo los archivos existentes y solo borra el comprimido si tiene éxito"""
        path = Path(archive_path)
        dest_dir = path.parent
        
        try:
            # Extraer el nombre base sin extensiones para el directorio de destino
            base_name = path.stem  # Esto elimina solo la última extensión
            while base_name != path.stem:  # Para manejar múltiples extensiones como .tar.gz
                path = Path(base_name)
                base_name = path.stem
            
            target_dir = dest_dir / base_name
            
            # No eliminamos el directorio si ya existe - permitimos sobrescritura
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Manejo de diferentes formatos
            if path.suffixes[-2:] == ['.tar', '.gz'] or path.suffix == '.tgz':
                with tarfile.open(path, "r:gz") as tar:
                    tar.extractall(path=target_dir)
                    
            elif path.suffixes[-2:] == ['.tar', '.xz'] or path.suffix == '.txz':
                try:
                    with tarfile.open(path, "r:xz") as tar:
                        tar.extractall(path=target_dir)
                except ImportError:
                    # Fallback al comando tar del sistema
                    result = subprocess.run(
                        ["tar", "-xJf", str(path), "-C", str(target_dir)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    if result.returncode != 0:
                        print(f"Error con tar: {result.stderr.decode()}")
                        raise Exception(f"Error con tar: {result.stderr.decode()}")
                        
            elif path.suffix == '.zip':
                with zipfile.ZipFile(path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
                    
            else:
                # Último intento: verificar el tipo de archivo real
                file_output = subprocess.run(["file", "-b", str(path)], 
                                          capture_output=True, text=True).stdout
                if 'XZ compressed data' in file_output:
                    return self.decompress_archive(archive_path)
                print(f"Formato no soportado: {path}")
                return False
            
            # Asignar permisos adecuados
            for root, dirs, files in os.walk(target_dir):
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o755)
                for f in files:
                    os.chmod(os.path.join(root, f), 0o644)
            
            # Eliminar el archivo comprimido solo si todo fue bien
            try:
                path.unlink()
                print(f"Archivo comprimido eliminado: {path}")
            except Exception as e:
                print(f"No se pudo eliminar el archivo comprimido: {e}")
                # No es crítico, podemos continuar
            
            return True
            
        except Exception as e:
            print(f"Error al descomprimir {path}: {e}")
            # Intentar limpiar solo la extracción parcial si falló
            try:
                if target_dir.exists():
                    # Identificar archivos recién creados para eliminarlos
                    new_files = set(target_dir.glob('*')) - set(original_files)
                    for f in new_files:
                        if f.is_dir():
                            shutil.rmtree(f, ignore_errors=True)
                        else:
                            f.unlink(missing_ok=True)
            except Exception as cleanup_error:
                print(f"Error al limpiar: {cleanup_error}")
            
            return False