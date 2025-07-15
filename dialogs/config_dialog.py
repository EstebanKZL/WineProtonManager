import subprocess

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, QListWidget,
                             QHBoxLayout, QPushButton, QLabel, QFormLayout, QComboBox,
                             QLineEdit, QGroupBox, QRadioButton, QDialogButtonBox,
                             QMessageBox, QProgressDialog, QFileDialog, QProgressBar,
                             QListWidgetItem, QCheckBox, QApplication)
from PyQt5.QtCore import pyqtSignal, Qt, QDir
from PyQt5.QtGui import QFont

from pathlib import Path
from functools import partial
from threads.download_thread import DownloadThread
from threads.decompression_thread import DecompressionThread
from threads.version_search_thread import VersionSearchThread
from dialogs.repository_dialog import RepositoryDialog
from styles import STYLE_BREEZE, COLOR_BREEZE_ACCENT, COLOR_BREEZE_PRIMARY
from config_manager import ConfigManager

class ConfigDialog(QDialog):
    config_saved = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Configuración de Entorno")
        self.setMinimumSize(825, 625)
        self.current_config_name_for_editing = None
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)
        self.load_configs()
        self.update_save_settings_button_state()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.current_tab = QWidget()
        self.setup_current_config_tab()
        self.tabs.addTab(self.current_tab, "Configuraciones Guardadas")

        self.new_tab = QWidget()
        self.setup_new_config_tab()
        self.tabs.addTab(self.new_tab, "Crear/Editar Configuración")

        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Ajustes Generales")

        self.downloads_tab = QWidget()

        self.proton_tab = QWidget() 
        self.wine_tab = QWidget()  
        self.setup_downloads_tab()
        self.tabs.addTab(self.downloads_tab, "Descargas de Versiones")

        layout.addWidget(self.tabs)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.button(QDialogButtonBox.Close).setAutoDefault(False)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def setup_current_config_tab(self):
        layout = QVBoxLayout()
        self.list_config = QListWidget()
        self.list_config.itemDoubleClicked.connect(self.edit_config)
        self.list_config.itemSelectionChanged.connect(self.update_displayed_config_info)
        layout.addWidget(self.list_config)

        btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("Eliminar Configuración")
        self.btn_delete.setAutoDefault(False)
        self.btn_delete.clicked.connect(self.delete_config)
        btn_layout.addWidget(self.btn_delete)

        self.btn_set_default = QPushButton("Establecer por Defecto")
        self.btn_set_default.setAutoDefault(False)
        self.btn_set_default.clicked.connect(self.set_default_config)
        btn_layout.addWidget(self.btn_set_default)

        layout.addLayout(btn_layout)

        self.lbl_config_info = QLabel("Selecciona una configuración para ver los detalles")
        self.lbl_config_info.setWordWrap(True)
        layout.addWidget(self.lbl_config_info)
        self.current_tab.setLayout(layout)

    def setup_new_config_tab(self):
        layout = QFormLayout()

        self.config_type = QComboBox()
        self.config_type.addItems(["Wine", "Proton"])
        self.config_type.currentTextChanged.connect(self.update_config_field_visibility)
        layout.addRow("Tipo:", self.config_type)

        self.config_name = QLineEdit()
        layout.addRow("Nombre:", self.config_name)

        self.architecture_combo = QComboBox()
        self.architecture_combo.addItems(["win64", "win32"])
        layout.addRow("Arquitectura:", self.architecture_combo)

        self.prefix_path = QLineEdit()
        self.btn_prefix = QPushButton("Explorar...")
        self.btn_prefix.setAutoDefault(False)
        self.btn_prefix.clicked.connect(self.browse_prefix)
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(self.prefix_path)
        prefix_layout.addWidget(self.btn_prefix)
        layout.addRow("Ruta del Prefijo (WINEPREFIX):", prefix_layout)

        self.proton_prefix_type_group = QGroupBox("Tipo de Prefijo de Proton")
        proton_prefix_layout = QVBoxLayout()
        self.radio_proton_custom_prefix = QRadioButton("Prefijo personalizado")
        self.radio_proton_custom_prefix.setChecked(True) 
        self.radio_proton_custom_prefix.toggled.connect(self.update_proton_prefix_options)

        self.radio_proton_steam_prefix = QRadioButton("Usar prefijo de Steam (por APPID)")
        self.radio_proton_steam_prefix.toggled.connect(self.update_proton_prefix_options)

        proton_prefix_layout.addWidget(self.radio_proton_custom_prefix)
        proton_prefix_layout.addWidget(self.radio_proton_steam_prefix)

        self.appid_line_edit = QLineEdit()
        self.appid_line_edit.setPlaceholderText("Ingresa el APPID de Steam (ej. 123456)")
        proton_prefix_layout.addWidget(self.appid_line_edit)
        self.appid_line_edit.hide() 

        self.proton_prefix_type_group.setLayout(proton_prefix_layout)
        layout.addRow(self.proton_prefix_type_group)
        # Grupo para configuración de Wine (directorio de instalación)
        self.wine_directory = QLineEdit()
        self.btn_wine = QPushButton("Explorar...")
        self.btn_wine.setAutoDefault(False)
        self.btn_wine.clicked.connect(self.browse_wine)
        wine_layout = QHBoxLayout()
        wine_layout.addWidget(self.wine_directory)
        wine_layout.addWidget(self.btn_wine)

        self.wine_group = QGroupBox("Configuración de Wine Personalizada")
        wine_inner_layout = QFormLayout()
        wine_inner_layout.addRow("Directorio de instalación de Wine:", wine_layout)
        self.wine_group.setLayout(wine_inner_layout)
        # Grupo para configuración de Proton (directorio de instalación)
        self.proton_directory = QLineEdit()
        self.btn_proton = QPushButton("Explorar...")
        self.btn_proton.setAutoDefault(False)
        self.btn_proton.clicked.connect(self.browse_proton)
        proton_layout = QHBoxLayout()
        proton_layout.addWidget(self.proton_directory)
        proton_layout.addWidget(self.btn_proton)

        self.proton_group = QGroupBox("Configuración de Proton Personalizada")
        proton_inner_layout = QFormLayout()
        proton_inner_layout.addRow("Directorio de instalación de Proton:", proton_layout)
        self.proton_group.setLayout(proton_inner_layout)

        layout.addRow(self.wine_group)
        layout.addRow(self.proton_group)

        self.btn_create_prefix = QPushButton("Crear/Inicializar Prefijo")
        self.btn_create_prefix.setAutoDefault(False)
        self.btn_create_prefix.clicked.connect(self.create_and_initialize_prefix)
        layout.addRow(self.btn_create_prefix)

        buttons_layout = QHBoxLayout()
        self.btn_test = QPushButton("Probar Configuración")
        self.btn_test.setAutoDefault(False)
        self.btn_test.clicked.connect(self.test_configuration)
        buttons_layout.addWidget(self.btn_test)

        self.btn_save_config = QPushButton("Guardar Configuración")
        self.btn_save_config.setAutoDefault(False)
        self.btn_save_config.clicked.connect(self.save_new_config)
        buttons_layout.addWidget(self.btn_save_config)
        layout.addRow(buttons_layout)

        self.update_config_field_visibility() 
        self.new_tab.setLayout(layout)

    def create_and_initialize_prefix(self):
        """Crea el directorio del prefijo si no existe y ejecuta wineboot de forma segura."""
        config_name = self.config_name.text().strip()
        if not config_name:
            QMessageBox.warning(self, "Error", "Debes especificar un nombre para la configuración.")
            return

        # 1. Recopilar datos de la UI en un diccionario temporal
        temp_config_data = {
            "type": "wine" if self.config_type.currentText() == "Wine" else "proton",
            "arch": self.architecture_combo.currentText()
        }

        try:
            if temp_config_data["type"] == "proton":
                proton_dir = self.proton_directory.text().strip()
                if not proton_dir or not Path(proton_dir).is_dir():
                    raise ValueError("Debes especificar un directorio de Proton válido.")
                temp_config_data["proton_dir"] = proton_dir

                if self.radio_proton_steam_prefix.isChecked():
                    appid = self.appid_line_edit.text().strip()
                    if not appid or not appid.isdigit():
                        raise ValueError("Para un prefijo de Steam, debes ingresar un APPID numérico válido.")
                    steam_compat_data_root = Path.home() / ".local/share/Steam/steamapps/compatdata"
                    temp_config_data["prefix"] = str(steam_compat_data_root / appid / "pfx")
                    temp_config_data["steam_appid"] = appid
                else:
                    prefix = self.prefix_path.text().strip()
                    if not prefix: raise ValueError("Debes especificar una ruta de prefijo para Proton.")
                    temp_config_data["prefix"] = prefix
            else: # Wine
                prefix = self.prefix_path.text().strip()
                if not prefix: raise ValueError("Debes especificar una ruta de prefijo para Wine.")
                temp_config_data["prefix"] = prefix

                wine_dir = self.wine_directory.text().strip()
                if wine_dir and not Path(wine_dir).is_dir():
                    raise ValueError("El directorio de instalación de Wine no es válido.")
                elif wine_dir:
                    temp_config_data["wine_dir"] = wine_dir
        except ValueError as e:
            QMessageBox.warning(self, "Entrada Inválida", str(e))
            return

        prefix_path = Path(temp_config_data["prefix"])
        if prefix_path.exists():
            reply = QMessageBox.question(self, "Prefijo Existente",
                                         f"El prefijo '{prefix_path}' ya existe. ¿Deseas reinicializarlo?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No: return

        # 2. Proceder con la inicialización
        progress_dialog = QProgressDialog("Inicializando Prefijo...", "", 0, 0, self)
        progress_dialog.setWindowTitle("Inicialización del Prefijo")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None)
        self.config_manager.apply_breeze_style_to_widget(progress_dialog)
        progress_dialog.show()

        process = None
        try:
            prefix_path.mkdir(parents=True, exist_ok=True, mode=0o755)

            # 3. Crear una copia temporal de las configuraciones para obtener el entorno de forma segura
            temp_full_configs = {
                "configs": {config_name: temp_config_data},
                "last_used": config_name
            }
            original_configs = self.config_manager.configs
            self.config_manager.configs = temp_full_configs
            env = self.config_manager.get_current_environment(config_name)
            self.config_manager.configs = original_configs # Restaurar inmediatamente

            wine_executable = env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado: {wine_executable}")

            process = subprocess.Popen([wine_executable, "wineboot"], env=env,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, bufsize=1, universal_newlines=True)
            log_output = ""
            while True:
                line = process.stdout.readline()
                if not line: break
                log_output += line
                progress_dialog.setLabelText(f"Inicializando...\n{line.strip()}")
                QApplication.processEvents()

            process.wait(timeout=120)
            self.config_manager.write_to_log("Creación del Prefijo", f"Wineboot ({config_name})", f"Salida:\n{log_output}")

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "wineboot", output=log_output)

            QMessageBox.information(self, "Éxito", "El prefijo ha sido inicializado exitosamente.\nRecuerda guardar la configuración si deseas conservarla.")

        except Exception as e:
            if process: process.kill()
            error_msg = f"No se pudo inicializar el prefijo: {e}"
            if isinstance(e, subprocess.CalledProcessError):
                error_msg = f"Falló la inicialización del prefijo. Código: {e.returncode}\nSalida: {e.output}"
            QMessageBox.critical(self, "Error al Crear/Inicializar Prefijo", error_msg)
        finally:
            progress_dialog.close()

    def _create_prefix(self, config: dict, config_name: str, prefix_path: Path):
        """Crea un nuevo prefijo de Wine/Proton y lo inicializa con wineboot."""
        prefix_path.mkdir(parents=True, exist_ok=True, mode=0o755)

        original_configs = self.config_manager.configs.copy()
        temp_configs_dict = {k: v.copy() if isinstance(v, dict) else v for k, v in original_configs.get("configs", {}).items()}
        temp_configs_dict[config_name] = config
        self.config_manager.configs["configs"] = temp_configs_dict
        self.config_manager.configs["last_used"] = config_name

        env = self.config_manager.get_current_environment(config_name)

        wine_executable = env.get("WINE")
        if not wine_executable or not Path(wine_executable).is_file():
            self.config_manager.configs = original_configs
            self.config_manager.save_configs()
            raise FileNotFoundError(f"Ejecutable de Wine no encontrado: {wine_executable}")

        progress_dialog = QProgressDialog("Inicializando Prefijo de Wine/Proton...", "", 0, 0, self)
        progress_dialog.setWindowTitle("Inicialización del Prefijo")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.setFixedSize(450, 150)
        self.config_manager.apply_breeze_style_to_widget(progress_dialog)
        progress_dialog.show()

        try:
            process = subprocess.Popen(
                [wine_executable, "wineboot"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            log_output = ""
            for line in process.stdout:
                log_output += line
                progress_dialog.setLabelText(f"Inicializando Prefijo de Wine/Proton...\n{line.strip()}")
                QApplication.processEvents()
            process.wait(timeout=60)

            self.config_manager.write_to_log("Creación del Prefijo", f"Wineboot ({config_name})", f"Salida:\n{log_output}")

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "wineboot", output=log_output)

        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception("La inicialización del prefijo de Wine/Proton agotó el tiempo de espera.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"No se pudo inicializar el prefijo de Wine/Proton. Código de salida: {e.returncode}\nSalida: {e.output}")
        finally:
            progress_dialog.close()
            self.config_manager.configs = original_configs
            self.config_manager.save_configs()

    def update_proton_prefix_options(self):
        """Controla la visibilidad de los campos de prefijo según el tipo de Proton."""
        if self.radio_proton_steam_prefix.isChecked():
            self.appid_line_edit.show()
            self.prefix_path.setEnabled(False)
            self.btn_prefix.setEnabled(False)
            self.prefix_path.setPlaceholderText("Se generará automáticamente con el APPID")
        else:
            self.appid_line_edit.hide()
            self.prefix_path.setEnabled(True)
            self.btn_prefix.setEnabled(True)
            self.prefix_path.setPlaceholderText("")

    def update_config_field_visibility(self):
        """Actualiza la visibilidad de los campos de configuración Wine/Proton."""
        is_proton = self.config_type.currentText() == "Proton"
        self.proton_group.setVisible(is_proton)
        self.wine_group.setVisible(not is_proton)
        self.proton_prefix_type_group.setVisible(is_proton)

        if is_proton and self.radio_proton_steam_prefix.isChecked():
            self.prefix_path.setEnabled(False)
            self.btn_prefix.setEnabled(False)
        else:
            self.prefix_path.setEnabled(True)
            self.btn_prefix.setEnabled(True)

    def setup_downloads_tab(self):
        
        downloads_tab_layout = QVBoxLayout(self.downloads_tab) 

        self.download_tabs = QTabWidget() 
       
       # Configuración de la pestaña Proton
        proton_inner_layout = QVBoxLayout(self.proton_tab)
        self.group_proton_repos = QGroupBox("Repositorios de Proton")
        repo_layout = QVBoxLayout()
        self.list_repos_proton = QListWidget()
        self.list_repos_proton.setSelectionMode(QListWidget.SingleSelection)
        self.load_proton_repositories()
        repo_layout.addWidget(self.list_repos_proton)
        repo_btn_layout = QHBoxLayout()
        self.btn_add_proton_repo = QPushButton("Añadir")
        self.btn_add_proton_repo.setAutoDefault(False)
        self.btn_add_proton_repo.clicked.connect(self.add_proton_repository)
        repo_btn_layout.addWidget(self.btn_add_proton_repo)
        self.btn_delete_proton_repo = QPushButton("Eliminar")
        self.btn_delete_proton_repo.setAutoDefault(False)
        self.btn_delete_proton_repo.clicked.connect(self.delete_proton_repository)
        repo_btn_layout.addWidget(self.btn_delete_proton_repo)
        self.btn_toggle_proton_repo = QPushButton("Habilitar/Deshabilitar")
        self.btn_toggle_proton_repo.setAutoDefault(False)
        self.btn_toggle_proton_repo.clicked.connect(self.toggle_proton_repository)
        repo_btn_layout.addWidget(self.btn_toggle_proton_repo)
        repo_layout.addLayout(repo_btn_layout)
        self.group_proton_repos.setLayout(repo_layout)
        proton_inner_layout.addWidget(self.group_proton_repos)

        self.group_proton_versions = QGroupBox("Versiones de Proton Disponibles")
        versions_layout = QVBoxLayout()
        self.list_versions_proton = QListWidget()
        versions_layout.addWidget(self.list_versions_proton)
        buttons_layout = QHBoxLayout()
        self.btn_update_proton = QPushButton("Actualizar Lista")
        self.btn_update_proton.setAutoDefault(False)
        self.btn_update_proton.clicked.connect(self.update_proton_versions)
        buttons_layout.addWidget(self.btn_update_proton)
        self.btn_download_proton = QPushButton("Descargar Seleccionado")
        self.btn_download_proton.setAutoDefault(False)
        self.btn_download_proton.clicked.connect(self.download_selected_proton_version)
        buttons_layout.addWidget(self.btn_download_proton)
        versions_layout.addLayout(buttons_layout)
        self.group_proton_versions.setLayout(versions_layout)
        proton_inner_layout.addWidget(self.group_proton_versions) 
       
       # Configuración de la pestaña Wine
        wine_inner_layout = QVBoxLayout(self.wine_tab) 
        self.group_wine_repos = QGroupBox("Repositorios de Wine")
        wine_repo_layout = QVBoxLayout()
        self.list_repos_wine = QListWidget()
        self.list_repos_wine.setSelectionMode(QListWidget.SingleSelection)
        self.load_wine_repositories()
        wine_repo_layout.addWidget(self.list_repos_wine)
        wine_repo_btn_layout = QHBoxLayout()
        self.btn_add_wine_repo = QPushButton("Añadir")
        self.btn_add_wine_repo.setAutoDefault(False)
        self.btn_add_wine_repo.clicked.connect(self.add_wine_repository)
        wine_repo_btn_layout.addWidget(self.btn_add_wine_repo)
        self.btn_delete_wine_repo = QPushButton("Eliminar")
        self.btn_delete_wine_repo.setAutoDefault(False)
        self.btn_delete_wine_repo.clicked.connect(self.delete_wine_repository)
        wine_repo_btn_layout.addWidget(self.btn_delete_wine_repo)
        self.btn_toggle_wine_repo = QPushButton("Habilitar/Deshabilitar")
        self.btn_toggle_wine_repo.setAutoDefault(False)
        self.btn_toggle_wine_repo.clicked.connect(self.toggle_wine_repository)
        wine_repo_btn_layout.addWidget(self.btn_toggle_wine_repo)
        wine_repo_layout.addLayout(wine_repo_btn_layout)
        self.group_wine_repos.setLayout(wine_repo_layout)
        wine_inner_layout.addWidget(self.group_wine_repos)

        self.group_wine_versions = QGroupBox("Versiones de Wine Disponibles")
        wine_versions_layout = QVBoxLayout()
        self.list_versions_wine = QListWidget()
        wine_versions_layout.addWidget(self.list_versions_wine)
        wine_buttons_layout = QHBoxLayout()
        self.btn_update_wine = QPushButton("Actualizar Lista")
        self.btn_update_wine.setAutoDefault(False)
        self.btn_update_wine.clicked.connect(self.update_wine_versions)
        wine_buttons_layout.addWidget(self.btn_update_wine)
        self.btn_download_wine = QPushButton("Descargar Seleccionado")
        self.btn_download_wine.setAutoDefault(False)
        self.btn_download_wine.clicked.connect(self.download_selected_wine_version)
        wine_buttons_layout.addWidget(self.btn_download_wine)
        wine_versions_layout.addLayout(wine_buttons_layout)
        self.group_wine_versions.setLayout(wine_versions_layout)
        wine_inner_layout.addWidget(self.group_wine_versions)

        self.download_tabs.addTab(self.proton_tab, "Proton")
        self.download_tabs.addTab(self.wine_tab, "Wine")

        downloads_tab_layout.addWidget(self.download_tabs) 

    def download_selected_proton_version(self):
        """Inicia la descarga de la versión de Proton seleccionada."""
        selected_item = self.list_versions_proton.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección Inválida", "Por favor, selecciona una versión de Proton para descargar.")
            return

        assets = selected_item.data(Qt.UserRole)
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Archivo Proton")
        layout = QVBoxLayout()

        label = QLabel("Selecciona el archivo específico para descargar:")
        layout.addWidget(label)

        version_combo = QComboBox()
        for asset in assets:
            name = asset["name"]
            size = asset.get("size", 0) / (1024 * 1024) 
            version_combo.addItem(f"{name} ({size:.1f} MB)", asset)
        layout.addWidget(version_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        self.config_manager.apply_breeze_style_to_widget(dialog) 

        if dialog.exec_() == QDialog.Accepted:
            selected_asset = version_combo.currentData()
            download_url = selected_asset["browser_download_url"]
            filename = selected_asset["name"]
            destination = self.config_manager.proton_download_dir / filename

            self.download_file(download_url, destination, f"Proton {selected_item.text()}")

    def setup_wine_download_tab(self):
        layout = QVBoxLayout()
        self.group_wine_repos = QGroupBox("Repositorios de Wine")
        repo_layout = QVBoxLayout()

        self.list_repos_wine = QListWidget()
        self.list_repos_wine.setSelectionMode(QListWidget.SingleSelection)
        self.load_wine_repositories()
        repo_layout.addWidget(self.list_repos_wine)

        repo_btn_layout = QHBoxLayout()
        self.btn_add_wine_repo = QPushButton("Añadir")
        self.btn_add_wine_repo.setAutoDefault(False)
        self.btn_add_wine_repo.clicked.connect(self.add_wine_repository)
        repo_btn_layout.addWidget(self.btn_add_wine_repo)

        self.btn_delete_wine_repo = QPushButton("Eliminar")
        self.btn_delete_wine_repo.setAutoDefault(False)
        self.btn_delete_wine_repo.clicked.connect(self.delete_wine_repository)
        repo_btn_layout.addWidget(self.btn_delete_wine_repo)

        self.btn_toggle_wine_repo = QPushButton("Habilitar/Deshabilitar")
        self.btn_toggle_wine_repo.setAutoDefault(False)
        self.btn_toggle_wine_repo.clicked.connect(self.toggle_wine_repository)
        repo_btn_layout.addWidget(self.btn_toggle_wine_repo)

        repo_layout.addLayout(repo_btn_layout)
        self.group_wine_repos.setLayout(repo_layout)
        layout.addWidget(self.group_wine_repos)

        self.group_wine_versions = QGroupBox("Versiones de Wine Disponibles")
        versions_layout = QVBoxLayout()

        self.list_versions_wine = QListWidget()
        versions_layout.addWidget(self.list_versions_wine)

        buttons_layout = QHBoxLayout()
        self.btn_update_wine = QPushButton("Actualizar Lista")
        self.btn_update_wine.setAutoDefault(False)
        self.btn_update_wine.clicked.connect(self.update_wine_versions)
        buttons_layout.addWidget(self.btn_update_wine)

        self.btn_download_wine = QPushButton("Descargar Seleccionado")
        self.btn_download_wine.setAutoDefault(False)
        self.btn_download_wine.clicked.connect(self.download_selected_wine_version)
        buttons_layout.addWidget(self.btn_download_wine)
        versions_layout.addLayout(buttons_layout)

        self.group_wine_versions.setLayout(versions_layout)
        layout.addWidget(self.group_wine_versions)

        self.wine_tab.setLayout(layout)

    def load_proton_repositories(self):
        """Carga y muestra los repositorios de Proton."""
        self.list_repos_proton.clear()
        repos = self.config_manager.get_repositories("proton")

        base_font = STYLE_BREEZE["font"]
        list_font_size = base_font.pointSize() + 2
        font_for_item = QFont(base_font.family(), list_font_size)
        font_for_item.setBold(True)

        for repo in repos:
            item = QListWidgetItem(repo["name"])
            item.setData(Qt.UserRole, repo["url"])
            item.setCheckState(Qt.Checked if repo.get("enabled", True) else Qt.Unchecked)
            item.setFont(font_for_item)
            self.list_repos_proton.addItem(item)

    def load_wine_repositories(self):
        """Carga y muestra los repositorios de Wine."""
        self.list_repos_wine.clear()
        repos = self.config_manager.get_repositories("wine")

        base_font = STYLE_BREEZE["font"]
        list_font_size = base_font.pointSize() + 2
        font_for_item = QFont(base_font.family(), list_font_size)
        font_for_item.setBold(True)

        for repo in repos:
            item = QListWidgetItem(repo["name"])
            item.setData(Qt.UserRole, repo["url"])
            item.setCheckState(Qt.Checked if repo.get("enabled", True) else Qt.Unchecked)
            item.setFont(font_for_item)
            self.list_repos_wine.addItem(item)

    def add_repository_dialog(self, repo_type: str):
        """Abre el diálogo para añadir un nuevo repositorio."""
        dialog = RepositoryDialog(repo_type, self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                name, url = dialog.get_repository_info()
                if self.config_manager.add_repository(repo_type, name, url):
                    if repo_type == "proton":
                        self.load_proton_repositories()
                    else:
                        self.load_wine_repositories()
                    QMessageBox.information(self, "Repositorio Añadido", f"Repositorio '{name}' añadido exitosamente.")
                else:
                    QMessageBox.warning(self, "Duplicado", f"El repositorio '{name}' ya existe.")
            except ValueError as e:
                QMessageBox.warning(self, "Entrada Inválida", str(e))

    def add_proton_repository(self):
        self.add_repository_dialog("proton")

    def add_wine_repository(self):
        self.add_repository_dialog("wine")

    def delete_repository_dialog(self, repo_type: str):
        """Elimina un repositorio seleccionado."""
        list_widget = self.list_repos_proton if repo_type == "proton" else self.list_repos_wine
        selected_row = list_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona un repositorio para eliminar.")
            return

        repo_name = list_widget.item(selected_row).text()
        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Estás seguro de que quieres eliminar el repositorio '{repo_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.config_manager.delete_repository(repo_type, selected_row):
                if repo_type == "proton":
                    self.load_proton_repositories()
                else:
                    self.load_wine_repositories()
                QMessageBox.information(self, "Eliminado", f"Repositorio '{repo_name}' eliminado.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el repositorio.")

    def delete_proton_repository(self):
        self.delete_repository_dialog("proton")

    def delete_wine_repository(self):
        self.delete_repository_dialog("wine")

    def toggle_repository_state(self, repo_type: str):
        """Habilita o deshabilita un repositorio seleccionado."""
        list_widget = self.list_repos_proton if repo_type == "proton" else self.list_repos_wine
        selected_row = list_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona un repositorio para habilitar/deshabilitar.")
            return

        item = list_widget.item(selected_row)
        current_state = item.checkState() == Qt.Checked
        if self.config_manager.toggle_repository(repo_type, selected_row, not current_state):
            item.setCheckState(Qt.Unchecked if current_state else Qt.Checked)

    def toggle_proton_repository(self):
        self.toggle_repository_state("proton")

    def toggle_wine_repository(self):
        self.toggle_repository_state("wine")

    def update_versions(self, repo_type: str):
        """Actualiza la lista de versiones disponibles desde los repositorios."""
        list_widget = self.list_versions_proton if repo_type == "proton" else self.list_versions_wine
        list_widget.clear()
        enabled_repos = [repo for repo in self.config_manager.get_repositories(repo_type) if repo.get("enabled", True)]

        if not enabled_repos:
            QMessageBox.information(self, "No hay Repositorios", f"No hay repositorios de {repo_type.capitalize()} activos. Por favor, añade o habilita uno.")
            return

        self.progress_dialog = QProgressDialog(f"Buscando versiones de {repo_type.capitalize()}...", "Cancelar", 0, len(enabled_repos), self)
        self.progress_dialog.setWindowTitle("Actualizando Versiones")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setCancelButton(None) 
        self.config_manager.apply_breeze_style_to_widget(self.progress_dialog)

        self.version_search_thread = VersionSearchThread(repo_type, enabled_repos)
        self.version_search_thread.progress.connect(self.progress_dialog.setValue)
        self.version_search_thread.new_release.connect(self._add_release_to_list)
        self.version_search_thread.finished.connect(self.progress_dialog.close)
        self.version_search_thread.error.connect(lambda msg: QMessageBox.warning(self, "Error Obteniendo Versiones", msg))

        self.version_search_thread.start()
        self.progress_dialog.exec_() 

    def update_proton_versions(self):
        self.update_versions("proton")

    def update_wine_versions(self):
        self.update_versions("wine")

    def _add_release_to_list(self, repo_type: str, release_name: str, version: str, assets: object, published_at: str):
        """Añade un lanzamiento a la lista correspondiente (Wine o Proton)."""
        list_widget = self.list_versions_proton if repo_type == "proton" else self.list_versions_wine
        item = QListWidgetItem(release_name)
        item.setData(Qt.UserRole, assets) 

        tooltip = f"<b>Versión:</b> {version}<br/>" \
                  f"<b>Fecha:</b> {published_at.split('T')[0] if published_at else 'N/A'}<br/>" \
                  f"<b>Archivos:</b> {len(assets)}"
        item.setToolTip(tooltip)

        base_font = STYLE_BREEZE["font"]
        list_font_size = base_font.pointSize() + 2
        font_for_item = QFont(base_font.family(), list_font_size)
        font_for_item.setBold(True)
        item.setFont(font_for_item)

        list_widget.addItem(item)

    def download_selected_wine_version(self):
        """Inicia la descarga de la versión de Wine seleccionada."""
        selected_item = self.list_versions_wine.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección Inválida", "Por favor, selecciona una versión de Wine para descargar.")
            return

        assets = selected_item.data(Qt.UserRole)

        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Archivo Wine")
        layout = QVBoxLayout()

        label = QLabel("Selecciona el archivo específico para descargar:")
        layout.addWidget(label)

        version_combo = QComboBox()
        for asset in assets:
            name = asset["name"]
            size = asset.get("size", 0) / (1024 * 1024)
            version_combo.addItem(f"{name} ({size:.1f} MB)", asset)
        layout.addWidget(version_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        self.config_manager.apply_breeze_style_to_widget(dialog)

        if dialog.exec_() == QDialog.Accepted:
            selected_asset = version_combo.currentData()
            download_url = selected_asset["browser_download_url"]
            filename = selected_asset["name"]
            destination = self.config_manager.wine_download_dir / filename

            self.download_file(download_url, destination, f"Wine {selected_item.text()}")

    def download_file(self, url: str, destination: Path, name: str):
        """Inicia el proceso de descarga de un archivo."""
        self.progress_dialog = QProgressDialog(f"Descargando {name}...", "Cancelar", 0, 100, self)
        self.progress_dialog.setWindowTitle("Descargando")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.config_manager.apply_breeze_style_to_widget(self.progress_dialog)

        self.download_progress_bar = QProgressBar(self.progress_dialog)
        self.download_progress_bar.setRange(0, 100)
        self.progress_dialog.setBar(self.download_progress_bar)

        self.download_thread = DownloadThread(url, destination, name, self.config_manager, "Downloads")

        self.download_thread.progress.connect(self.download_progress_bar.setValue)
        self.download_thread.finished.connect(partial(self.on_download_finished, name=name))
        self.download_thread.error.connect(self.show_download_error)
        self.progress_dialog.canceled.connect(self.download_thread.stop)

        self.download_thread.start()
        self.progress_dialog.exec_()

    def show_download_error(self, error_msg: str):
        """Muestra un mensaje de error de descarga."""
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error de Descarga", error_msg)

    def on_download_finished(self, filepath: str, name: str):
        """Maneja la finalización de una descarga, iniciando la descompresión."""
        self.progress_dialog.setLabelText(f"Descomprimiendo {name}...")
        self.progress_dialog.setMaximum(0)
        self.config_manager.apply_breeze_style_to_widget(self.progress_dialog)

        self.decompression_thread = DecompressionThread(filepath, self.config_manager, name, "Downloads")

        self.decompression_thread.finished.connect(partial(self.on_decompression_finished, name=name))
        self.decompression_thread.error.connect(self.show_decompression_error)
        self.decompression_thread.start()

    def show_decompression_error(self, error_msg: str):
        """Muestra un mensaje de error de descompresión."""
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error de Descompresión", error_msg)

    def on_decompression_finished(self, path: str, name: str):
        """Maneja la finalización de la descompresión."""
        self.progress_dialog.close()
        QMessageBox.information(self, "Éxito", f"Descarga y descompresión de {name} completadas.\nInstalado en: {path}")

    def save_new_config(self):
        """Guarda una nueva configuración o actualiza una existente."""
        try:
            new_config_name = self.config_name.text().strip()
            if not new_config_name:
                QMessageBox.warning(self, "Error", "Debes especificar un nombre para la configuración.")
                return

            original_config_name = self.current_config_name_for_editing

            if new_config_name != original_config_name and new_config_name in self.config_manager.configs.get("configs", {}):
                QMessageBox.warning(self, "Nombre Duplicado", f"Ya existe una configuración con el nombre '{new_config_name}'. Por favor, elige otro nombre.")
                return

            config_type = "wine" if self.config_type.currentText() == "Wine" else "proton"
            architecture = self.architecture_combo.currentText()
            prefix = self.prefix_path.text().strip()

            config_data = {
                "type": config_type,
                "arch": architecture
            }

            if config_type == "proton":
                proton_directory = self.proton_directory.text().strip()
                if not proton_directory or not Path(proton_directory).is_dir():
                    QMessageBox.warning(self, "Error", "Debes especificar un directorio de Proton válido.")
                    return
                config_data["proton_dir"] = proton_directory

                if self.radio_proton_steam_prefix.isChecked():
                    appid = self.appid_line_edit.text().strip()
                    if not appid.isdigit() or not appid:
                        QMessageBox.warning(self, "Error", "Para un prefijo de Steam, debes ingresar un APPID numérico válido.")
                        return
                    steam_compat_data_root = Path.home() / ".local/share/Steam/steamapps/compatdata"
                    config_data["prefix"] = str(steam_compat_data_root / appid / "pfx")
                    config_data["steam_appid"] = appid
                else:
                    if not prefix:
                        QMessageBox.warning(self, "Error", "Debes especificar un prefijo para Proton personalizado.")
                        return
                    config_data["prefix"] = prefix
            else:
                if not prefix:
                    QMessageBox.warning(self, "Error", "Debes especificar un prefijo para Wine.")
                    return
                config_data["prefix"] = prefix
                wine_directory = self.wine_directory.text().strip()
                if wine_directory:
                    if not Path(wine_directory).is_dir():
                        QMessageBox.warning(self, "Error", "El directorio de instalación de Wine especificado no es válido.")
                        return
                    config_data["wine_dir"] = wine_directory

            self.config_manager.configs.setdefault("configs", {})[new_config_name] = config_data
            self.config_manager.save_configs()
            QMessageBox.information(self, "Guardado", f"Configuración '{new_config_name}' guardada exitosamente.")

            self.load_configs() 
            self.tabs.setCurrentIndex(0)
            self.current_config_name_for_editing = None

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando configuración: {str(e)}")

    def setup_settings_tab(self):
        main_layout = QVBoxLayout()

        paths_group = QGroupBox("Rutas")
        paths_layout = QFormLayout()

        # Campo para Winetricks (existente)
        self.edit_winetricks_path = QLineEdit(self.config_manager.get_winetricks_path())
        self.btn_winetricks = QPushButton("Explorar...")
        self.btn_winetricks.setAutoDefault(False)
        self.btn_winetricks.clicked.connect(self.browse_winetricks)
        winetricks_layout = QHBoxLayout()
        winetricks_layout.addWidget(self.edit_winetricks_path)
        winetricks_layout.addWidget(self.btn_winetricks)
        paths_layout.addRow("Ruta de Winetricks:", winetricks_layout)

        # Campo para la Ruta Raíz de Steam
        self.edit_steam_root_path = QLineEdit(self.config_manager.get_steam_root_path())
        self.edit_steam_root_path.setPlaceholderText("Dejar en blanco para detección automática")
        self.btn_browse_steam_root = QPushButton("Explorar...")
        self.btn_browse_steam_root.setAutoDefault(False)
        self.btn_browse_steam_root.clicked.connect(self.browse_steam_root)
        steam_root_layout = QHBoxLayout()
        steam_root_layout.addWidget(self.edit_steam_root_path)
        steam_root_layout.addWidget(self.btn_browse_steam_root)
        paths_layout.addRow("Ruta Raíz de Steam:", steam_root_layout)

        paths_group.setLayout(paths_layout)
        main_layout.addWidget(paths_group)

        install_options_group = QGroupBox("Tema y Opciones de Instalación")
        install_options_layout = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro"])
        current_theme = self.config_manager.get_theme()
        self.theme_combo.setCurrentText("Oscuro" if current_theme == "dark" else "Claro")
        install_options_layout.addRow("Tema de Interfaz:", self.theme_combo)

        silent_layout = QHBoxLayout()
        silent_label = QLabel("Habilitar modo silencioso por defecto (-q)")
        self.checkbox_silent_global = QCheckBox()
        self.checkbox_silent_global.setChecked(self.config_manager.get_silent_install())
        silent_layout.addWidget(silent_label)
        silent_layout.addStretch()
        silent_layout.addWidget(self.checkbox_silent_global)
        install_options_layout.addRow(silent_layout)

        force_winetricks_layout = QHBoxLayout()
        force_winetricks_label = QLabel("Forzar instalación de Winetricks (--force)")
        self.checkbox_force_winetricks = QCheckBox()
        self.checkbox_force_winetricks.setChecked(self.config_manager.get_force_winetricks_install())
        force_winetricks_layout.addWidget(force_winetricks_label)
        force_winetricks_layout.addStretch()
        force_winetricks_layout.addWidget(self.checkbox_force_winetricks)
        install_options_layout.addRow(force_winetricks_layout)

        install_options_group.setLayout(install_options_layout)
        main_layout.addWidget(install_options_group)

        backup_options_group = QGroupBox("Opciones de Backup") 
        backup_options_layout = QFormLayout()

        ask_for_backup_layout = QHBoxLayout()
        ask_for_backup_label = QLabel("Preguntar por backup antes de iniciar una herramienta/instalación")
        self.checkbox_ask_for_backup_before_action = QCheckBox()
        self.checkbox_ask_for_backup_before_action.setToolTip("Si está activado, se le preguntará si desea hacer un backup antes de ciertas operaciones que puedan modificar el prefijo.")
        self.checkbox_ask_for_backup_before_action.setChecked(self.config_manager.get_ask_for_backup_before_action())
        ask_for_backup_layout.addWidget(ask_for_backup_label)
        ask_for_backup_layout.addStretch()
        ask_for_backup_layout.addWidget(self.checkbox_ask_for_backup_before_action)
        backup_options_layout.addRow(ask_for_backup_layout)

        backup_options_group.setLayout(backup_options_layout)
        main_layout.addWidget(backup_options_group)

        main_layout.addStretch()

        self.btn_save_settings = QPushButton("Guardar Ajustes")
        self.btn_save_settings.setAutoDefault(False)
        self.btn_save_settings.clicked.connect(self.save_settings)
        stretch_button_layout = QHBoxLayout()
        stretch_button_layout.addWidget(self.btn_save_settings)
        main_layout.addLayout(stretch_button_layout)

        self.settings_tab.setLayout(main_layout)

    def update_save_settings_button_state(self):
        """Habilita/deshabilita el botón 'Guardar Ajustes' basándose en si hay una instalación en curso."""

        if hasattr(self.config_manager, 'app_instance') and self.config_manager.app_instance:
            is_installer_running = self.config_manager.app_instance.installer_thread is not None and self.config_manager.app_instance.installer_thread.isRunning()
            is_backup_running = self.config_manager.app_instance.backup_thread is not None and self.config_manager.app_instance.backup_thread.isRunning()
            self.btn_save_settings.setEnabled(not is_installer_running and not is_backup_running)
        else:
            self.btn_save_settings.setEnabled(True) # Por defecto habilitado si no hay app_instance

    def _apply_theme_setting(self, text: str):
        """Este método ya no se llama directamente por currentTextChanged.
        Ahora solo actualiza la configuración en memoria. El cambio real se aplica al reiniciar la app."""
        theme_name = "dark" if text == "Oscuro" else "light"
        self.config_manager.set_theme(theme_name)

    def save_settings(self):
        """Guarda los ajustes generales de la aplicación."""
        try:
            # Guardar ruta de Winetricks
            winetricks_path_ok = self.config_manager.set_winetricks_path(self.edit_winetricks_path.text().strip())

            # Guardar ruta de Steam
            steam_root_path = self.edit_steam_root_path.text().strip()
            self.config_manager.set_steam_root_path(steam_root_path)

            # Guardar Tema
            theme = "dark" if self.theme_combo.currentText() == "Oscuro" else "light"
            self.config_manager.set_theme(theme)
            
            # Guardar otras opciones
            self.config_manager.set_silent_install(self.checkbox_silent_global.isChecked())
            self.config_manager.set_force_winetricks_install(self.checkbox_force_winetricks.isChecked())
            self.config_manager.set_ask_for_backup_before_action(self.checkbox_ask_for_backup_before_action.isChecked())

            # Guardar todo en el archivo JSON
            self.config_manager.save_configs()

            QMessageBox.information(self, "Guardado", "Ajustes guardados exitosamente.\nAlgunos cambios, como el tema o la ruta de Steam, pueden requerir un reinicio para aplicarse completamente.")
            self.config_saved.emit() 
            self.accept() 
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando ajustes: {str(e)}")

    def browse_steam_root(self):
        """Abre un diálogo para seleccionar la ruta raíz de Steam."""
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setWindowTitle("Seleccionar Directorio Raíz de Steam")

        # Usar una nueva clave para el último directorio o una existente
        dialog.setDirectory(self.config_manager.get_last_browsed_dir("steam_root"))
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)  

        self.config_manager.apply_breeze_style_to_widget(dialog)

        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                self.edit_steam_root_path.setText(selected[0])
                self.config_manager.set_last_browsed_dir("steam_root", selected[0])

    def browse_winetricks(self):
        """Abre un diálogo para seleccionar la ruta de Winetricks."""
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Ejecutables (*);;Todos los Archivos (*)")

        dialog.setDirectory(self.config_manager.get_last_browsed_dir("winetricks"))
        dialog.setFilter(QDir.AllEntries | QDir.AllDirs | QDir.NoDotAndDotDot) 

        self.config_manager.apply_breeze_style_to_widget(dialog)

        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                self.edit_winetricks_path.setText(selected[0])

                self.config_manager.set_last_browsed_dir("winetricks", str(Path(selected[0]).parent))


    def load_configs(self):
        """Carga y muestra las configuraciones guardadas."""
        self.list_config.clear()
        configs = self.config_manager.configs.get("configs", {})
        last_used = self.config_manager.configs.get("last_used", "")

        
        sorted_config_names = sorted(configs.keys())
        if last_used and last_used in sorted_config_names:
            sorted_config_names.remove(last_used)
            sorted_config_names.insert(0, last_used)
    
        base_font = STYLE_BREEZE["font"]
     
        list_font_size = base_font.pointSize() + 1
        font_for_item = QFont(base_font.family(), list_font_size)
        font_for_item.setBold(True)

        for name in sorted_config_names:
            item = QListWidgetItem(name)
            if name == last_used:
                item.setText(f"{name} (Por Defecto)")
            item.setFont(font_for_item) 
            self.list_config.addItem(item)
            if name == last_used:
                self.list_config.setCurrentItem(item) 

        self.update_displayed_config_info() 

    def edit_config(self, item: QListWidgetItem):
        """Carga una configuración seleccionada para edición."""
        config_name_display = item.text()
        config_name = config_name_display.replace(" (Por Defecto)", "").strip()
        self.current_config_name_for_editing = config_name 

        config = self.config_manager.get_config(config_name)
        if not config:
            QMessageBox.warning(self, "Error", "Configuración no encontrada o corrupta.")
            return

        self.tabs.setCurrentIndex(1) 
        self.config_name.setText(config_name)

        self.config_type.setCurrentText("Proton" if config.get("type") == "proton" else "Wine")
        self.prefix_path.setText(config.get("prefix", ""))
        self.architecture_combo.setCurrentText(config.get("arch", "win64"))

        if config.get("type") == "proton":
            self.proton_directory.setText(config.get("proton_dir", ""))
            self.wine_directory.setText("") 
            if "steam_appid" in config:
                self.radio_proton_steam_prefix.setChecked(True)
                self.appid_line_edit.setText(config["steam_appid"])
            else:
                self.radio_proton_custom_prefix.setChecked(True)
                self.appid_line_edit.setText("")
        else: 
            self.wine_directory.setText(config.get("wine_dir", ""))
            self.proton_directory.setText("")
            self.radio_proton_custom_prefix.setChecked(True)
            self.appid_line_edit.setText("")

        self.update_config_field_visibility()

    def delete_config(self):
        """Elimina una configuración seleccionada."""
        selected = self.list_config.currentItem()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Selecciona una configuración para eliminar.")
            return

        config_name_display = selected.text()
        config_name = config_name_display.replace(" (Por Defecto)", "").strip()

        if config_name == "Wine-System":
            QMessageBox.warning(self, "Error", "No se puede eliminar la configuración 'Wine-System' ya que es la predeterminada del sistema.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar la configuración '{config_name}'? Esto no eliminará el prefijo o los archivos de Wine/Proton asociados.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.config_manager.delete_config(config_name):
                self.load_configs()
                QMessageBox.information(self, "Éxito", f"Configuración '{config_name}' eliminada.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la configuración.")

    def set_default_config(self):
        """Establece una configuración seleccionada como predeterminada."""
        selected = self.list_config.currentItem()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Selecciona una configuración para establecer como predeterminada.")
            return

        config_name = selected.text().replace(" (Por Defecto)", "").strip()
        self.config_manager.configs["last_used"] = config_name
        self.config_manager.save_configs()
        QMessageBox.information(self, "Éxito", f"Configuración '{config_name}' establecida como predeterminada.")
        self.load_configs() 

    def update_displayed_config_info(self):
        """Actualiza la información de la configuración seleccionada en la GUI."""
        selected = self.list_config.currentItem()
        if not selected:
            self.lbl_config_info.setText("Selecciona una configuración para ver los detalles.")
            return

        config_name = selected.text().replace(" (Por Defecto)", "").strip()
        config = self.config_manager.get_config(config_name)
        if not config:
            self.lbl_config_info.setText("Configuración no encontrada o corrupta.")
            return

        try:
            env = self.config_manager.get_current_environment(config_name)
        except Exception as e:
            self.lbl_config_info.setText(f"Error cargando el entorno para '{config_name}': {e}")
            return

        version = env.get("PROTON_VERSION") if config.get("type") == "proton" else env.get("WINE_VERSION", "Desconocida")
        wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "N/A")

        info = [
            f"<b>Configuración Actual:</b> {config_name}",
            f"<b>Tipo:</b> {'Proton' if config['type'] == 'proton' else 'Wine'}",
            f"<b>Versión Detectada:</b> <span style='color: {COLOR_BREEZE_PRIMARY}; font-weight: bold;'>{version}</span>",
        ]

        if config['type'] == 'proton':
            info.extend([
                f"<b>Wine en Proton:</b> <span style='color: {COLOR_BREEZE_PRIMARY}; font-weight: bold;'>{wine_version_in_proton}</span>",
                f"<b>Directorio de Proton:</b> {config.get('proton_dir', 'No especificado')}"
            ])
            if "steam_appid" in config:
                info.append(f"<b>APPID de Steam:</b> {config['steam_appid']}")
                info.append(f"<b>Prefijo gestionado por Steam:</b> Sí")
            else:
                info.append(f"<b>Prefijo personalizado:</b> Sí")
        else:
            wine_dir = config.get('wine_dir', 'Sistema (PATH)')
            info.extend([
                f"<b>Directorio de Wine:</b> {wine_dir}"
            ])

        info.extend([
            f"<b>Arquitectura:</b> {config.get('arch', 'win64')}",
            f"<b>Prefijo:</b> <span style='color: #FFB347; font-weight: bold;'>{config.get('prefix', 'No especificado')}</span>"
        ])

        self.lbl_config_info.setText("<br>".join(info))

    def browse_prefix(self):
        """Abre un diálogo para seleccionar el directorio de prefijo."""
        key = "wine_prefix" if self.config_type.currentText() == "Wine" else "proton_prefix"
        path = self._get_directory_path("Seleccionar Directorio de Prefijo de Wine", key)
        if path:
            self.prefix_path.setText(path)

    def browse_wine(self):
        """Abre un diálogo para seleccionar el directorio de instalación de Wine."""
        path = self._get_directory_path("Seleccionar Directorio de Instalación de Wine (ej., bin/wine)", "wine_install")
        if path:
            self.wine_directory.setText(path)

    def browse_proton(self):
        """Abre un diálogo para seleccionar el directorio de instalación de Proton."""
        path = self._get_directory_path("Seleccionar Directorio de Instalación de Proton (ej., proton_dist/files)", "proton_install")
        if path:
            self.proton_directory.setText(path)

    def _get_directory_path(self, title="Seleccionar Directorio", config_key: str = "default") -> str | None:
        """Helper para abrir un diálogo de selección de directorio."""
        dialog = QFileDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)

        dialog.setDirectory(self.config_manager.get_last_browsed_dir(config_key))

        self.config_manager.apply_breeze_style_to_widget(dialog)

        if dialog.exec_() == QDialog.Accepted:
            selected_path = dialog.selectedFiles()[0]

            self.config_manager.set_last_browsed_dir(config_key, selected_path)
            return selected_path
        return None

    def test_configuration(self):
        """Prueba la configuración actual de Wine/Proton."""
        config_name_test = self.config_name.text().strip()
        if not config_name_test:
            QMessageBox.warning(self, "Advertencia", "Por favor, introduce un nombre para la configuración antes de probar.")
            return

        temp_config = {
            "type": "wine" if self.config_type.currentText() == "Wine" else "proton",
            "prefix": self.prefix_path.text().strip(),
            "arch": self.architecture_combo.currentText()
        }
        if temp_config["type"] == "proton":
            temp_config["proton_dir"] = self.proton_directory.text().strip()
            if self.radio_proton_steam_prefix.isChecked():
                appid = self.appid_line_edit.text().strip()
                if not appid.isdigit() or not appid:
                    QMessageBox.warning(self, "Error", "Para un prefijo de Steam, debes ingresar un APPID numérico válido.")
                    return
                steam_compat_data_root = Path.home() / ".local/share/Steam/steamapps/compatdata"
                temp_config["prefix"] = str(steam_compat_data_root / appid / "pfx")
                temp_config["steam_appid"] = appid
        elif self.wine_directory.text().strip():
            temp_config["wine_dir"] = self.wine_directory.text().strip()

        original_configs = self.config_manager.configs.copy()
        temp_configs_dict = {k: v.copy() if isinstance(v, dict) else v for k, v in original_configs.get("configs", {}).items()}
        temp_configs_dict[config_name_test] = temp_config
        self.config_manager.configs["configs"] = temp_configs_dict
        self.config_manager.configs["last_used"] = config_name_test 

        try:
            env = self.config_manager.get_current_environment(config_name_test)

            wine_executable = env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en la ruta especificada o en el PATH del sistema: {wine_executable}")

            process = subprocess.run(
                [wine_executable, "--version"],
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
                check=True 
            )
            version_output = process.stdout.strip()
            QMessageBox.information(
                self,
                "Prueba Exitosa",
                f"Configuración válida.\nVersión Detectada: {version_output}"
            )
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error de Prueba", f"Error de archivo: {str(e)}")
        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "Error de Prueba", "El comando Wine/Proton --version tardó demasiado en responder.")
        except subprocess.CalledProcessError as e:
            error_details = f"Código de Salida: {e.returncode}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            QMessageBox.critical(self, "Error de Prueba", f"El comando Wine/Proton --version falló.\nDetalles:\n{error_details}")
        except Exception as e:
            QMessageBox.critical(self, "Error de Prueba", f"Error inesperado durante la prueba: {str(e)}")
        finally:

            self.config_manager.configs = original_configs
            self.config_manager.save_configs() 
            