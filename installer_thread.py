import os
import subprocess
import tempfile
import time
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal

class InstallerThread(QThread):
    progress = pyqtSignal(str, str) # (item_name: str, status: str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    canceled = pyqtSignal(str) # Nombre del item que fue cancelado
    
    def __init__(self, items_to_install: list[tuple[str, str, str]], env: dict, silent_mode: bool, force_mode: bool, winetricks_path: str, config_manager):
        # IMPORTANT: items_to_install needs to be modified to include the 'name'
        # It should now be a list of tuples: (path_to_exe_or_winetricks_name, type_str, user_defined_name)
        super().__init__()
        self.items_to_install = items_to_install
        self.env = env
        self.silent_mode = silent_mode
        self.force_mode = force_mode 
        self.winetricks_path = winetricks_path
        self.config_manager = config_manager
        self._is_running = True
        self.current_process = None

    def run(self):
        try:
            self._check_konsole_availability()
        except EnvironmentError as e:
            self.error.emit(str(e))
            return

        # Iterate through the new tuple format: (path_or_name, type, user_name)
        for idx, (item_path_or_name, item_type, user_defined_name) in enumerate(self.items_to_install):
            if not self._is_running:
                # Use user_defined_name for canceled signal as well
                self.canceled.emit(user_defined_name)
                break
            
            # Use the user_defined_name consistently for all progress updates and logging
            display_name_for_progress = user_defined_name

            self.progress.emit(display_name_for_progress, f"{display_name_for_progress}: Instalando...")
            self.config_manager.write_to_log(display_name_for_progress, f"Iniciando instalacion: {item_path_or_name} (Tipo: {item_type}, Silencioso: {self.silent_mode}, Forzado: {self.force_mode})")
            
            temp_log_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as temp_log_file:
                    temp_log_path = Path(temp_log_file.name)
                
                if item_type == "exe":
                    self._install_exe(item_path_or_name, temp_log_path, display_name_for_progress)
                elif item_type == "winetricks":
                    self._install_winetricks(item_path_or_name, temp_log_path, display_name_for_progress)
                elif item_type == "wtr": 
                    self._install_winetricks_script(item_path_or_name, temp_log_path, display_name_for_progress)
                else:
                    raise ValueError(f"Tipo de instalacion no reconocido: {item_type}")
                
                self._register_successful_installation(display_name_for_progress)
                self.progress.emit(display_name_for_progress, f"{display_name_for_progress}: Finalizado")
                self.config_manager.write_to_log(display_name_for_progress, f"Instalacion de {display_name_for_progress} completada exitosamente.")
                
            except Exception as e:
                self._handle_installation_error(e, display_name_for_progress, temp_log_path)
                break 
            finally:
                if temp_log_path and temp_log_path.exists():
                    try:
                        temp_log_path.unlink()
                        retcode_file = Path(str(temp_log_path) + ".retcode")
                        if retcode_file.exists():
                            retcode_file.unlink()
                    except OSError as e:
                        self.config_manager.write_to_log(display_name_for_progress, f"Advertencia: No se pudo eliminar el archivo temporal {temp_log_path}: {e}")

        self.finished.emit()

    def _check_konsole_availability(self):
        """Comprueba si Konsole esta disponible."""
        try:
            subprocess.run(["which", "konsole"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            raise EnvironmentError(
                "Konsole no esta instalado o no se encuentra en PATH. "
                "Es necesario para mostrar la consola de instalacion. "
                "Puedes instalarlo con: sudo apt install konsole"
            )

    def _install_exe(self, exe_path: str, temp_log_path: Path, display_name: str):
        """Ejecuta un archivo .exe usando Wine/Proton en una nueva ventana de Konsole."""
        exe_path = Path(exe_path)
        if not exe_path.exists():
            raise FileNotFoundError(f"El archivo EXE no existe: {exe_path}")
            
        wine_executable = self.env.get("WINE")
        if not wine_executable or not Path(wine_executable).is_file():
            raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")

        cmd = [
            "nohup", "konsole",
            "--nofork",
            "-e",
            "bash", "-c",
            f"'{wine_executable}' '{exe_path}' 2>&1 | tee '{temp_log_path}'; echo $? > '{temp_log_path}.retcode'; exit"
        ]
        
        self.config_manager.write_to_log(display_name, f"Comando EXE: {' '.join(cmd)}")
        self._execute_command_in_konsole(cmd, display_name, temp_log_path)

    def _install_winetricks(self, component_name: str, temp_log_path: Path, display_name: str):
        """Ejecuta un comando de winetricks en una nueva ventana de Konsole."""
        winetricks_executable = self.winetricks_path
        if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
            raise FileNotFoundError(f"Ejecutable de Winetricks no encontrado: {winetricks_executable}")

        silent_flag = "-q" if self.silent_mode else ""
        force_flag = "--force" if self.force_mode else "" 

        cmd = [
            "nohup", "konsole",
            "--nofork",
            "-e",
            "bash", "-c",
            f"'{winetricks_executable}' {silent_flag} {force_flag} '{component_name}' 2>&1 | tee '{temp_log_path}'; echo $? > '{temp_log_path}.retcode'; exit"
        ]
        cmd = [c for c in cmd if c]
        
        self.config_manager.write_to_log(display_name, f"Comando Winetricks: {' '.join(cmd)}")
        self._execute_command_in_konsole(cmd, display_name, temp_log_path)

    def _install_winetricks_script(self, script_path: str, temp_log_path: Path, display_name: str):
        """Ejecuta un script personalizado de Winetricks (.wtr) en una nueva ventana de Konsole."""
        script_path = Path(script_path)
        if not script_path.exists():
            raise FileNotFoundError(f"El archivo de script de Winetricks no existe: {script_path}")

        winetricks_executable = self.winetricks_path
        if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
            raise FileNotFoundError(f"Ejecutable de Winetricks no encontrado: {winetricks_executable}")
            
        silent_flag = "-q" if self.silent_mode else "" 
        force_flag = "--force" if self.force_mode else "" 

        cmd = [
            "nohup", "konsole",
            "--nofork",
            "-e",
            "bash", "-c",
            f"'{winetricks_executable}' {silent_flag} {force_flag} '{script_path}' 2>&1 | tee '{temp_log_path}'; echo $? > '{temp_log_path}.retcode'; exit"
        ]
        cmd = [c for c in cmd if c]
        
        self.config_manager.write_to_log(display_name, f"Comando de script Winetricks: {' '.join(cmd)}")
        self._execute_command_in_konsole(cmd, display_name, temp_log_path)

    def _execute_command_in_konsole(self, cmd: list[str], display_name: str, temp_log_path: Path):
        """Ejecuta un comando y espera su finalizacion, procesando el codigo de retorno."""
        self.current_process = subprocess.Popen(
            cmd,
            env=self.env,
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setpgrp 
        )
        self.current_process.wait()

        return_code_file = Path(str(temp_log_path) + ".retcode")
        retcode = -1 
        if return_code_file.exists():
            try:
                with open(return_code_file, 'r') as f:
                    retcode = int(f.read().strip())
            except Exception as e:
                self.config_manager.write_to_log(display_name, f"Advertencia: No se pudo leer el codigo de retorno del subshell: {e}")

        log_content = ""
        if temp_log_path.exists():
            try:
                with open(temp_log_path, 'r', encoding='utf-8', errors='replace') as f:
                    log_content = f.read()
            except Exception as e:
                self.config_manager.write_to_log(display_name, f"Advertencia: No se pudo leer el log temporal {temp_log_path}: {e}")
        
        self.config_manager.write_to_log(display_name, "=== INICIO DEL LOG DEL PROCESO ===")
        self.config_manager.write_to_log(display_name, log_content)
        self.config_manager.write_to_log(display_name, f"Codigo de retorno del proceso: {retcode}")
        self.config_manager.write_to_log(display_name, "=== FIN DEL LOG DEL PROCESO ===\n")

        if retcode != 0:
            raise subprocess.CalledProcessError(retcode, cmd, output=log_content)

    def _register_successful_installation(self, display_name: str):
        """Registra una instalacion exitosa en el log del prefijo."""
        prefix_path = Path(self.env["WINEPREFIX"])
        log_file = prefix_path / "wineprotonmanager.log"
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} installed {display_name}\n")
        except IOError as e:
            self.config_manager.write_to_log(display_name, f"Advertencia: No se pudo escribir en el log del prefijo {log_file}: {e}")

    def _handle_installation_error(self, error: Exception, display_name: str, temp_log_path: Path | None):
        """Maneja y notifica errores durante la instalacion."""
        error_msg = f"Error instalando {display_name}:\n"
        if isinstance(error, subprocess.CalledProcessError):
            error_msg += f"Comando fallido: {' '.join(error.cmd)}\nCodigo de Salida: {error.returncode}\nSalida/Error: {error.output or error.stderr}"
        else:
            error_msg += str(error)
            
        self.config_manager.write_to_log(display_name, f"ERROR DURANTE LA INSTALACION: {error_msg}")
        self.progress.emit(display_name, f"{display_name}: Error") # Actualizar estado en GUI
        self.error.emit(f"Error fatal durante la instalacion de {display_name}. "
                        f"Consulta el registro para mas detalles: {self.config_manager.get_log_path(display_name)}\n"
                        f"Mensaje de error: {str(error)}")
            
    def stop(self):
        """Detiene la instalacion, incluyendo el proceso de Konsole."""
        self._is_running = False
        if self.current_process and self.current_process.poll() is None:
            try:
                os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGINT)
                self.current_process.wait(timeout=2)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGTERM)
                    self.current_process.wait(timeout=2)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    try:
                        os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGKILL)
                    except ProcessLookupError:
                        pass
