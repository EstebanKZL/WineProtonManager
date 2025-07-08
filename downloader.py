import os
import shutil
import time
import tarfile
import zipfile
import tempfile
from pathlib import Path
from urllib.request import urlopen, Request
from PyQt5.QtCore import QThread, pyqtSignal


class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, destination, config_manager):
        super().__init__()
        self.url = url
        self.destination = destination
        self.config_manager = config_manager
        self._is_running = True

    def run(self):
        try:
            req = Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req) as response:
                if response.getcode() != 200:
                    raise Exception(f"Error HTTP {response.getcode()}: {response.reason}")

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192

                dest_path = Path(self.destination)
                if dest_path.exists():
                    dest_path.unlink()

                required_space = total_size if total_size > 0 else 100 * 1024 * 1024
                stat = os.statvfs(dest_path.parent)
                free_space = stat.f_frsize * stat.f_bavail

                if free_space < required_space * 1.1:
                    raise Exception(f"No hay suficiente espacio en disco. Se necesitan {required_space/1024/1024:.1f} MB")

                with open(self.destination, 'wb') as f:
                    while self._is_running:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            self.progress.emit(int(downloaded * 100 / total_size))

            if self._is_running:
                self.finished.emit(str(self.destination))

        except Exception as e:
            if Path(self.destination).exists():
                try:
                    Path(self.destination).unlink()
                except Exception:
                    pass
            self.error.emit(f"Error downloading {self.url}: {str(e)}")

    def stop(self):
        self._is_running = False

class DecompressThread(QThread):
    finished = pyqtSignal(str)  # Emitir la ruta del directorio descomprimido
    error = pyqtSignal(str)
    progress = pyqtSignal(int)  # Para mostrar progreso si es necesario

    def __init__(self, archive_path, config_manager):
        super().__init__()
        self.archive_path = Path(archive_path)
        self.config_manager = config_manager
        self._is_running = True
        self.target_dir = None

    def set_permissions(self, path):
        """Función recursiva para establecer permisos"""
        try:
            if path.is_dir():
                os.chmod(path, 0o775)  # Permisos para directorios
                for item in path.iterdir():
                    self.set_permissions(item)
            else:
                os.chmod(path, 0o775)  # Permisos para archivos
        except Exception as e:
            print(f"Error al establecer permisos en {path}: {e}")

    def run(self):
        try:
            if not self.archive_path.exists():
                raise FileNotFoundError(f"El archivo {self.archive_path} no existe")

            dest_dir = self.archive_path.parent

            # Verificar espacio en disco
            stat = os.statvfs(dest_dir)
            free_space = stat.f_frsize * stat.f_bavail
            archive_size = self.archive_path.stat().st_size
            required_space = archive_size * 3

            if free_space < required_space:
                raise Exception(f"No hay suficiente espacio en disco. Se necesitan al menos {required_space/1024/1024:.1f} MB")

            # Extraer base name
            base_name = self.archive_path.stem
            tmp_path = self.archive_path
            while tmp_path.suffix:
                tmp_path = tmp_path.with_suffix("")
                base_name = tmp_path.name

            with tempfile.TemporaryDirectory(prefix="wpm_") as temp_dir:
                temp_dir = Path(temp_dir)

                # Descomprimir en tmp
                if self.archive_path.suffixes[-2:] == ['.tar', '.gz'] or self.archive_path.suffix == '.tgz':
                    with tarfile.open(self.archive_path, "r:gz") as tar:
                        tar.extractall(path=temp_dir, filter='data')
                elif self.archive_path.suffixes[-2:] == ['.tar', '.xz'] or self.archive_path.suffix == '.txz':
                    with tarfile.open(self.archive_path, "r:xz") as tar:
                        tar.extractall(path=temp_dir, filter='data')
                elif self.archive_path.suffix == '.zip':
                    with zipfile.ZipFile(self.archive_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                else:
                    file_output = subprocess.run(["file", "-b", str(self.archive_path)],
                                              capture_output=True, text=True).stdout
                    if 'XZ compressed data' in file_output:
                        with tarfile.open(self.archive_path, "r:xz") as tar:
                            tar.extractall(path=temp_dir, filter='data')
                    else:
                        raise ValueError(f"Formato no soportado: {self.archive_path}")

                # Establecer permisos en el directorio temporal ANTES de mover
                self.set_permissions(temp_dir)

                # Mover contenido al destino final
                contents = list(temp_dir.iterdir())
                if len(contents) == 1 and contents[0].is_dir():
                    self.target_dir = dest_dir / contents[0].name
                    if self.target_dir.exists():
                        shutil.rmtree(self.target_dir)
                    shutil.move(str(contents[0]), str(self.target_dir))
                else:
                    self.target_dir = dest_dir / base_name
                    if self.target_dir.exists():
                        shutil.rmtree(self.target_dir)
                    self.target_dir.mkdir(parents=True, exist_ok=True)
                    for item in contents:
                        shutil.move(str(item), str(self.target_dir / item.name))

                # Establecer permisos nuevamente en el destino final por seguridad
                self.set_permissions(self.target_dir)

            # Eliminar archivo comprimido si existe
            try:
                if self.archive_path.exists():
                    self.archive_path.unlink()
            except Exception as e:
                print(f"No se pudo eliminar archivo comprimido: {e}")

            self.finished.emit(str(self.target_dir))

        except Exception as e:
            # Limpieza en caso de error
            try:
                if self.target_dir and self.target_dir.exists():
                    shutil.rmtree(self.target_dir, ignore_errors=True)
            except Exception as cleanup_error:
                print(f"Error al limpiar: {cleanup_error}")

            self.error.emit(f"Error al descomprimir {self.archive_path}: {str(e)}")

    def stop(self):
        self._is_running = False
