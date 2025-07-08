import os
import shutil
import time
import tarfile
import zipfile
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
                # Verificar código de respuesta HTTP
                if response.getcode() != 200:
                    raise Exception(f"Error HTTP {response.getcode()}: {response.reason}")
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192
                
                # Verificar espacio en disco antes de descargar
                dest_path = Path(self.destination)
                if dest_path.exists():
                    dest_path.unlink()  # Eliminar si ya existe
                
                required_space = total_size if total_size > 0 else 100 * 1024 * 1024  # 100MB si tamaño desconocido
                stat = os.statvfs(dest_path.parent)
                free_space = stat.f_frsize * stat.f_bavail
                
                if free_space < required_space * 1.1:  # 10% más por seguridad
                    raise Exception(f"No hay suficiente espacio en disco. Se necesitan {required_space/1024/1024:.1f} MB")
                
                with open(self.destination, 'wb') as f:
                    while True:
                        if not self._is_running:
                            # Eliminar archivo parcial si se cancela
                            if dest_path.exists():
                                dest_path.unlink()
                            return
                        
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                            
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = int(downloaded * 100 / total_size)
                            self.progress.emit(progress)
            
            self.finished.emit(str(self.destination))
        
        except Exception as e:
            # Eliminar archivo parcial si hubo error
            if Path(self.destination).exists():
                try:
                    Path(self.destination).unlink()
                except Exception:
                    pass
            self.error.emit(f"Error downloading {self.url}: {str(e)}")
    
    def stop(self):
        self._is_running = False

class DecompressThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, archive_path, config_manager):
        super().__init__()
        self.archive_path = archive_path
        self.config_manager = config_manager
        self._is_running = True
        
    def run(self):
        try:
            path = Path(self.archive_path)
            if not path.exists():
                raise FileNotFoundError(f"El archivo {path} no existe")
                
            dest_dir = path.parent
            
            # Verificar espacio en disco antes de descomprimir (aproximadamente 3x el tamaño del archivo)
            stat = os.statvfs(dest_dir)
            free_space = stat.f_frsize * stat.f_bavail
            archive_size = path.stat().st_size
            required_space = archive_size * 3
            
            if free_space < required_space:
                raise Exception(f"No hay suficiente espacio en disco. Se necesitan al menos {required_space/1024/1024:.1f} MB")
            
            # Mostrar progreso para archivos grandes
            if path.suffixes == ['.tar', '.gz'] or path.suffix == '.tgz':
                with tarfile.open(path, "r:gz") as tar:
                    members = tar.getmembers()
                    total = len(members)
                    for i, member in enumerate(members, 1):
                        if not self._is_running:
                            self.clean_partial_extraction(dest_dir, members[:i])
                            return
                        tar.extract(member, path=dest_dir)
            
            elif path.suffixes == ['.tar', '.xz'] or path.suffix == '.txz':
                with tarfile.open(path, "r:xz") as tar:
                    members = tar.getmembers()
                    total = len(members)
                    for i, member in enumerate(members, 1):
                        if not self._is_running:
                            self.clean_partial_extraction(dest_dir, members[:i])
                            return
                        tar.extract(member, path=dest_dir)
            
            elif path.suffix == '.zip':
                with zipfile.ZipFile(path, 'r') as zip_ref:
                    file_list = zip_ref.infolist()
                    total = len(file_list)
                    for i, file_info in enumerate(file_list, 1):
                        if not self._is_running:
                            self.clean_partial_extraction(dest_dir, file_list[:i])
                            return
                        zip_ref.extract(file_info, dest_dir)
            
            else:
                raise ValueError(f"Formato no soportado: {path}")
                
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f"Error al descomprimir {self.archive_path}: {str(e)}")
            
    def clean_partial_extraction(self, dest_dir, extracted_items):
        """Elimina archivos extraídos parcialmente si se cancela la operación"""
        try:
            for item in extracted_items:
                item_path = Path(dest_dir) / item.name
                if item_path.exists():
                    if item_path.is_dir():
                        shutil.rmtree(item_path)
                    else:
                        item_path.unlink()
        except Exception as e:
            print(f"Error al limpiar extracción parcial: {e}")
            
    def stop(self):
        self._is_running = False