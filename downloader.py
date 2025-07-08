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

        # Determinar directorio base (Wine o Proton)
        base_dir = self.wine_download_dir if "wine" in path.name.lower() else self.proton_download_dir
        
        # Obtener nombre de carpeta destino (nombre archivo sin extensiones)
        folder_name = path.stem
        while path.suffix:
            path = Path(path.stem)  # Quitar extensiones múltiples (.tar.gz)
            folder_name = path.stem
        
        target_dir = base_dir / folder_name

        # Verificar espacio en disco antes de descomprimir (aproximadamente 3x el tamaño del archivo)
        stat = os.statvfs(str(base_dir))
        free_space = stat.f_frsize * stat.f_bavail
        archive_size = Path(self.archive_path).stat().st_size
        required_space = archive_size * 3
        
        if free_space < required_space:
            raise Exception(f"No hay suficiente espacio en disco. Se necesitan al menos {required_space/1024/1024:.1f} MB")

        # Crear directorio temporal seguro
        with tempfile.TemporaryDirectory(prefix="wpm_") as temp_dir:
            temp_dir = Path(temp_dir)
            
            # Descompresión según formato con progreso
            if str(self.archive_path).endswith(('.tar.gz', '.tgz')):
                with tarfile.open(str(self.archive_path), "r:gz") as tar:
                    members = tar.getmembers()
                    total = len(members)
                    for i, member in enumerate(members, 1):
                        if not self._is_running:
                            self.clean_partial_extraction(temp_dir, members[:i])
                            return
                        tar.extract(member, path=str(temp_dir))
                        
            elif str(self.archive_path).endswith(('.tar.xz', '.txz')):
                try:
                    with tarfile.open(str(self.archive_path), "r:xz") as tar:
                        members = tar.getmembers()
                        total = len(members)
                        for i, member in enumerate(members, 1):
                            if not self._is_running:
                                self.clean_partial_extraction(temp_dir, members[:i])
                                return
                            tar.extract(member, path=str(temp_dir))
                except ImportError:
                    # Alternativa con subprocess si no hay soporte para xz
                    subprocess.run(
                        ["tar", "-xJf", str(self.archive_path), "-C", str(temp_dir)],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
            elif str(self.archive_path).endswith('.zip'):
                with zipfile.ZipFile(str(self.archive_path), 'r') as zip_ref:
                    file_list = zip_ref.infolist()
                    total = len(file_list)
                    for i, file_info in enumerate(file_list, 1):
                        if not self._is_running:
                            self.clean_partial_extraction(temp_dir, file_list[:i])
                            return
                        zip_ref.extract(file_info, str(temp_dir))
                    
            else:
                raise ValueError(f"Formato no soportado: {self.archive_path}")

            # Mover contenido al directorio final
            contents = list(temp_dir.iterdir())
            
            # Caso 1: El archivo creó una carpeta con el mismo nombre
            if len(contents) == 1 and contents[0].name == folder_name:
                shutil.move(str(contents[0]), str(target_dir))
            
            # Caso 2: Contenido directo
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                for item in contents:
                    shutil.move(str(item), str(target_dir / item.name))

        # Asignar permisos 775 recursivamente
        for root, dirs, files in os.walk(str(target_dir)):
            for d in dirs:
                os.chmod(Path(root) / d, 0o775)
            for f in files:
                os.chmod(Path(root) / f, 0o775)

        # Eliminar archivo comprimido tras éxito
        Path(self.archive_path).unlink(missing_ok=True)
        self.finished.emit()
        
    except Exception as e:
        # Limpiar en caso de error
        shutil.rmtree(str(target_dir), ignore_errors=True)
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
