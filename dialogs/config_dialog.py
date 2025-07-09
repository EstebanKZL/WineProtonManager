import json
import subprocess
import time
from pathlib import Path
from functools import partial # Importar partial para conexiones de señal mas limpias

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QCheckBox, QDialog, QDialogButtonBox,
    QMessageBox, QGroupBox, QComboBox, QLineEdit, QFileDialog,
    QTabWidget, QFormLayout, QScrollArea, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTreeWidget, QTreeWidgetItem, QProgressDialog, QProgressBar,
    QInputDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDir, QSize, QUrl, QTimer
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QDesktopServices
from urllib.request import urlopen, Request, HTTPError

from styles import STYLE_STEAM_DECK, COLOR_PRIMARY, COLOR_ACCENT, COLOR_PRESSED, \
                   COLOR_DISABLED_BG_LIGHT, COLOR_DISABLED_TEXT_LIGHT, COLOR_BORDER_LIGHT, \
                   COLOR_DARK_TEXT, COLOR_DARK_WINDOW, COLOR_DARK_WINDOW_TEXT, COLOR_DARK_BASE, \
                   COLOR_DARK_BUTTON, COLOR_DARK_BUTTON_TEXT, COLOR_DARK_HIGHLIGHT, \
                   COLOR_DARK_HIGHLIGHT_TEXT, COLOR_DARK_BORDER, \
                   COLOR_LIGHT_WINDOW, COLOR_LIGHT_WINDOW_TEXT, COLOR_LIGHT_BASE, \
                   COLOR_LIGHT_TEXT, COLOR_LIGHT_BUTTON, COLOR_LIGHT_BUTTON_TEXT, \
                   COLOR_LIGHT_HIGHLIGHT, COLOR_LIGHT_HIGHLIGHT_TEXT, COLOR_LIGHT_BORDER
                   # Assuming ConfigManager is in ../config_manager.py
from config_manager import ConfigManager # Corrected import path
# Assuming DownloadThread and DecompressionThread are in ../downloader.py
from downloader import DownloadThread, DecompressionThread # Corrected import path
from dialogs.repository_dialog import RepositoryDialog

