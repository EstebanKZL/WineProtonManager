import os
import subprocess
import shutil
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal, QProcess
from PyQt5.QtWidgets import QApplication

from config_manager import ConfigManager

class BackupThread(QThread):
    progress_update = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str, str)

    def __init__(self, source_path: Path, destination_path: Path, config_manager: ConfigManager, is_full_backup: bool, config_name: str):
        super().__init__()
        self.source_path = source_path
        self.destination_path = destination_path
        self.config_manager = config_manager
        self.is_full_backup = is_full_backup
        self.config_name = config_name
        self._is_running = True
        self._process: subprocess.Popen | None = None

    def run(self):
        log_source = "Backup"
        self.config_manager.write_to_log(self.config_name, log_source, f"Iniciando backup de '{self.source_path}' a '{self.destination_path}'")
        try:
            if not self.source_path.exists() or not self.source_path.is_dir():
                raise FileNotFoundError(f"La carpeta de origen del prefijo no existe: {self.source_path}")

            rsync_command = ["rsync", "-av", "--no-o", "--no-g"]
            final_backup_path_str = ""

            if not self.is_full_backup:
                rsync_command.append("--checksum")
                self.config_manager.write_to_log(self.config_name, log_source, "Realizando backup incremental con rsync --checksum.")
                rsync_command.extend([f"{self.source_path}/", str(self.destination_path)])
                final_backup_path_str = str(self.destination_path)
            else:
                self.config_manager.write_to_log(self.config_name, log_source, "Realizando backup completo (nueva carpeta con timestamp).")
                temp_backup_dir = self.destination_path.parent / (self.destination_path.name + "_tmp")
                temp_backup_dir.mkdir(parents=True, exist_ok=True)
                rsync_command.extend([f"{self.source_path}/", str(temp_backup_dir)])
                final_backup_path_str = str(self.destination_path)

            self.progress_update.emit("Iniciando sincronización...")
            self.config_manager.write_to_log(self.config_name, log_source, f"Comando rsync: {' '.join(rsync_command)}")
            self._process = subprocess.Popen(rsync_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True, preexec_fn=os.setsid)

            while self._process.poll() is None and self._is_running:
                line = self._process.stdout.readline()
                if line:
                    self.progress_update.emit(line.strip())
                else:
                    QThread.msleep(50)
                QApplication.processEvents()

            stdout, stderr = self._process.communicate()

            if not self._is_running:
                self.finished.emit(False, "Backup cancelado por el usuario.", "", self.config_name)
                self.config_manager.write_to_log(self.config_name, log_source, "Backup cancelado por el usuario.")
                if self.is_full_backup and 'temp_backup_dir' in locals() and temp_backup_dir.exists():
                    shutil.rmtree(temp_backup_dir, ignore_errors=True)
            elif self._process.returncode == 0:
                if self.is_full_backup:
                    shutil.move(str(temp_backup_dir), str(Path(final_backup_path_str)))
                    self.config_manager.set_last_full_backup_path(self.config_name, final_backup_path_str)
                    success_msg = f"Backup COMPLETO de '{self.source_path.name}' completado exitosamente a '{final_backup_path_str}'."
                else:
                    success_msg = f"Backup INCREMENTAL de '{self.source_path.name}' completado exitosamente a '{self.destination_path}'."
                self.config_manager.write_to_log(self.config_name, log_source, success_msg)
                self.finished.emit(True, success_msg, final_backup_path_str, self.config_name)
            else:
                error_msg = f"Rsync falló con código {self._process.returncode}.\nStderr: {stderr}\nStdout: {stdout}"
                self.config_manager.write_to_log(self.config_name, log_source, f"ERROR: {error_msg}")
                if self.is_full_backup and 'temp_backup_dir' in locals() and temp_backup_dir.exists():
                    shutil.rmtree(temp_backup_dir, ignore_errors=True)
                self.finished.emit(False, f"Error durante el backup: {stderr.strip() or stdout.strip()}", "", self.config_name)

        except FileNotFoundError as e:
            msg = f"Error: Comando rsync no encontrado o ruta de origen/destino inválida. Asegúrate de que rsync esté instalado. {e}"
            self.config_manager.write_to_log(self.config_name, log_source, f"ERROR: {msg}")
            self.finished.emit(False, msg, "", self.config_name)
        except Exception as e:
            msg = f"Error inesperado durante el backup: {str(e)}"
            self.config_manager.write_to_log(self.config_name, log_source, f"ERROR: {msg}")
            self.finished.emit(False, msg, "", self.config_name)

    def stop(self):
        self._is_running = False
        if self._process and self._process.poll() is None:
            try:
                os.killpg(os.getpgid(self._process.pid), subprocess.signal.SIGINT)
            except ProcessLookupError:
                pass
