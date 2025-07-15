import os
import subprocess
import tempfile
import time
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

from config_manager import ConfigManager

class InstallerThread(QThread):
    progress = pyqtSignal(str, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    item_error = pyqtSignal(str, str)
    canceled = pyqtSignal(str)
    console_output = pyqtSignal(str)

    def __init__(self, items_to_install: list[tuple[str, str, str]], env: dict, silent_mode: bool, force_mode: bool, winetricks_path: str, config_manager: ConfigManager, config_name: str):
        super().__init__()
        self.items_to_install = items_to_install
        self.env = env
        self.silent_mode = silent_mode
        self.force_mode = force_mode
        self.winetricks_path = winetricks_path
        self.config_manager = config_manager
        self.config_name = config_name
        self._is_running = True
        self.current_process: subprocess.Popen | None = None

    def run(self):
        try:
            wine_executable = self.env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                self.error.emit(f"Ejecutable de Wine/Proton no encontrado o no ejecutable: {wine_executable}")
                return
            if any(item[1] in ["winetricks", "wtr"] for item in self.items_to_install):
                winetricks_executable = self.winetricks_path
                if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
                    self.error.emit(f"Ejecutable de Winetricks no encontrado o no ejecutable: {winetricks_executable}")
                    return
        except EnvironmentError as e:
            self.error.emit(str(e))
            return

        for idx, (item_path_or_name, item_type, user_defined_name) in enumerate(self.items_to_install):
            if not self._is_running:
                self.canceled.emit(user_defined_name)
                break

            display_name_for_progress = user_defined_name
            log_source = f"Install-{display_name_for_progress}"

            self.progress.emit(display_name_for_progress, "Instalando")
            self.config_manager.write_to_log(self.config_name, log_source, f"Iniciando instalación: {item_path_or_name} (Tipo: {item_type}, Silencioso: {self.silent_mode}, Forzado: {self.force_mode})")

            temp_log_path = None
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

                self._register_successful_installation(display_name_for_progress, item_type, item_path_or_name)
                self.progress.emit(display_name_for_progress, "Finalizado")
                self.config_manager.write_to_log(self.config_name, log_source, f"Instalación de {display_name_for_progress} completada exitosamente.")

            except Exception as e:
                error_msg = f"Comando fallido para {display_name_for_progress}. Detalles:\n"
                if isinstance(e, subprocess.CalledProcessError):
                    error_msg += f"Comando: {' '.join(e.cmd)}\nCódigo de Salida: {e.returncode}\nSalida/Error: {e.output or e.stderr}"
                else:
                    error_msg += str(e)

                self.config_manager.write_to_log(self.config_name, log_source, f"ERROR: DURANTE LA INSTALACIÓN: {error_msg}")
                self.progress.emit(display_name_for_progress, "Error")
                self.item_error.emit(display_name_for_progress, error_msg)
            finally:
                if temp_log_path and temp_log_path.exists():
                    try:
                        temp_log_path.unlink()
                        retcode_file = Path(str(temp_log_path) + ".retcode")
                        if retcode_file.exists():
                            retcode_file.unlink()
                    except OSError as e:
                        self.config_manager.write_to_log(self.config_name, log_source, f"Advertencia: No se pudo eliminar el archivo temporal {temp_log_path}: {e}")

        if self._is_running:
            self.finished.emit()

    def _install_exe(self, exe_path: str, temp_log_path: Path, display_name: str):
        exe_path = Path(exe_path)
        if not exe_path.exists():
            raise FileNotFoundError(f"El archivo EXE no existe: {exe_path}")
        wine_executable = self.env.get("WINE")
        if not wine_executable or not Path(wine_executable).is_file():
            raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")
        cmd = [wine_executable, str(exe_path)]
        self.config_manager.write_to_log(self.config_name, f"Install-{display_name}", f"Comando EXE: {' '.join(cmd)}")
        self._execute_command_and_capture_output(cmd, display_name, temp_log_path)

    def _install_winetricks(self, component_name: str, temp_log_path: Path, display_name: str):
        winetricks_executable = self.winetricks_path
        if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
            raise FileNotFoundError(f"Ejecutable de Winetricks no encontrado: {winetricks_executable}")
        silent_flag = "-q" if self.silent_mode else ""
        force_flag = "--force" if self.force_mode else ""
        cmd = [c for c in [winetricks_executable, silent_flag, force_flag, component_name] if c]
        self.config_manager.write_to_log(self.config_name, f"Install-{display_name}", f"Comando Winetricks: {' '.join(cmd)}")
        self._execute_command_and_capture_output(cmd, display_name, temp_log_path)

    def _install_winetricks_script(self, script_path: str, temp_log_path: Path, display_name: str):
        script_path = Path(script_path)
        if not script_path.exists():
            raise FileNotFoundError(f"El archivo de script de Winetricks no existe: {script_path}")
        winetricks_executable = self.winetricks_path
        if not Path(winetricks_executable).is_file() and winetricks_executable != "winetricks":
            raise FileNotFoundError(f"Ejecutable de Winetricks no encontrado: {winetricks_executable}")
        silent_flag = "-q" if self.silent_mode else ""
        force_flag = "--force" if self.force_mode else ""
        cmd = [c for c in [winetricks_executable, silent_flag, force_flag, str(script_path)] if c]
        self.config_manager.write_to_log(self.config_name, f"Install-{display_name}", f"Comando de script Winetricks: {' '.join(cmd)}")
        self._execute_command_and_capture_output(cmd, display_name, temp_log_path)

    def _execute_command_and_capture_output(self, cmd: list[str], display_name: str, temp_log_path: Path):
        log_source = f"Process-{display_name}"
        try:
            self.current_process = subprocess.Popen(
                cmd, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True, preexec_fn=os.setsid
            )
            log_content = ""
            while True:
                line = self.current_process.stdout.readline()
                if not line: break
                log_content += line
                self.console_output.emit(line.strip())
                QApplication.processEvents()
            self.current_process.wait(timeout=300)
            retcode = self.current_process.returncode

            with open(temp_log_path, 'w', encoding='utf-8') as f: f.write(log_content)

            self.config_manager.write_to_log(self.config_name, log_source, "=== INICIO DEL LOG DEL PROCESO ===")
            self.config_manager.write_to_log(self.config_name, log_source, log_content)
            self.config_manager.write_to_log(self.config_name, log_source, f"Código de retorno del proceso: {retcode}")
            self.config_manager.write_to_log(self.config_name, log_source, "=== FIN DEL LOG DEL PROCESO ===\n")

            if retcode != 0:
                raise subprocess.CalledProcessError(retcode, cmd, output=log_content)
        except subprocess.TimeoutExpired:
            self.current_process.kill()
            raise Exception("El comando de instalación agotó el tiempo de espera.")
        except Exception as e:
            raise Exception(f"Error inesperado al ejecutar comando: {str(e)}")
            
    def _register_successful_installation(self, display_name: str, item_type: str, original_path_or_name: str):
        prefix_path = Path(self.env["WINEPREFIX"])
        log_file = prefix_path / "wineprotonmanager.ini"
        try:
            entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} installed {display_name} (Type: {item_type}, Source: {original_path_or_name})"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{entry}\n")
        except IOError as e:
            self.config_manager.write_to_log(self.config_name, f"Install-{display_name}", f"Advertencia: No se pudo escribir en el log del prefijo {log_file}: {e}")

    def stop(self):
        self._is_running = False
        if self.current_process and self.current_process.poll() is None:
            try:
                os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGTERM)
                self.current_process.wait(5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if self.current_process.poll() is None:
                    os.killpg(os.getpgid(self.current_process.pid), subprocess.signal.SIGKILL)
            except Exception as e:
                self.config_manager.write_to_log(self.config_name, "InstallerThread", f"Error al intentar detener el proceso de instalación: {e}")
