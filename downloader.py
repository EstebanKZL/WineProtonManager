import os
import ssl
import shutil
import tarfile
import zipfile
import tempfile
from urllib.request import urlopen, Request, HTTPError
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal

# Deshabilitar verificacion SSL para casos especificos (descargas, APIs).
# Esto debe usarse con precaucion, solo si las fuentes son de confianza.
ssl._create_default_https_context = ssl._create_unverified_context

class DownloadThread(QThread):
    progress = pyqtSignal(int) # % de progreso
    finished = pyqtSignal(str) # Ruta al archivo descargado
    error = pyqtSignal(str)
    
    def __init__(self, url: str, destination_path: Path, name: str, config_manager):
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
    
    def __init__(self, archive_path: str, config_manager, name: str):
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