class ConfigDialog(QDialog):
    config_saved = pyqtSignal()
    
    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Configuracion de Entorno")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.apply_steamdeck_style()
        self.load_configs() # Cargar configuraciones aqui para asegurar que la lista este poblada

    def apply_steamdeck_style(self):
        self.setFont(STYLE_STEAM_DECK["font"]) # Aplicar fuente de estilo global a todo el dialogo.
        theme = self.config_manager.get_theme()
        
        # 1. Iterar sobre todos los widgets hijos para aplicar estilos generales
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                # Aplicar el estilo de boton correcto (azul en oscuro, etc.)
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme == "dark" else STYLE_STEAM_DECK["button_style"])
                widget.setFont(STYLE_STEAM_DECK["font"]) # Asegurar que el texto del boton tenga la fuente
            elif isinstance(widget, QGroupBox):
                widget.setFont(STYLE_STEAM_DECK["title_font"]) # Titulo de grupo en negrita
                # Aplicar el estilo de grupo correcto (bordes, color de titulo)
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_groupbox_style"] if theme == "dark" else STYLE_STEAM_DECK["groupbox_style"])
            elif isinstance(widget, QLabel):
                widget.setFont(STYLE_STEAM_DECK["font"]) # Asegurar que las etiquetas tambien tengan la fuente
            elif isinstance(widget, QComboBox) or isinstance(widget, QLineEdit):
                widget.setFont(STYLE_STEAM_DECK["font"]) # Asegurar que combos y lineedits tengan la fuente
        
        # 2. Aplicar estilo especifico para QListWidgets (listas de repositorios y versiones)
        # Esto ya incluye negrita y tamano consistente.
        list_style_template = """
            QListWidget {{
                background-color: {};
                color: {};
                border: 1px solid {};
                font-size: {}px;
                font-weight: bold;
            }}
            QListWidget::item {{
                padding: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {};
                color: white;
            }}
        """

        base_font_size = STYLE_STEAM_DECK["font"].pointSize()
        list_font_size = base_font_size + 6

        if theme == "dark":
            # REMOVE .name() here, as COLOR_DARK_WINDOW, COLOR_DARK_TEXT are already strings
            list_bg = COLOR_DARK_WINDOW
            list_text = COLOR_DARK_TEXT
            list_border = COLOR_DARK_BORDER
            list_highlight = COLOR_PRIMARY
        else:
            # REMOVE .name() here, as COLOR_LIGHT_BASE, COLOR_LIGHT_TEXT are already strings
            list_bg = COLOR_LIGHT_BASE
            list_text = COLOR_LIGHT_TEXT
            list_border = COLOR_LIGHT_BORDER
            list_highlight = COLOR_PRIMARY

        unified_list_style = list_style_template.format(
            list_bg, list_text, list_border, list_font_size, list_highlight
        )

        self.list_repos_proton.setStyleSheet(unified_list_style)
        self.list_repos_wine.setStyleSheet(unified_list_style)
        self.list_versions_proton.setStyleSheet(unified_list_style)
        self.list_versions_wine.setStyleSheet(unified_list_style)
        
        self.list_config.setStyleSheet(STYLE_STEAM_DECK["dark_table_style"] if theme == "dark" else STYLE_STEAM_DECK["table_style"])


    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        self.current_tab = QWidget()
        self.setup_current_config_tab()
        self.tabs.addTab(self.current_tab, "Configuraciones Guardadas")

        self.new_tab = QWidget()
        self.setup_new_config_tab()
        self.tabs.addTab(self.new_tab, "Crear/Editar Configuracion")

        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Ajustes Generales")

        self.downloads_tab = QWidget()
        self.setup_downloads_tab()
        self.tabs.addTab(self.downloads_tab, "Descargas de Versiones")

        layout.addWidget(self.tabs)
        
        # Botones en la parte inferior del dialogo
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.button(QDialogButtonBox.Close).setAutoDefault(False)
        self.button_box.accepted.connect(self.accept) # Conectar OK si es necesario, pero Close es mas apropiado para ConfigDialog
        self.button_box.rejected.connect(self.reject)
        self.button_box.clicked.connect(self.close) # Usar clicked para Close
        layout.addWidget(self.button_box)
        
        self.setLayout(layout)

    def setup_current_config_tab(self):
        layout = QVBoxLayout()
        self.list_config = QListWidget()
        self.list_config.itemDoubleClicked.connect(self.edit_config)
        self.list_config.itemSelectionChanged.connect(self.update_displayed_config_info)
        layout.addWidget(self.list_config)

        btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("Eliminar Configuracion")
        self.btn_delete.setAutoDefault(False)
        self.btn_delete.clicked.connect(self.delete_config)
        btn_layout.addWidget(self.btn_delete)

        self.btn_set_default = QPushButton("Establecer por Defecto")
        self.btn_set_default.setAutoDefault(False)
        self.btn_set_default.clicked.connect(self.set_default_config)
        btn_layout.addWidget(self.btn_set_default)

        layout.addLayout(btn_layout)

        self.lbl_config_info = QLabel("Selecciona una configuracion para ver los detalles")
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

        self.wine_directory = QLineEdit()
        self.btn_wine = QPushButton("Explorar...")
        self.btn_wine.setAutoDefault(False)
        self.btn_wine.clicked.connect(self.browse_wine)
        wine_layout = QHBoxLayout()
        wine_layout.addWidget(self.wine_directory)
        wine_layout.addWidget(self.btn_wine)

        self.wine_group = QGroupBox("Configuracion de Wine Personalizada")
        wine_inner_layout = QFormLayout()
        wine_inner_layout.addRow("Directorio de instalacion de Wine:", wine_layout)
        self.wine_group.setLayout(wine_inner_layout)

        self.proton_directory = QLineEdit()
        self.btn_proton = QPushButton("Explorar...")
        self.btn_proton.setAutoDefault(False)
        self.btn_proton.clicked.connect(self.browse_proton)
        proton_layout = QHBoxLayout()
        proton_layout.addWidget(self.proton_directory)
        proton_layout.addWidget(self.btn_proton)

        self.proton_group = QGroupBox("Configuracion de Proton Personalizada")
        proton_inner_layout = QFormLayout()
        proton_inner_layout.addRow("Directorio de instalacion de Proton:", proton_layout)
        self.proton_group.setLayout(proton_inner_layout)

        layout.addRow(self.wine_group)
        layout.addRow(self.proton_group)
        
        buttons_layout = QHBoxLayout()
        self.btn_test = QPushButton("Probar Configuracion")
        self.btn_test.setAutoDefault(False)
        self.btn_test.clicked.connect(self.test_configuration)
        buttons_layout.addWidget(self.btn_test)
        
        self.btn_save_config = QPushButton("Guardar Configuracion")
        self.btn_save_config.setAutoDefault(False)
        self.btn_save_config.clicked.connect(self.save_new_config)
        buttons_layout.addWidget(self.btn_save_config)
        layout.addRow(buttons_layout)

        self.update_config_field_visibility() # Inicializar visibilidad
        self.new_tab.setLayout(layout)

    def setup_downloads_tab(self):
        layout = QVBoxLayout()
        
        self.download_tabs = QTabWidget()
        
        self.proton_tab = QWidget()
        self.setup_proton_download_tab()
        self.download_tabs.addTab(self.proton_tab, "Proton")
        
        self.wine_tab = QWidget()
        self.setup_wine_download_tab()
        self.download_tabs.addTab(self.wine_tab, "Wine")
        
        layout.addWidget(self.download_tabs)
        self.downloads_tab.setLayout(layout)

    def download_selected_proton_version(self):
        selected_item = self.list_versions_proton.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleccion Invalida", "Por favor, selecciona una version de Proton para descargar.")
            return

        assets = selected_item.data(Qt.UserRole)
        
        # Dialogo para seleccionar el asset especifico (ej., version tar.gz)
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Archivo Proton")
        layout = QVBoxLayout()
        
        label = QLabel("Selecciona el archivo especifico para descargar:")
        layout.addWidget(label)
        
        version_combo = QComboBox()
        for asset in assets:
            name = asset["name"]
            size = asset.get("size", 0) / (1024 * 1024)  # Convertir a MB
            version_combo.addItem(f"{name} ({size:.1f} MB)", asset)
        layout.addWidget(version_combo)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.setFont(STYLE_STEAM_DECK["font"]) # Aplicar fuente al dialogo
        self.config_manager.apply_theme_to_dialog(dialog) # Aplicar tema al dialogo
        

        if dialog.exec_() == QDialog.Accepted:
            selected_asset = version_combo.currentData()
            download_url = selected_asset["browser_download_url"]
            filename = selected_asset["name"]
            destination = self.config_manager.proton_download_dir / filename
            
            self.download_file(download_url, destination, f"Proton {selected_item.text()}")

    def setup_proton_download_tab(self):
        layout = QVBoxLayout()
        
        self.group_proton_repos = QGroupBox("Repositorios de Proton")
        repo_layout = QVBoxLayout()
        
        self.list_repos_proton = QListWidget()
        self.list_repos_proton.setSelectionMode(QListWidget.SingleSelection)
        self.load_proton_repositories()
        repo_layout.addWidget(self.list_repos_proton)
        
        repo_btn_layout = QHBoxLayout()
        
        self.btn_add_proton_repo = QPushButton("Anadir")
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
        layout.addWidget(self.group_proton_repos)
        
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
        layout.addWidget(self.group_proton_versions)
        
        self.proton_tab.setLayout(layout)
        
    def setup_wine_download_tab(self):
        layout = QVBoxLayout()
        
        self.group_wine_repos = QGroupBox("Repositorios de Wine")
        repo_layout = QVBoxLayout()
        
        self.list_repos_wine = QListWidget()
        self.list_repos_wine.setSelectionMode(QListWidget.SingleSelection)
        self.load_wine_repositories()
        repo_layout.addWidget(self.list_repos_wine)
        
        repo_btn_layout = QHBoxLayout()
        
        self.btn_add_wine_repo = QPushButton("Anadir")
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
        self.list_repos_proton.clear()
        repos = self.config_manager.get_repositories("proton")
        for repo in repos:
            item = QListWidgetItem(repo["name"])
            item.setData(Qt.UserRole, repo["url"])
            item.setCheckState(Qt.Checked if repo.get("enabled", True) else Qt.Unchecked)
            self.list_repos_proton.addItem(item)
            
    def load_wine_repositories(self):
        self.list_repos_wine.clear()
        repos = self.config_manager.get_repositories("wine")
        for repo in repos:
            item = QListWidgetItem(repo["name"])
            item.setData(Qt.UserRole, repo["url"])
            item.setCheckState(Qt.Checked if repo.get("enabled", True) else Qt.Unchecked)
            self.list_repos_wine.addItem(item)
            
    def add_repository_dialog(self, repo_type: str):
        dialog = RepositoryDialog(repo_type, self)
        # Aplicar el tema al diálogo del repositorio
        self.config_manager.apply_theme_to_dialog(dialog)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                name, url = dialog.get_repository_info()
                if self.config_manager.add_repository(repo_type, name, url):
                    if repo_type == "proton":
                        self.load_proton_repositories()
                    else:
                        self.load_wine_repositories()
                    QMessageBox.information(self, "Repositorio Anadido", f"Repositorio '{name}' anadido exitosamente.")
                else:
                    QMessageBox.warning(self, "Duplicado", f"El repositorio '{name}' ya existe.")
            except ValueError as e:
                QMessageBox.warning(self, "Entrada Invalida", str(e))

    def add_proton_repository(self):
        self.add_repository_dialog("proton")
            
    def add_wine_repository(self):
        self.add_repository_dialog("wine")
            
    def delete_repository_dialog(self, repo_type: str):
        list_widget = self.list_repos_proton if repo_type == "proton" else self.list_repos_wine
        selected_row = list_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Advertencia", "Selecciona un repositorio para eliminar.")
            return
            
        repo_name = list_widget.item(selected_row).text()
        reply = QMessageBox.question(self, "Confirmar Eliminacion", 
                                     f"Estas seguro de que quieres eliminar el repositorio '{repo_name}'?",
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
        list_widget = self.list_versions_proton if repo_type == "proton" else self.list_versions_wine
        list_widget.clear()
        enabled_repos = [repo for repo in self.config_manager.get_repositories(repo_type) if repo.get("enabled", True)]
        
        if not enabled_repos:
            QMessageBox.information(self, "No hay Repositorios", f"No hay repositorios de {repo_type.capitalize()} activos. Por favor, anade o habilita uno.")
            return

        self.progress_dialog = QProgressDialog(f"Buscando versiones de {repo_type.capitalize()}...", "Cancelar", 0, len(enabled_repos), self)
        self.progress_dialog.setWindowTitle("Actualizando Versiones")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setCancelButton(None) # No permitir cancelar la busqueda

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
        
    def _add_release_to_list(self, repo_type: str, release_name: str, version: str, assets: list, published_at: str):
        """Anade un lanzamiento a la lista correspondiente (Wine o Proton)."""
        list_widget = self.list_versions_proton if repo_type == "proton" else self.list_versions_wine
        item = QListWidgetItem(release_name)
        item.setData(Qt.UserRole, assets) # Guardar los assets para la descarga
        
        tooltip = f"<b>Version:</b> {version}<br/>" \
                  f"<b>Fecha:</b> {published_at.split('T')[0]}<br/>" \
                  f"<b>Archivos:</b> {len(assets)}"
        item.setToolTip(tooltip)
        
        list_widget.addItem(item)


    def download_selected_wine_version(self):
        selected_item = self.list_versions_wine.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Seleccion Invalida", "Por favor, selecciona una version de Wine para descargar.")
            return

        assets = selected_item.data(Qt.UserRole)
        
        # Dialogo para seleccionar el asset especifico
        dialog = QDialog(self)
        dialog.setWindowTitle("Seleccionar Archivo Wine")
        layout = QVBoxLayout()
        
        label = QLabel("Selecciona el archivo especifico para descargar:")
        layout.addWidget(label)
        
        version_combo = QComboBox()
        for asset in assets:
            name = asset["name"]
            size = asset.get("size", 0) / (1024 * 1024)  # Convertir a MB
            version_combo.addItem(f"{name} ({size:.1f} MB)", asset)
        layout.addWidget(version_combo)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.setFont(STYLE_STEAM_DECK["font"]) # Aplicar fuente al dialogo
        self.config_manager.apply_theme_to_dialog(dialog) # Aplicar tema al dialogo

        if dialog.exec_() == QDialog.Accepted:
            selected_asset = version_combo.currentData()
            download_url = selected_asset["browser_download_url"]
            filename = selected_asset["name"]
            destination = self.config_manager.wine_download_dir / filename
            
            self.download_file(download_url, destination, f"Wine {selected_item.text()}")
            
    def download_file(self, url: str, destination: Path, name: str):
        self.progress_dialog = QProgressDialog(f"Descargando {name}...", "Cancelar", 0, 100, self)
        self.progress_dialog.setWindowTitle("Descargando")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(False) # Mantener abierto hasta finalizar
        
        self.download_progress_bar = QProgressBar(self.progress_dialog)
        self.download_progress_bar.setRange(0, 100)
        self.progress_dialog.setBar(self.download_progress_bar)
        
        self.download_thread = DownloadThread(url, destination, name, self.config_manager)
        self.download_thread.progress.connect(self.download_progress_bar.setValue)
        self.download_thread.finished.connect(partial(self.on_download_finished, name=name))
        self.download_thread.error.connect(self.show_download_error)
        self.progress_dialog.canceled.connect(self.download_thread.stop)
        
        self.download_thread.start()
        self.progress_dialog.exec_()
        
    def show_download_error(self, error_msg: str):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error de Descarga", error_msg)

    def on_download_finished(self, filepath: str, name: str):
        self.progress_dialog.setLabelText(f"Descomprimiendo {name}...")
        self.progress_dialog.setMaximum(0) # Modo indeterminado para la descompresion
        
        self.decompression_thread = DecompressionThread(filepath, self.config_manager, name)
        self.decompression_thread.finished.connect(partial(self.on_decompression_finished, name=name))
        self.decompression_thread.error.connect(self.show_decompression_error)
        self.decompression_thread.start()

    def show_decompression_error(self, error_msg: str):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error de Descompresion", error_msg)

    def on_decompression_finished(self, path: str, name: str):
        self.progress_dialog.close()
        QMessageBox.information(self, "Exito", f"Descarga y descompresion de {name} completadas.\nInstalado en: {path}")

    def save_new_config(self):
        try:
            config_name = self.config_name.text().strip()
            if not config_name:
                QMessageBox.warning(self, "Error", "Debes especificar un nombre para la configuracion.")
                return

            # Obtener el elemento actual para la comprobacion de edicion, manejando de forma segura la no seleccion
            current_item_name = self.list_config.currentItem().text().replace(" (Default)", "").strip() if self.list_config.currentItem() else ""

            if config_name in self.config_manager.configs.get("configs", {}) and config_name != current_item_name:
                QMessageBox.warning(self, "Nombre Duplicado", f"Ya existe una configuracion con el nombre '{config_name}'. Por favor, elige otro nombre o edita la existente.")
                return

            config_type = "wine" if self.config_type.currentText() == "Wine" else "proton"
            architecture = self.architecture_combo.currentText()
            prefix = self.prefix_path.text().strip()

            if not prefix:
                QMessageBox.warning(self, "Error", "Debes especificar un prefijo.")
                return

            config_data = {
                "type": config_type,
                "prefix": prefix,
                "arch": architecture
            }

            if config_type == "proton":
                proton_directory = self.proton_directory.text().strip()
                if not proton_directory:
                    QMessageBox.warning(self, "Error", "Debes especificar el directorio de Proton.")
                    return
                config_data["proton_dir"] = proton_directory
            else: # Wine
                wine_directory = self.wine_directory.text().strip()
                if wine_directory: # wine_directory es opcional, si esta vacio, se usara el Wine del sistema
                    config_data["wine_dir"] = wine_directory

            # Si se esta editando, eliminar la configuracion antigua antes de guardar la nueva
            if current_item_name and current_item_name != config_name:
                self.config_manager.delete_config(current_item_name)
                
            self.config_manager.configs.setdefault("configs", {})[config_name] = config_data
            self.config_manager.save_configs()
            
            QMessageBox.information(self, "Guardado", f"Configuracion '{config_name}' guardada exitosamente.")
            self.load_configs() # Recargar la lista de configuraciones
            self.config_saved.emit() # Notificar a la ventana principal
            self.tabs.setCurrentIndex(0) # Volver a la pestana de configuraciones
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando configuracion: {str(e)}")

    def setup_settings_tab(self):
        layout = QFormLayout()
        self.edit_winetricks_path = QLineEdit(self.config_manager.get_winetricks_path())
        self.btn_winetricks = QPushButton("Explorar...")
        self.btn_winetricks.setAutoDefault(False)
        self.btn_winetricks.clicked.connect(self.browse_winetricks)

        winetricks_layout = QHBoxLayout()
        winetricks_layout.addWidget(self.edit_winetricks_path)
        winetricks_layout.addWidget(self.btn_winetricks)
        layout.addRow("Ruta de Winetricks:", winetricks_layout)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro"])
        current_theme = self.config_manager.get_theme()
        self.theme_combo.setCurrentText("Oscuro" if current_theme == "dark" else "Claro")
        layout.addRow("Tema de Interfaz:", self.theme_combo)

        # Global silent install checkbox
        self.checkbox_silent_global = QCheckBox("Habilitar modo silencioso por defecto (-q)")
        self.checkbox_silent_global.setChecked(self.config_manager.get_silent_install())
        layout.addRow(self.checkbox_silent_global)
        
        # New checkbox for forcing Winetricks installation
        self.checkbox_force_winetricks = QCheckBox("Forzar instalacion de Winetricks (--force)")
        self.checkbox_force_winetricks.setChecked(self.config_manager.get_force_winetricks_install())
        layout.addRow(self.checkbox_force_winetricks)

        self.btn_save_settings = QPushButton("Guardar Ajustes")
        self.btn_save_settings.setAutoDefault(False)
        self.btn_save_settings.clicked.connect(self.save_settings)
        layout.addWidget(self.btn_save_settings)
        self.settings_tab.setLayout(layout)
        
    def save_settings(self):
        try:
            winetricks_path_ok = self.config_manager.set_winetricks_path(self.edit_winetricks_path.text().strip())
            
            theme = "dark" if self.theme_combo.currentText() == "Oscuro" else "light"
            self.config_manager.set_theme(theme)
            
            self.config_manager.set_silent_install(self.checkbox_silent_global.isChecked())
            self.config_manager.set_force_winetricks_install(self.checkbox_force_winetricks.isChecked())
            
            if winetricks_path_ok:
                QMessageBox.information(self, "Guardado", "Ajustes guardados exitosamente.\nLos cambios de tema se aplicaran despues de reiniciar la aplicacion.")
            # Si winetricks_path_ok es False, el mensaje de error ya se ha mostrado por set_winetricks_path
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando ajustes: {str(e)}")
            
    def browse_winetricks(self):
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog) # Mejor control visual
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Ejecutables (*);;Todos los Archivos (*)")
        dialog.setDirectory(str(Path.home())) # Empezar en home
        
        # Corrección: Llama al método desde self.config_manager
        self.config_manager.apply_theme_to_dialog(dialog)
        
        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                self.edit_winetricks_path.setText(selected[0])

    def load_configs(self):
        self.list_config.clear()
        configs = self.config_manager.configs.get("configs", {})
        last_used = self.config_manager.configs.get("last_used", "")
        
        # Ordenar las claves para asegurar un orden de visualizacion consistente, excepto la predeterminada
        sorted_config_names = sorted(configs.keys())
        if last_used in sorted_config_names:
            sorted_config_names.remove(last_used)
            sorted_config_names.insert(0, last_used)

        for name in sorted_config_names:
            item = QListWidgetItem(name)
            if name == last_used:
                item.setText(f"{name} (Por Defecto)")
            self.list_config.addItem(item)
            if name == last_used:
                self.list_config.setCurrentItem(item) # Seleccionar la predeterminada
                
        self.update_displayed_config_info()

    def edit_config(self, item: QListWidgetItem):
        config_name_display = item.text()
        # Eliminar "(Por Defecto)" para obtener el nombre real
        config_name = config_name_display.replace(" (Por Defecto)", "").strip()
        
        config = self.config_manager.get_config(config_name)
        if not config:
            QMessageBox.warning(self, "Error", "Configuracion no encontrada o corrupta.")
            return

        self.tabs.setCurrentIndex(1) # Ir a la pestana de nueva configuracion
        self.config_name.setText(config_name)
        
        self.config_type.setCurrentText("Proton" if config.get("type") == "proton" else "Wine")
        self.prefix_path.setText(config.get("prefix", ""))
        self.architecture_combo.setCurrentText(config.get("arch", "win64"))

        if config.get("type") == "proton":
            self.proton_directory.setText(config.get("proton_dir", ""))
            self.wine_directory.setText("")
        else:
            self.wine_directory.setText(config.get("wine_dir", ""))
            self.proton_directory.setText("")
        
        self.update_config_field_visibility() # Asegurar que los campos correctos esten visibles

    def delete_config(self):
        selected = self.list_config.currentItem()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Selecciona una configuracion para eliminar.")
            return

        config_name_display = selected.text()
        config_name = config_name_display.replace(" (Por Defecto)", "").strip()

        if config_name == "Wine-System":
            QMessageBox.warning(self, "Error", "No se puede eliminar la configuracion 'Wine-System' ya que es la predeterminada del sistema.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Eliminacion",
            f"Estas seguro de que quieres eliminar la configuracion '{config_name}'? Esto no eliminara el prefijo o los archivos de Wine/Proton asociados.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.config_manager.delete_config(config_name):
                self.load_configs()
                QMessageBox.information(self, "Exito", f"Configuracion '{config_name}' eliminada.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la configuracion.")

    def set_default_config(self):
        selected = self.list_config.currentItem()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Selecciona una configuracion para establecer como predeterminada.")
            return

        config_name = selected.text().replace(" (Por Defecto)", "").strip()
        self.config_manager.configs["last_used"] = config_name
        self.config_manager.save_configs()
        QMessageBox.information(self, "Exito", f"Configuracion '{config_name}' establecida como predeterminada.")
        self.load_configs() # Recargar para actualizar el texto "(Por Defecto)"
        self.config_saved.emit() # Notificar a la ventana principal

    def update_displayed_config_info(self):
        selected = self.list_config.currentItem()
        if not selected:
            self.lbl_config_info.setText("Selecciona una configuracion para ver los detalles.")
            return

        config_name = selected.text().replace(" (Por Defecto)", "").strip()
        config = self.config_manager.get_config(config_name)
        if not config:
            self.lbl_config_info.setText("Configuracion no encontrada o corrupta.")
            return

        try:
            env = self.config_manager.get_current_environment(config_name)
        except Exception as e:
            self.lbl_config_info.setText(f"Error cargando el entorno para '{config_name}': {e}")
            return

        version = env.get("PROTON_VERSION") if config.get("type") == "proton" else env.get("WINE_VERSION", "Desconocida")
        wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "N/A")

        info = [
            f"<b>Configuracion Actual:</b> {config_name}",
            f"<b>Tipo:</b> {'Proton' if config['type'] == 'proton' else 'Wine'}",
            f"<b>Version Detectada:</b> <span style='color: #27ae60; font-weight: bold;'>{version}</span>",
        ]

        if config['type'] == 'proton':
            info.extend([
                f"<b>Wine en Proton:</b> <span style='color: #27ae60; font-weight: bold;'>{wine_version_in_proton}</span>",
                f"<b>Directorio de Proton:</b> {config.get('proton_dir', 'No especificado')}"
            ])
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

    def update_config_field_visibility(self):
        is_proton = self.config_type.currentText() == "Proton"
        self.proton_group.setVisible(is_proton)
        self.wine_group.setVisible(not is_proton)

    def browse_prefix(self):
        path = self._get_directory_path("Seleccionar Directorio de Prefijo de Wine")
        if path:
            self.prefix_path.setText(path)

    def browse_wine(self):
        path = self._get_directory_path("Seleccionar Directorio de Instalacion de Wine (ej., bin/wine)")
        if path:
            self.wine_directory.setText(path)

    def browse_proton(self):
        path = self._get_directory_path("Seleccionar Directorio de Instalacion de Proton (ej., proton_dist/files)")
        if path:
            self.proton_directory.setText(path)

    def _get_directory_path(self, title="Seleccionar Directorio") -> str | None:
        dialog = QFileDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        dialog.setDirectory(str(Path.home())) # Directorio inicial
        
        # Corrección: Llama al método desde self.config_manager
        self.config_manager.apply_theme_to_dialog(dialog)
        
        if dialog.exec_() == QDialog.Accepted:
            return dialog.selectedFiles()[0]
        return None

    def test_configuration(self):
        config_name_test = self.config_name.text().strip()
        if not config_name_test:
            QMessageBox.warning(self, "Advertencia", "Por favor, introduce un nombre para la configuracion antes de probar.")
            return

        temp_config = {
            "type": "wine" if self.config_type.currentText() == "Wine" else "proton",
            "prefix": self.prefix_path.text().strip(),
            "arch": self.architecture_combo.currentText()
        }
        if temp_config["type"] == "proton":
            temp_config["proton_dir"] = self.proton_directory.text().strip()
        elif self.wine_directory.text().strip():
            temp_config["wine_dir"] = self.wine_directory.text().strip()
            
        # Guardar temporalmente para que get_current_environment pueda acceder
        original_configs = self.config_manager.configs.copy()
        # Crear una copia profunda de 'configs' para evitar modificar el original durante la configuracion de prueba
        temp_configs_dict = {k: v.copy() if isinstance(v, dict) else v for k, v in original_configs.get("configs", {}).items()}
        temp_configs_dict[config_name_test] = temp_config
        self.config_manager.configs["configs"] = temp_configs_dict
        self.config_manager.configs["last_used"] = config_name_test


        try:
            env = self.config_manager.get_current_environment(config_name_test)
            
            # Intentar ejecutar wine --version
            wine_executable = env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en la ruta especificada o en el PATH del sistema: {wine_executable}")

            # Ejecutar con un tiempo de espera para evitar bloqueos
            process = subprocess.run(
                [wine_executable, "--version"],
                env=env,
                capture_output=True,
                text=True,
                timeout=10, # Tiempo de espera de 10 segundos
                check=True # Lanzar CalledProcessError si el codigo de retorno no es 0
            )
            version_output = process.stdout.strip()
            QMessageBox.information(
                self,
                "Prueba Exitosa",
                f"Configuracion valida.\nVersion Detectada: {version_output}"
            )
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error de Prueba", f"Error de archivo: {str(e)}")
        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "Error de Prueba", "El comando Wine/Proton --version tardo demasiado en responder.")
        except subprocess.CalledProcessError as e:
            error_details = f"Codigo de Salida: {e.returncode}\nStdout: {e.stdout}\nStderr: {e.stderr}"
            QMessageBox.critical(self, "Error de Prueba", f"El comando Wine/Proton --version fallo.\nDetalles:\n{error_details}")
        except Exception as e:
            QMessageBox.critical(self, "Error de Prueba", f"Error inesperado durante la prueba: {str(e)}")
        finally:
            # Restaurar la configuracion original
            self.config_manager.configs = original_configs
            self.config_manager.save_configs()


