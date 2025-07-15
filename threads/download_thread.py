import shutil
from urllib.request import urlopen, Request, HTTPError
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

from config_manager import ConfigManager

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url: str, destination_path: Path, name: str, config_manager: ConfigManager, config_name: str):
        super().__init__()
        self.url = url
        self.destination = destination_path
        self.name = name
        self.config_manager = config_manager
        self.config_name = config_name 
        self._is_running = True

    def run(self):
        log_source = f"Download-{self.name}"
        self.config_manager.write_to_log(self.config_name, log_source, f"Iniciando descarga de {self.url} a {self.destination}")
        try:
            req = Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=30) as response:
                if response.getcode() != 200:
                    raise HTTPError(self.url, response.getcode(), response.reason, response.headers, None)

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192

                free_space = shutil.disk_usage(self.destination.parent).free
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
                    if self.destination.exists():
                        try:
                            self.destination.unlink()
                        except OSError:
                            pass
                    self.config_manager.write_to_log(self.config_name, log_source, f"Descarga de {self.name} cancelada.")
                    return

                self.finished.emit(str(self.destination))
                self.config_manager.write_to_log(self.config_name, log_source, f"Descarga de {self.name} completada.")

        except HTTPError as e:
            msg = f"Error HTTP descargando {self.url}: {e.code} - {e.reason}"
            self.config_manager.write_to_log(self.config_name, log_source, f"ERROR: {msg}")
            self.error.emit(msg)
        except Exception as e:
            msg = f"Error inesperado durante la descarga de {self.name}: {str(e)}"
            self.config_manager.write_to_log(self.config_name, log_source, f"ERROR: {msg}")
            if self.destination.exists():
                try:
                    self.destination.unlink()
                except OSError:
                    pass
            self.error.emit(msg)

    def stop(self):
        """Detiene la descarga."""
        self._is_running = False