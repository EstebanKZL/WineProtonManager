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

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QApplication
from config_manager import ConfigManager

# Deshabilitar verificación SSL (usar con precaución y solo si las fuentes son de confianza).
ssl._create_default_https_context = ssl._create_unverified_context

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