class VersionSearchThread(QThread):
    progress = pyqtSignal(int)
    new_release = pyqtSignal(str, str, str, object, str) # type, name, version, assets, published_at
    error = pyqtSignal(str)

    def __init__(self, repo_type: str, repositories: list[dict]):
        super().__init__()
        self.repo_type = repo_type
        self.repositories = repositories

    def run(self):
        fetched_count = 0
        total_repos = len(self.repositories)

        for i, repo in enumerate(self.repositories):
            if not repo.get("enabled", True):
                continue
            
            url = repo["url"]
            try:
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(req, timeout=10) as response: # Anadir tiempo de espera a la solicitud
                    if response.getcode() != 200:
                        raise HTTPError(url, response.getcode(), response.reason, response.headers, None)
                    
                    releases = json.loads(response.read().decode())
                    
                    for release in releases:
                        if release.get("draft", False) or release.get("prerelease", False):
                            continue # Ignorar borradores y pre-lanzamientos
                        
                        version = release["tag_name"]
                        # Filtrar assets relevantes (tar.gz, tar.xz, zip)
                        assets = [a for a in release["assets"] if any(a["name"].endswith(ext) for ext in ['.tar.gz', '.tar.xz', '.zip'])]
                        
                        if not assets:
                            continue
                            
                        release_name = release.get("name", version)
                        published_at = release.get("published_at", "")
                        
                        self.new_release.emit(self.repo_type, release_name, version, assets, published_at)
                
            except HTTPError as e:
                self.error.emit(f"Error HTTP del repositorio '{repo['name']}': {e.code} - {e.reason}")
            except Exception as e:
                self.error.emit(f"Error obteniendo versiones de '{repo['name']}': {str(e)}")
            finally:
                fetched_count += 1
                self.progress.emit(int(fetched_count * 100 / total_repos))
