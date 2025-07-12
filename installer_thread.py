import sys
import os
import subprocess
import time
import tempfile
import shutil
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from config_manager import ConfigManager

class InstallerThread(QThread):
    progress = pyqtSignal(str, str) # Emite (nombre_del_elemento, estado)
    finished = pyqtSignal()
    error = pyqtSignal(str) # Ahora se usa para errores globales o al final del bucle
    item_error = pyqtSignal(str, str) # [MODIFICACIÓN 1] Nuevo: Emite (nombre_del_elemento, mensaje_de_error_específico) cuando falla un solo ítem.
    canceled = pyqtSignal(str) # Emite (nombre_del_elemento) cuando se cancela
    console_output = pyqtSignal(str) # Emite salida de consola en tiempo real

    def __init__(self, items_to_install: list[tuple[str, str, str]], env: dict, silent_mode: bool, force_mode: bool, winetricks_path: str, config_manager: ConfigManager):
        super().__init__()
        self.items_to_install = items_to_install # Lista de (ruta_o_nombre, tipo, nombre_mostrar)
        self.env = env
        self.silent_mode = silent_mode
        self.force_mode = force_mode
        self.winetricks_path = winetricks_path
        self.config_manager = config_manager
        self._is_running = True
        self.current_process: subprocess.Popen | None = None

    def run(self):
        try:
            # Verificar si wine/proton es accesible antes de empezar
            wine_executable = self.env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                # [MODIFICACIÓN 1] Emitir un error fatal si el ejecutable principal no se encuentra
                self.error.emit(f"Ejecutable de Wine/Proton no encontrado o no ejecutable: {wine_executable}")
                return

            # Verificar winetricks si se va a usar
            if any(item[1] in ["winetricks", "wtr"] for item in self.items_to_install):
                winetricks_executable = self.winetricks_path
                if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
                    # [MODIFICACIÓN 1] Emitir un error fatal si winetricks no se encuentra y se necesita
                    self.error.emit(f"Ejecutable de Winetricks no encontrado o no ejecutable: {winetricks_executable}")
                    return

        except EnvironmentError as e:
            self.error.emit(str(e))
            return

        for idx, (item_path_or_name, item_type, user_defined_name) in enumerate(self.items_to_install):
            if not self._is_running:
                self.canceled.emit(user_defined_name)
                # [MODIFICACIÓN 1] Ya no se usa 'break' aquí, la cancelación se maneja de forma más granular
                # El bucle termina si _is_running es False
                break # El bucle for debe terminar si se ha cancelado

            display_name_for_progress = user_defined_name

            self.progress.emit(display_name_for_progress, f"Instalando")
            self.config_manager.write_to_log(display_name_for_progress, f"Iniciando instalación: {item_path_or_name} (Tipo: {item_type}, Silencioso: {self.silent_mode}, Forzado: {self.force_mode})")

            temp_log_path = None # Se sigue usando temp_log_path para capturar stdout/stderr del proceso antes de agregarlo al log unificado.
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".log", mode='w+', encoding='utf-8') as temp_log_file:
                    temp_log_path = Path(temp_log_file.name)

                if item_type == "exe":
                    self._install_exe(item_path_or_name, temp_log_path, display_name_for_progress)
                elif item_type == "winetricks":
                    self._install_winetricks(item_path_or_name, temp_log_path, display_name_for_progress)
                elif item_type == "wtr":
                    self._install_winetricks_script(item_path_or_name, temp_log_path, display_name_for_progress)
                else:
                    raise ValueError(f"Tipo de instalación no reconocido: {item_type}")

                self._register_successful_installation(display_name_for_progress, item_type, item_path_or_name) # MODIFICACIÓN 3: Pasar item_type y item_path_or_name
                self.progress.emit(display_name_for_progress, f"Finalizado")
                self.config_manager.write_to_log(display_name_for_progress, f"Instalación de {display_name_for_progress} completada exitosamente.")

            except Exception as e:
                # [MODIFICACIÓN 1] Ahora emitimos 'item_error' y continuamos el bucle
                error_msg = f"Comando fallido para {display_name_for_progress}. Detalles:\n"
                if isinstance(e, subprocess.CalledProcessError):
                    error_msg += f"Comando: {' '.join(e.cmd)}\nCódigo de Salida: {e.returncode}\nSalida/Error: {e.output or e.stderr}"
                else:
                    error_msg += str(e)

                self.config_manager.write_to_log(display_name_for_progress, f"ERROR: DURANTE LA INSTALACIÓN: {error_msg}")
                self.progress.emit(display_name_for_progress, f"Error") # Actualiza el estado en la UI
                self.item_error.emit(display_name_for_progress, error_msg) # Emitir error específico del ítem
                # No se usa 'break', la instalación continúa con el siguiente ítem
            finally:
                if temp_log_path and temp_log_path.exists():
                    try:
                        temp_log_path.unlink() # Limpiar el archivo de log temporal
                        retcode_file = Path(str(temp_log_path) + ".retcode")
                        if retcode_file.exists():
                            retcode_file.unlink()
                    except OSError as e:
                        self.config_manager.write_to_log(display_name_for_progress, f"Advertencia: No se pudo eliminar el archivo temporal {temp_log_path}: {e}")

        # [MODIFICACIÓN 1] La señal 'finished' se emite solo cuando todos los ítems han sido procesados.
        if self._is_running: # Solo si no se ha cancelado globalmente
            self.finished.emit()

    def _install_exe(self, exe_path: str, temp_log_path: Path, display_name: str):
        """Ejecuta un archivo .exe usando Wine/Proton, capturando la salida."""
        exe_path = Path(exe_path)
        if not exe_path.exists():
            raise FileNotFoundError(f"El archivo EXE no existe: {exe_path}")

        wine_executable = self.env.get("WINE")
        # Ya verificado al inicio de run(), pero una doble verificación no hace daño
        if not wine_executable or not Path(wine_executable).is_file():
            raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")

        cmd = [wine_executable, str(exe_path)]
        self.config_manager.write_to_log(display_name, f"Comando EXE: {' '.join(cmd)}")
        self._execute_command_and_capture_output(cmd, display_name, temp_log_path)

    def _install_winetricks(self, component_name: str, temp_log_path: Path, display_name: str):
        """Ejecuta un comando de winetricks, capturando la salida."""
        winetricks_executable = self.winetricks_path
        if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
            raise FileNotFoundError(f"Ejecutable de Winetricks no encontrado: {winetricks_executable}")

        silent_flag = "-q" if self.silent_mode else ""
        force_flag = "--force" if self.force_mode else ""

        cmd = [winetricks_executable, silent_flag, force_flag, component_name]
        cmd = [c for c in cmd if c] # Elimina los flags vacíos

        self.config_manager.write_to_log(display_name, f"Comando Winetricks: {' '.join(cmd)}")
        self._execute_command_and_capture_output(cmd, display_name, temp_log_path)

    def _install_winetricks_script(self, script_path: str, temp_log_path: Path, display_name: str):
        """Ejecuta un script personalizado de Winetricks (.wtr), capturando la salida."""
        script_path = Path(script_path)
        if not script_path.exists():
            raise FileNotFoundError(f"El archivo de script de Winetricks no existe: {script_path}")

        winetricks_executable = self.winetricks_path
        if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
            raise FileNotFoundError(f"Ejecutable de Winetricks no encontrado: {winetricks_executable}")

        silent_flag = "-q" if self.silent_mode else ""
        force_flag = "--force" if self.force_mode else ""

        cmd = [winetricks_executable, silent_flag, force_flag, str(script_path)]
        cmd = [c for c in cmd if c] # Elimina los flags vacíos

        self.config_manager.write_to_log(display_name, f"Comando de script Winetricks: {' '.join(cmd)}")
        self._execute_command_and_capture_output(cmd, display_name, temp_log_path)

    def _execute_command_and_capture_output(self, cmd: list[str], display_name: str, temp_log_path: Path):
        """Ejecuta un comando, captura su salida y la emite para la ventana emergente."""
        try:
            self.current_process = subprocess.Popen(
                cmd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Capturar stdout y stderr juntos
                text=True, # Modo texto para unicode
                bufsize=1, # Line-buffered
                universal_newlines=True, # Para compatibilidad de saltos de línea
                preexec_fn=os.setsid # Crear un nuevo grupo de procesos para matar hijos
            )

            log_content = ""
            while True:
                line = self.current_process.stdout.readline()
                if not line:
                    break
                log_content += line
                self.console_output.emit(line.strip())
                QApplication.processEvents() # Permitir que la UI se actualice

            # Esperar a que el proceso termine después de leer toda la salida
            self.current_process.wait(timeout=300) # Tiempo de espera para la ejecución del comando

            retcode = self.current_process.returncode

            # Escribir el log completo al archivo temporal (esto es solo para debugging si se desea)
            with open(temp_log_path, 'w', encoding='utf-8') as f:
                f.write(log_content)

            self.config_manager.write_to_log(display_name, "=== INICIO DEL LOG DEL PROCESO ===")
            self.config_manager.write_to_log(display_name, log_content)
            self.config_manager.write_to_log(display_name, f"Código de retorno del proceso: {retcode}")
            self.config_manager.write_to_log(display_name, "=== FIN DEL LOG DEL PROCESO ===\n")

            if retcode != 0:
                raise subprocess.CalledProcessError(retcode, cmd, output=log_content)

        except subprocess.TimeoutExpired:
            self.current_process.kill() # Matar proceso si se excede el tiempo
            raise Exception("El comando de instalación agotó el tiempo de espera.")
        except subprocess.CalledProcessError as e:
            # Relanzar el error para que sea capturado por el manejador de errores principal
            raise e
        except Exception as e:
            raise Exception(f"Error inesperado al ejecutar comando: {str(e)}")

    def _register_successful_installation(self, display_name: str, item_type: str, original_path_or_name: str): # MODIFICACIÓN 3: Nuevos parámetros
        """
        MODIFICACIÓN 3: Registra una instalación exitosa en el log del prefijo (wineprotomanager.ini).
        Añade más contexto al registro.
        """
        prefix_path = Path(self.env["WINEPREFIX"])
        # MODIFICACIÓN 3: Cambiar a wineprotomanager.ini
        log_file = prefix_path / "wineprotonmanager.ini"
        try:
            # Usar un formato simple para el .ini
            entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} installed {display_name} (Type: {item_type}, Source: {original_path_or_name})"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{entry}\n")
        except IOError as e:
            self.config_manager.write_to_log(display_name, f"Advertencia: No se pudo escribir en el log del prefijo {log_file}: {e}")

    def stop(self):
        """Detiene la instalación, incluyendo el proceso hijo."""
        self._is_running = False
        if self.current_process and self.current_process.poll() is None:
            try:
                # Usar os.killpg para matar el grupo de procesos y asegurar que los hijos también mueran
                os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGTERM)
                self.current_process.wait(5) # Dar tiempo para terminar limpiamente
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if self.current_process.poll() is None: # Si aún no ha terminado, forzar
                    os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGKILL)
            except Exception as e:
                self.config_manager.write_to_log("InstallerThread", f"Error al intentar detener el proceso de instalación: {e}")

