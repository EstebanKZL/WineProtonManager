import os
import subprocess
import time
import tempfile
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

class InstallerThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    canceled = pyqtSignal(int)  # Nueva señal para cancelación

    def __init__(self, items, env, item_types=None, silent_mode=False, winetricks_path="winetricks", config_manager=None):
        super().__init__()
        self.items = items
        self.env = env
        self._is_running = True
        self.silent_mode = silent_mode
        self.item_types = item_types or []
        self.winetricks_path = winetricks_path
        self.config_manager = config_manager

    def run(self):
        try:
            subprocess.run(["which", "konsole"], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            self.error.emit(
                "Konsole no está instalado. Es necesario para mostrar la consola.\n"
                "Puede instalarlo con: sudo apt install konsole"
            )
            return

        for idx, (item_path, item_type) in enumerate(zip(self.items, self.item_types)):
            if not self._is_running:
                self.canceled.emit(idx)  # Emitir señal de cancelación
                break

            display_name = Path(item_path).name if item_type == "exe" else item_path
            self.progress.emit(idx, f"{display_name}: Instalando...")
            
            # Crear archivo de log temporal
            with tempfile.NamedTemporaryFile(delete=False) as temp_log:
                temp_log_path = temp_log.name
            
            try:
                if item_type == "exe":
                    exe_path = Path(item_path)
                    if not exe_path.exists():
                        raise FileNotFoundError(f"El archivo no existe:\n{exe_path}")
                    
                    wine_binary = self.env.get("WINE", "wine")
                    if "PROTON_DIR" in self.env:
                        proton_dir = Path(self.env["PROTON_DIR"])
                        wine_binary = str(proton_dir / "files/bin/wine")
                    
                    # Comando para ejecutable (.exe) - se cierra automáticamente
                    cmd = [
                        "konsole",
                        "--nofork",  # Esto permite que konsole se cierre automáticamente
                        "-e",
                        "bash", "-c",
                        f"{wine_binary} '{item_path}' 2>&1 | tee '{temp_log_path}'; exit"
                    ]
                    
                else:
                    # Comando para winetricks - se cierra automáticamente
                    silent_flag = "-q" if self.silent_mode else ""
                    cmd = [
                        "konsole",
                        "--nofork",  # Esto permite que konsole se cierra automáticamente
                        "-e",
                        "bash", "-c",
                        f"{self.winetricks_path} --force {silent_flag} '{item_path}' 2>&1 | tee '{temp_log_path}'; exit"
                    ]
                
                # Ejecutar el comando
                process = subprocess.Popen(
                    cmd,
                    env=self.env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Esperar a que termine el proceso
                process.wait()

                # Leer el log temporal
                with open(temp_log_path, 'r', encoding='utf-8', errors='replace') as log_file:
                    log_content = log_file.read()
                
                # Guardar en el log permanente
                if self.config_manager:
                    self.config_manager.write_to_log(display_name, f"=== INICIO DE INSTALACIÓN ===")
                    self.config_manager.write_to_log(display_name, f"Comando ejecutado: {' '.join(cmd)}")
                    self.config_manager.write_to_log(display_name, log_content)
                    self.config_manager.write_to_log(display_name, f"=== FIN DE INSTALACIÓN ===\n")

                if process.returncode != 0:
                    error_msg = f"Error durante la instalación. Código: {process.returncode}"
                    if self.config_manager:
                        self.config_manager.write_to_log(display_name, f"ERROR: {error_msg}")
                    raise subprocess.CalledProcessError(
                        process.returncode, cmd, error_msg
                    )

                # Registrar la instalación en wineprotonmanager.log (solo el nombre)
                prefix_path = Path(self.env["WINEPREFIX"])
                log_file = prefix_path / "wineprotonmanager.log"
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} installed {display_name}\n")

                self.progress.emit(idx, f"{display_name}: Finalizado")
                
            except Exception as e:
                if self.config_manager:
                    self.config_manager.write_to_log(display_name, f"ERROR DURANTE INSTALACIÓN: {str(e)}")
                self.error.emit(f"Error instalando {display_name}:\n{str(e)}")
                break
            finally:
                # Eliminar archivo temporal
                try:
                    os.unlink(temp_log_path)
                except:
                    pass

        self.finished.emit()

    def stop(self):
        self._is_running = False