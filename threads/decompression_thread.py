import os
import shutil
import tarfile
import zipfile
import tempfile
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

from config_manager import ConfigManager

class DecompressionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, archive_path: str, config_manager: ConfigManager, name: str, config_name: str):
        super().__init__()
        self.archive_path = Path(archive_path)
        self.config_manager = config_manager
        self.name = name
        self.config_name = config_name
        self.target_dir = None
        self._is_running = True

    def _set_permissions_recursively(self, path: Path):
        """Aplica permisos 0o755 (ejecutable para todos) a directorios y archivos específicos, 0o644 a otros archivos."""
        log_source = f"Decompress-{self.name}"
        if not path.exists():
            return
        try:
            if path.is_dir():
                os.chmod(path, 0o755)
                for item in path.iterdir():
                    self._set_permissions_recursively(item)
            elif path.is_file():
                if "bin" in path.parts or "wine" in path.name.lower() or "wineserver" in path.name.lower():
                    os.chmod(path, 0o755)
                else:
                    os.chmod(path, 0o644)
        except OSError as e:
            self.config_manager.write_to_log(self.config_name, log_source, f"Advertencia: No se pudieron establecer permisos en {path}: {e}")

    def run(self):
        log_source = f"Decompress-{self.name}"
        self.config_manager.write_to_log(self.config_name, log_source, f"Iniciando descompresión de {self.archive_path}")
        try:
            if not self.archive_path.exists():
                raise FileNotFoundError(f"El archivo {self.archive_path} no existe.")

            dest_dir_root = self.archive_path.parent
            base_name = self.archive_path.stem
            if self.archive_path.suffix in ['.gz', '.xz', '.zip'] and base_name.endswith('.tar'):
                base_name = Path(base_name).stem
            self.target_dir = dest_dir_root / base_name

            if self.target_dir.exists():
                self.config_manager.write_to_log(self.config_name, log_source, f"El directorio de destino {self.target_dir} ya existe. Eliminando...")
                shutil.rmtree(self.target_dir)

            with tempfile.TemporaryDirectory(prefix="wpm_decompress_") as temp_unzip_dir_str:
                temp_unzip_dir = Path(temp_unzip_dir_str)
                self.config_manager.write_to_log(self.config_name, log_source, f"Descomprimiendo al directorio temporal: {temp_unzip_dir}")

                if self.archive_path.suffix == '.zip':
                    with zipfile.ZipFile(self.archive_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_unzip_dir)
                elif self.archive_path.suffix in ['.gz', '.xz', '.bz2', '.zst'] or self.archive_path.name.endswith(('.tar.gz', '.tar.xz', '.tar.bz2', '.tar.zst')):
                    mode = "r:" + self.archive_path.suffix[1:]
                    with tarfile.open(self.archive_path, mode) as tar:
                        tar.extractall(path=temp_unzip_dir, filter='data')
                else:
                    raise ValueError(f"Formato de archivo no compatible para descompresión: {self.archive_path.suffix}")

                extracted_contents = list(temp_unzip_dir.iterdir())
                source_dir_to_move = extracted_contents[0] if len(extracted_contents) == 1 and extracted_contents[0].is_dir() else temp_unzip_dir

                self.config_manager.write_to_log(self.config_name, log_source, f"Moviendo {source_dir_to_move} a {self.target_dir}")
                shutil.move(str(source_dir_to_move), str(self.target_dir))
                self._set_permissions_recursively(self.target_dir)

            try:
                self.archive_path.unlink()
                self.config_manager.write_to_log(self.config_name, log_source, f"Archivo comprimido {self.archive_path} eliminado.")
            except OSError as e:
                self.config_manager.write_to_log(self.config_name, log_source, f"Advertencia: No se pudo eliminar el archivo comprimido {self.archive_path}: {e}")

            self.finished.emit(str(self.target_dir))
            self.config_manager.write_to_log(self.config_name, log_source, f"Descompresión de {self.name} completada. Ruta: {self.target_dir}")

        except Exception as e:
            msg = f"Error descomprimiendo {self.name}: {str(e)}"
            self.config_manager.write_to_log(self.config_name, log_source, f"ERROR: {msg}")
            if self.target_dir and self.target_dir.exists():
                try:
                    shutil.rmtree(self.target_dir, ignore_errors=True)
                    self.config_manager.write_to_log(self.config_name, log_source, f"Directorio incompleto {self.target_dir} eliminado después del error.")
                except OSError as cleanup_error:
                    self.config_manager.write_to_log(self.config_name, log_source, f"Error limpiando {self.target_dir}: {cleanup_error}")
            self.error.emit(msg)

    def stop(self):
        self._is_running = False