# --- Hilo de Backup ---
class BackupThread(QThread):
    progress_update = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str, str) # MODIFICACIÓN: Añadir config_name al finished signal

    def __init__(self, source_path: Path, destination_path: Path, config_manager: ConfigManager, is_full_backup: bool, config_name: str): # MODIFICACIÓN: Añadir config_name
        super().__init__()
        self.source_path = source_path
        self.destination_path = destination_path
        self.config_manager = config_manager
        self.is_full_backup = is_full_backup
        self.config_name = config_name # Guardar config_name
        self._is_running = True
        self._process: subprocess.Popen | None = None

    def run(self):
        self.config_manager.write_to_backup_log(f"Iniciando backup de '{self.source_path}' a '{self.destination_path}' para '{self.config_name}'") # MODIFICACIÓN: Log más detallado
        try:
            if not self.source_path.exists() or not self.source_path.is_dir():
                raise FileNotFoundError(f"La carpeta de origen del prefijo no existe: {self.source_path}")

            rsync_command = ["rsync", "-av", "--no-o", "--no-g"]

            final_backup_path_str = "" # Inicializar aquí
            if not self.is_full_backup: # Si es backup incremental (rsync)
                rsync_command.append("--checksum")
                self.config_manager.write_to_backup_log("Realizando backup incremental con rsync --checksum.")
                rsync_command.append(f"{self.source_path}/")
                rsync_command.append(str(self.destination_path))
                final_backup_path_str = str(self.destination_path) # El destino es el backup existente
            else:
                self.config_manager.write_to_backup_log("Realizando backup completo (nueva carpeta con timestamp).")
                temp_backup_dir = self.destination_path.parent / (self.destination_path.name + "_tmp")
                temp_backup_dir.mkdir(parents=True, exist_ok=True)

                rsync_command.append(f"{self.source_path}/")
                rsync_command.append(str(temp_backup_dir))
                final_backup_path_str = str(self.destination_path) # Este es el nombre final deseado

            self.progress_update.emit("Iniciando sincronización...")
            self.config_manager.write_to_backup_log(f"Comando rsync: {' '.join(rsync_command)}")

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
                self.finished.emit(False, "Backup cancelado por el usuario.", "", self.config_name) # MODIFICACIÓN: Añadir config_name
                self.config_manager.write_to_backup_log("Backup cancelado por el usuario.")
                if self.is_full_backup and temp_backup_dir.exists():
                    shutil.rmtree(temp_backup_dir, ignore_errors=True)
            elif self._process.returncode == 0:
                if self.is_full_backup:
                    shutil.move(str(temp_backup_dir), str(Path(final_backup_path_str))) # Asegurarse de que Path() se usa correctamente
                    self.config_manager.set_last_full_backup_path(self.config_name, final_backup_path_str) # MODIFICACIÓN: Guardar la ruta para esta config
                    success_msg = f"Backup COMPLETO de '{self.source_path.name}' completado exitosamente a '{final_backup_path_str}'."
                else:
                    success_msg = f"Backup INCREMENTAL de '{self.source_path.name}' completado exitosamente a '{self.destination_path}'."
                self.config_manager.write_to_backup_log(success_msg)
                self.finished.emit(True, success_msg, final_backup_path_str, self.config_name) # MODIFICACIÓN: Añadir config_name
            else:
                error_msg = f"Rsync falló con código {self._process.returncode}.\nStderr: {stderr}\nStdout: {stdout}"
                self.config_manager.write_to_backup_log(f"ERROR: {error_msg}")
                if self.is_full_backup and temp_backup_dir.exists():
                    shutil.rmtree(temp_backup_dir, ignore_errors=True)
                self.finished.emit(False, f"Error durante el backup: {stderr.strip() or stdout.strip()}", "", self.config_name) # MODIFICACIÓN: Añadir config_name

        except FileNotFoundError as e:
            msg = f"Error: Comando rsync no encontrado o ruta de origen/destino inválida. Asegúrate de que rsync esté instalado. {e}"
            self.config_manager.write_to_backup_log(f"ERROR: {msg}")
            self.finished.emit(False, msg, "", self.config_name) # MODIFICACIÓN: Añadir config_name
        except Exception as e:
            msg = f"Error inesperado durante el backup: {str(e)}"
            self.config_manager.write_to_backup_log(f"ERROR: {msg}")
            self.finished.emit(False, msg, "", self.config_name) # MODIFICACIÓN: Añadir config_name

    def stop(self):
        """Detiene el hilo y el subproceso de backup."""
        self._is_running = False
        if self._process and self._process.poll() is None:
            try:
                # Envía SIGINT para intentar una terminación limpia
                os.killpg(os.getpgid(self._process.pid), subprocess.signal.SIGINT)
            except ProcessLookupError:
                pass # El proceso ya no existe