# dialogs/config_dialog.py
import os
import subprocess
import json
import re
import time
import tarfile
import zipfile
import shutil
from pathlib import Path
from urllib.request import urlopen, Request

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QCheckBox, QDialog, QDialogButtonBox,
    QMessageBox, QGroupBox, QComboBox, QLineEdit, QFileDialog,
    QTabWidget, QFormLayout, QScrollArea, QListWidgetItem, QAction,
    QMenu, QMenuBar, QTableWidget, QTableWidgetItem, QHeaderView, 
    QTreeWidget, QTreeWidgetItem, QProgressDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDir, QSize, QUrl
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QDesktopServices

from dialogs.repository_dialog import RepositoryDialog
from downloader import DownloadThread
from config_manager import ConfigManager
from styles import STEAM_DECK_STYLE

class ConfigDialog(QDialog):
    config_saved = pyqtSignal()
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Configuración de Entornos")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.load_configs()
        self.apply_steamdeck_style()

    def apply_steamdeck_style(self):
        self.setFont(STEAM_DECK_STYLE["font"])
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(STEAM_DECK_STYLE["font"])
            if isinstance(widget, QGroupBox):
                widget.setFont(STEAM_DECK_STYLE["title_font"])
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STEAM_DECK_STYLE["button_style"])

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        self.current_tab = QWidget()
        self.setup_current_config_tab()
        self.tabs.addTab(self.current_tab, "Configuraciones")

        self.new_tab = QWidget()
        self.setup_new_config_tab()
        self.tabs.addTab(self.new_tab, "Nueva Configuración")

        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Configuración General")

        self.downloads_tab = QWidget()
        self.setup_downloads_tab()
        self.tabs.addTab(self.downloads_tab, "Descargas")

        layout.addWidget(self.tabs)
        self.exit_btn = QPushButton("Salir")
        self.exit_btn.setAutoDefault(False)
        self.exit_btn.clicked.connect(self.reject)
        layout.addWidget(self.exit_btn)
        self.setLayout(layout)

    def setup_current_config_tab(self):
        layout = QVBoxLayout()
        self.config_list = QListWidget()
        self.config_list.itemDoubleClicked.connect(self.edit_config)
        self.config_list.itemSelectionChanged.connect(self.update_config_info)
        layout.addWidget(self.config_list)

        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Eliminar Configuración")
        self.delete_btn.setAutoDefault(False)
        self.delete_btn.clicked.connect(self.delete_config)
        btn_layout.addWidget(self.delete_btn)

        self.set_default_btn = QPushButton("Establecer como Predeterminada")
        self.set_default_btn.setAutoDefault(False)
        self.set_default_btn.clicked.connect(self.set_default_config)
        btn_layout.addWidget(self.set_default_btn)

        layout.addLayout(btn_layout)

        self.config_info = QLabel("Selecciona una configuración para ver detalles")
        self.config_info.setWordWrap(True)
        layout.addWidget(self.config_info)
        self.current_tab.setLayout(layout)

    def setup_new_config_tab(self):
        layout = QFormLayout()

        self.config_type = QComboBox()
        self.config_type.addItems(["Wine", "Proton"])
        self.config_type.currentTextChanged.connect(self.update_config_fields)
        layout.addRow("Tipo:", self.config_type)

        self.config_name = QLineEdit()
        layout.addRow("Nombre:", self.config_name)

        self.arch_combo = QComboBox()
        self.arch_combo.addItems(["win64", "win32"])
        layout.addRow("Arquitectura:", self.arch_combo)

        self.prefix_path = QLineEdit()
        self.prefix_btn = QPushButton("Examinar...")
        self.prefix_btn.setAutoDefault(False)
        self.prefix_btn.clicked.connect(self.browse_prefix)
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(self.prefix_path)
        prefix_layout.addWidget(self.prefix_btn)
        layout.addRow("Prefix:", prefix_layout)

        self.wine_dir = QLineEdit()
        self.wine_btn = QPushButton("Examinar...")
        self.wine_btn.setAutoDefault(False)
        self.wine_btn.clicked.connect(self.browse_wine)
        wine_layout = QHBoxLayout()
        wine_layout.addWidget(self.wine_dir)
        wine_layout.addWidget(self.wine_btn)

        self.wine_group = QGroupBox("Configuración Wine")
        wine_inner_layout = QFormLayout()
        wine_inner_layout.addRow("Directorio Wine:", wine_layout)
        self.wine_group.setLayout(wine_inner_layout)

        self.proton_dir = QLineEdit()
        self.proton_btn = QPushButton("Examinar...")
        self.proton_btn.setAutoDefault(False)
        self.proton_btn.clicked.connect(self.browse_proton)
        proton_layout = QHBoxLayout()
        proton_layout.addWidget(self.proton_dir)
        proton_layout.addWidget(self.proton_btn)

        self.proton_group = QGroupBox("Configuración Proton")
        proton_inner_layout = QFormLayout()
        proton_inner_layout.addRow("Directorio Proton:", proton_layout)
        self.proton_group.setLayout(proton_inner_layout)

        layout.addRow(self.wine_group)
        layout.addRow(self.proton_group)

        # Botones en la misma fila
        buttons_layout = QHBoxLayout()
        self.test_btn = QPushButton("Probar Configuración")
        self.test_btn.setAutoDefault(False)
        self.test_btn.clicked.connect(self.test_configuration)
        buttons_layout.addWidget(self.test_btn)
        
        self.save_config_btn = QPushButton("Guardar Configuración")
        self.save_config_btn.setAutoDefault(False)
        self.save_config_btn.clicked.connect(self.save_new_config)
        buttons_layout.addWidget(self.save_config_btn)
        layout.addRow(buttons_layout)

        self.update_config_fields()
        self.new_tab.setLayout(layout)

    def setup_downloads_tab(self):
        layout = QVBoxLayout()
        
        # Pestañas para Wine y Proton
        self.download_tabs = QTabWidget()
        
        # Tab de Proton
        self.proton_tab = QWidget()
        self.setup_proton_download_tab()
        self.download_tabs.addTab(self.proton_tab, "Proton")
        
        # Tab de Wine
        self.wine_tab = QWidget()
        self.setup_wine_download_tab()
        self.download_tabs.addTab(self.wine_tab, "Wine")
        
        layout.addWidget(self.download_tabs)
        self.downloads_tab.setLayout(layout)

    def download_selected_proton_version(self):
        selected = self.proton_versions_list.currentRow()
        if selected >= 0:
            item = self.proton_versions_list.item(selected)
            assets = item.data(Qt.UserRole)
            
            # Mostrar diálogo para seleccionar el asset específico
            dialog = QDialog(self)
            dialog.setWindowTitle("Seleccionar versión de Proton")
            layout = QVBoxLayout()
            
            label = QLabel("Selecciona la versión específica a descargar:")
            layout.addWidget(label)
            
            self.version_combo = QComboBox()
            for asset in assets:
                name = asset["name"]
                size = asset.get("size", 0) / (1024 * 1024)  # Convertir a MB
                self.version_combo.addItem(f"{name} ({size:.1f} MB)", asset)
            layout.addWidget(self.version_combo)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                selected_asset = self.version_combo.currentData()
                download_url = selected_asset["browser_download_url"]
                filename = selected_asset["name"]
                destination = self.config_manager.proton_download_dir / filename
                
                self.download_file(download_url, destination, f"Proton {filename}")

    def setup_proton_download_tab(self):
        layout = QVBoxLayout()
        
        # Lista de repositorios
        self.proton_repo_group = QGroupBox("Repositorios Proton")
        repo_layout = QVBoxLayout()
        
        self.proton_repo_list = QListWidget()
        self.load_proton_repositories()
        repo_layout.addWidget(self.proton_repo_list)
        
        # Botones para gestionar repositorios
        repo_btn_layout = QHBoxLayout()
        
        self.add_proton_repo_btn = QPushButton("Añadir Repositorio")
        self.add_proton_repo_btn.setAutoDefault(False)
        self.add_proton_repo_btn.clicked.connect(self.add_proton_repository)
        repo_btn_layout.addWidget(self.add_proton_repo_btn)
        
        self.remove_proton_repo_btn = QPushButton("Eliminar Repositorio")
        self.remove_proton_repo_btn.setAutoDefault(False)
        self.remove_proton_repo_btn.clicked.connect(self.remove_proton_repository)
        repo_btn_layout.addWidget(self.remove_proton_repo_btn)
        
        self.toggle_proton_repo_btn = QPushButton("Activar/Desactivar")
        self.toggle_proton_repo_btn.setAutoDefault(False)
        self.toggle_proton_repo_btn.clicked.connect(self.toggle_proton_repository)
        repo_btn_layout.addWidget(self.toggle_proton_repo_btn)
        
        repo_layout.addLayout(repo_btn_layout)
        self.proton_repo_group.setLayout(repo_layout)
        layout.addWidget(self.proton_repo_group)
        
        # Lista de versiones disponibles
        self.proton_versions_group = QGroupBox("Versiones Disponibles")
        versions_layout = QVBoxLayout()
        
        self.proton_versions_list = QListWidget()
        versions_layout.addWidget(self.proton_versions_list)
        
        # Botones en la misma línea
        buttons_layout = QHBoxLayout()
        self.refresh_proton_btn = QPushButton("Actualizar Lista")
        self.refresh_proton_btn.setAutoDefault(False)
        self.refresh_proton_btn.clicked.connect(self.refresh_proton_versions)
        buttons_layout.addWidget(self.refresh_proton_btn)
        
        self.download_proton_btn = QPushButton("Descargar Versión Seleccionada")
        self.download_proton_btn.setAutoDefault(False)
        self.download_proton_btn.clicked.connect(self.download_selected_proton_version)
        buttons_layout.addWidget(self.download_proton_btn)
        versions_layout.addLayout(buttons_layout)
        
        self.proton_versions_group.setLayout(versions_layout)
        layout.addWidget(self.proton_versions_group)
        
        self.proton_tab.setLayout(layout)
    
    def setup_wine_download_tab(self):
        layout = QVBoxLayout()
        
        # Lista de repositorios
        self.wine_repo_group = QGroupBox("Repositorios Wine")
        repo_layout = QVBoxLayout()
        
        self.wine_repo_list = QListWidget()
        self.load_wine_repositories()
        repo_layout.addWidget(self.wine_repo_list)
        
        # Botones para gestionar repositorios
        repo_btn_layout = QHBoxLayout()
        
        self.add_wine_repo_btn = QPushButton("Añadir Repositorio")
        self.add_wine_repo_btn.setAutoDefault(False)
        self.add_wine_repo_btn.clicked.connect(self.add_wine_repository)
        repo_btn_layout.addWidget(self.add_wine_repo_btn)
        
        self.remove_wine_repo_btn = QPushButton("Eliminar Repositorio")
        self.remove_wine_repo_btn.setAutoDefault(False)
        self.remove_wine_repo_btn.clicked.connect(self.remove_wine_repository)
        repo_btn_layout.addWidget(self.remove_wine_repo_btn)
        
        self.toggle_wine_repo_btn = QPushButton("Activar/Desactivar")
        self.toggle_wine_repo_btn.setAutoDefault(False)
        self.toggle_wine_repo_btn.clicked.connect(self.toggle_wine_repository)
        repo_btn_layout.addWidget(self.toggle_wine_repo_btn)
        
        repo_layout.addLayout(repo_btn_layout)
        self.wine_repo_group.setLayout(repo_layout)
        layout.addWidget(self.wine_repo_group)
        
        # Lista de versiones disponibles
        self.wine_versions_group = QGroupBox("Versiones Disponibles")
        versions_layout = QVBoxLayout()
        
        self.wine_versions_list = QListWidget()
        versions_layout.addWidget(self.wine_versions_list)
        
        # Botones en la misma línea
        buttons_layout = QHBoxLayout()
        self.refresh_wine_btn = QPushButton("Actualizar Lista")
        self.refresh_wine_btn.setAutoDefault(False)
        self.refresh_wine_btn.clicked.connect(self.refresh_wine_versions)
        buttons_layout.addWidget(self.refresh_wine_btn)
        
        self.download_wine_btn = QPushButton("Descargar Versión Seleccionada")
        self.download_wine_btn.setAutoDefault(False)
        self.download_wine_btn.clicked.connect(self.download_wine_version)
        buttons_layout.addWidget(self.download_wine_btn)
        versions_layout.addLayout(buttons_layout)
        
        self.wine_versions_group.setLayout(versions_layout)
        layout.addWidget(self.wine_versions_group)
        
        self.wine_tab.setLayout(layout)
    
    def load_proton_repositories(self):
        self.proton_repo_list.clear()
        repos = self.config_manager.get_repositories("proton")
        for repo in repos:
            item = QListWidgetItem(repo["name"])
            item.setData(Qt.UserRole, repo["url"])
            item.setCheckState(Qt.Checked if repo.get("enabled", True) else Qt.Unchecked)
            self.proton_repo_list.addItem(item)
    
    def load_wine_repositories(self):
        self.wine_repo_list.clear()
        repos = self.config_manager.get_repositories("wine")
        for repo in repos:
            item = QListWidgetItem(repo["name"])
            item.setData(Qt.UserRole, repo["url"])
            item.setCheckState(Qt.Checked if repo.get("enabled", True) else Qt.Unchecked)
            self.wine_repo_list.addItem(item)
    
    def add_proton_repository(self):
        dialog = RepositoryDialog("Proton", self)
        if dialog.exec_() == QDialog.Accepted:
            name, url = dialog.get_repository_info()
            self.config_manager.add_repository("proton", name, url)
            self.load_proton_repositories()
    
    def add_wine_repository(self):
        dialog = RepositoryDialog("Wine", self)
        if dialog.exec_() == QDialog.Accepted:
            name, url = dialog.get_repository_info()
            self.config_manager.add_repository("wine", name, url)
            self.load_wine_repositories()
    
    def remove_proton_repository(self):
        selected = self.proton_repo_list.currentRow()
        if selected >= 0:
            self.config_manager.remove_repository("proton", selected)
            self.load_proton_repositories()
    
    def remove_wine_repository(self):
        selected = self.wine_repo_list.currentRow()
        if selected >= 0:
            self.config_manager.remove_repository("wine", selected)
            self.load_wine_repositories()
    
    def toggle_proton_repository(self):
        selected = self.proton_repo_list.currentRow()
        if selected >= 0:
            item = self.proton_repo_list.item(selected)
            enabled = item.checkState() == Qt.Checked
            self.config_manager.toggle_repository("proton", selected, not enabled)
            item.setCheckState(Qt.Unchecked if enabled else Qt.Checked)
    
    def toggle_wine_repository(self):
        selected = self.wine_repo_list.currentRow()
        if selected >= 0:
            item = self.wine_repo_list.item(selected)
            enabled = item.checkState() == Qt.Checked
            self.config_manager.toggle_repository("wine", selected, not enabled)
            item.setCheckState(Qt.Unchecked if enabled else Qt.Checked)
    
    def refresh_proton_versions(self):
        self.proton_versions_list.clear()
        
        for i in range(self.proton_repo_list.count()):
            item = self.proton_repo_list.item(i)
            if item.checkState() == Qt.Checked:
                url = item.data(Qt.UserRole)
                try:
                    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urlopen(req) as response:
                        releases = json.loads(response.read().decode())
                        
                        for release in releases:
                            if release.get("draft", False):
                                continue
                                
                            version = release["tag_name"]
                            assets = [a for a in release["assets"] 
                                     if any(a["name"].endswith(ext) 
                                     for ext in ['.tar.gz', '.tar.xz', '.zip'])]
                            
                            if not assets:
                                continue
                            
                            # Crear item con el título de la release
                            release_name = release.get("name", version)
                            item = QListWidgetItem(release_name)
                            item.setData(Qt.UserRole, assets)
                            
                            # Añadir tooltip con información adicional
                            release_date = release.get("published_at", "").split('T')[0]
                            item.setToolTip(
                                f"<b>Versión:</b> {version}<br/>"
                                f"<b>Fecha:</b> {release_date}<br/>"
                                f"<b>Assets:</b> {len(assets)}"
                            )
                            
                            self.proton_versions_list.addItem(item)
                
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"No se pudo obtener información del repositorio:\n{str(e)}")

    def refresh_wine_versions(self):
        self.wine_versions_list.clear()
        
        for i in range(self.wine_repo_list.count()):
            item = self.wine_repo_list.item(i)
            if item.checkState() == Qt.Checked:
                url = item.data(Qt.UserRole)
                try:
                    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urlopen(req) as response:
                        releases = json.loads(response.read().decode())
                        
                        for release in releases:
                            if release.get("draft", False):
                                continue
                                
                            version = release["tag_name"]
                            assets = [a for a in release["assets"] 
                                     if any(a["name"].endswith(ext) 
                                           for ext in ['.tar.xz', '.tar.gz', '.zip'])]
                            
                            if not assets:
                                continue
                            
                            # Crear item con el título de la release
                            release_name = release.get("name", version)
                            item = QListWidgetItem(release_name)
                            item.setData(Qt.UserRole, assets)
                            
                            # Añadir tooltip con información adicional
                            release_date = release.get("published_at", "").split('T')[0]
                            item.setToolTip(
                                f"<b>Versión:</b> {version}<br/>"
                                f"<b>Fecha:</b> {release_date}<br/>"
                                f"<b>Assets:</b> {len(assets)}"
                            )
                            
                            self.wine_versions_list.addItem(item)
                
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"No se pudo obtener información del repositorio:\n{str(e)}")
    
    def download_wine_version(self):
        selected = self.wine_versions_list.currentRow()
        if selected >= 0:
            item = self.wine_versions_list.item(selected)
            assets = item.data(Qt.UserRole)
            
            # Mostrar diálogo para seleccionar el tipo de build
            dialog = QDialog(self)
            dialog.setWindowTitle("Seleccionar versión de Wine")
            layout = QVBoxLayout()
            
            label = QLabel("Selecciona la versión específica a descargar:")
            layout.addWidget(label)
            
            self.version_combo = QComboBox()
            for asset in assets:
                name = asset["name"]
                size = asset.get("size", 0) / (1024 * 1024)  # Convertir a MB
                self.version_combo.addItem(f"{name} ({size:.1f} MB)", asset)
            layout.addWidget(self.version_combo)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                selected_asset = self.version_combo.currentData()
                download_url = selected_asset["browser_download_url"]
                filename = selected_asset["name"]
                destination = self.config_manager.wine_download_dir / filename
                
                self.download_file(download_url, destination, f"Wine {filename}")
    
    def download_file(self, url, destination, name):
        self.progress_dialog = QProgressDialog(f"Descargando {name}...", "Cancelar", 0, 100, self)
        self.progress_dialog.setWindowTitle("Descargando")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        
        # Barra de progreso para la descarga
        self.download_progress = QProgressBar()
        self.download_progress.setRange(0, 100)
        self.progress_dialog.setBar(self.download_progress)
        
        self.download_thread = DownloadThread(url, destination, self.config_manager)
        self.download_thread.progress.connect(self.download_progress.setValue)
        self.download_thread.finished.connect(lambda: self.on_download_finished(destination, name))
        self.download_thread.error.connect(self.show_download_error)
        self.progress_dialog.canceled.connect(self.download_thread.stop)
        
        self.download_thread.start()
        self.progress_dialog.exec_()
    
    def show_download_error(self, error_msg):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error de descarga", error_msg)

    def on_download_finished(self, filepath, name):
        self.progress_dialog.setLabelText(f"Descomprimiendo {name}...")
        self.progress_dialog.setMaximum(0)  # Modo indeterminado durante descompresión
        
        try:
            # Llamar a la lógica de descompresión (sin eliminar archivos descomprimidos)
            if self.config_manager.decompress_archive(filepath):
                # Opcional: Eliminar SOLO el archivo comprimido después de descomprimir exitosamente
                # Si quieres mantener incluso el archivo comprimido, comenta o elimina este bloque
                try:
                    Path(filepath).unlink()
                    print(f"Archivo comprimido eliminado: {filepath}")
                except Exception as e:
                    print(f"No se pudo eliminar el archivo comprimido {filepath}: {e}")
                    # No es crítico si falla, seguimos adelante
                
                QMessageBox.information(self, "Éxito", f"Descarga y descompresión completadas:\n{name}")
            else:
                QMessageBox.critical(self, "Error", f"Error al descomprimir {name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Excepción durante descompresión:\n{str(e)}")
        finally:
            self.progress_dialog.close()

    def show_decompress_error(self, error_msg):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Error de descompresión", error_msg)
        # Intentar eliminar el archivo descargado si hubo error
        try:
            Path(self.archive_path).unlink()
        except Exception:
            pass

    def on_decompress_finished(self, filepath, name):
        self.progress_dialog.close()
        QMessageBox.information(self, "Éxito", f"Descarga y descompresión completadas:\n{name}")
        # Eliminar el archivo comprimido después de descomprimir
        try:
            Path(filepath).unlink()
        except Exception as e:
            print(f"No se pudo eliminar el archivo {filepath}: {e}")

    def on_decompress_error(self, error):
        self.progress_dialog.close()
        QMessageBox.warning(self, "Error", f"Error al descomprimir:\n{error}")

    def save_new_config(self):
        try:
            config_name = self.config_name.text().strip()
            if not config_name:
                QMessageBox.warning(self, "Error", "Debes especificar un nombre para la configuración")
                return

            config_type = "wine" if self.config_type.currentText() == "Wine" else "proton"
            arch = self.arch_combo.currentText()
            prefix = self.prefix_path.text().strip()

            if not prefix:
                QMessageBox.warning(self, "Error", "Debes especificar un prefix")
                return

            config = {
                "type": config_type,
                "prefix": prefix,
                "arch": arch
            }

            if config_type == "proton":
                proton_dir = self.proton_dir.text().strip()
                if not proton_dir:
                    QMessageBox.warning(self, "Error", "Debes especificar el directorio de Proton")
                    return
                config["proton_dir"] = proton_dir
            else:
                wine_dir = self.wine_dir.text().strip()
                if wine_dir:
                    config["wine_dir"] = wine_dir

            self.config_manager.configs["configs"][config_name] = config
            self.config_manager.save_configs()
            QMessageBox.information(self, "Guardado", f"Configuración '{config_name}' guardada correctamente")
            
            self.load_configs()
            self.config_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {str(e)}")

    def setup_settings_tab(self):
        layout = QFormLayout()
        self.winetricks_path = QLineEdit(self.config_manager.get_winetricks_path())
        self.winetricks_btn = QPushButton("Examinar...")
        self.winetricks_btn.setAutoDefault(False)
        self.winetricks_btn.clicked.connect(self.browse_winetricks)

        winetricks_layout = QHBoxLayout()
        winetricks_layout.addWidget(self.winetricks_path)
        winetricks_layout.addWidget(self.winetricks_btn)
        layout.addRow("Ruta de Winetricks:", winetricks_layout)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro"])
        current_theme = self.config_manager.get_theme()
        self.theme_combo.setCurrentText("Oscuro" if current_theme == "dark" else "Claro")
        layout.addRow("Tema de la interfaz:", self.theme_combo)

        # Opción para modo silencioso por defecto
        self.silent_checkbox = QCheckBox("Instalación silenciosa por defecto (winetricks)")
        self.silent_checkbox.setChecked(self.config_manager.get_silent_install())
        layout.addRow(self.silent_checkbox)

        self.save_settings_btn = QPushButton("Guardar Ajustes")
        self.save_settings_btn.setAutoDefault(False)
        self.save_settings_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_settings_btn)
        self.settings_tab.setLayout(layout)
        
    def save_settings(self):
        try:
            winetricks_path = self.winetricks_path.text().strip()
            if winetricks_path:
                self.config_manager.set_winetricks_path(winetricks_path)
            
            theme = "dark" if self.theme_combo.currentText() == "Oscuro" else "light"
            self.config_manager.set_theme(theme)
            
            self.config_manager.set_silent_install(self.silent_checkbox.isChecked())
            
            QMessageBox.information(self, "Guardado", "Ajustes guardados correctamente.\nLos cambios de tema se aplicarán al reiniciar la aplicación.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar ajustes: {str(e)}")
            
    def browse_winetricks(self):
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog) 
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Todos los archivos (*)")
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        
        self.apply_theme_to_dialog(dialog)
        
        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                self.winetricks_path.setText(selected[0])
                self.config_manager.set_winetricks_path(selected[0])

    def load_configs(self):
        self.config_list.clear()
        for name in self.config_manager.configs["configs"].keys():
            self.config_list.addItem(name)

    def edit_config(self, item):
        config_name = item.text()
        config = self.config_manager.get_config(config_name)
        if not config:
            return

        self.tabs.setCurrentIndex(1)
        self.config_name.setText(config_name)

        if config["type"] == "proton":
            self.config_type.setCurrentText("Proton")
            self.proton_dir.setText(config.get("proton_dir", ""))
            self.wine_dir.setText("")
        else:
            self.config_type.setCurrentText("Wine")
            self.wine_dir.setText(config.get("wine_dir", ""))
            self.proton_dir.setText("")

        self.prefix_path.setText(config.get("prefix", ""))
        self.arch_combo.setCurrentText(config.get("arch", "win64"))

    def delete_config(self):
        selected = self.config_list.currentItem()
        if not selected:
            return

        config_name = selected.text()
        if config_name in ["Wine-System"]:
            QMessageBox.warning(self, "Error", "No se puede eliminar la configuración por defecto")
            return

        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Estás seguro de que deseas eliminar la configuración '{config_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QDialog.Yes:
            if self.config_manager.remove_config(config_name):
                self.load_configs()
                QMessageBox.information(self, "Éxito", f"Configuración '{config_name}' eliminada")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la configuración")

    def set_default_config(self):
        selected = self.config_list.currentItem()
        if not selected:
            return

        config_name = selected.text()
        self.config_manager.configs["last_used"] = config_name
        self.config_manager.save_configs()
        QMessageBox.information(self, "Éxito", f"Configuración '{config_name}' establecida como predeterminada")
        self.update_config_info()

    def update_config_info(self):
        selected = self.config_list.currentItem()
        if not selected:
            self.config_info.setText("Selecciona una configuración para ver detalles")
            return

        config_name = selected.text()
        config = self.config_manager.get_config(config_name)
        if not config:
            self.config_info.setText("Configuración no encontrada")
            return

        env = self.config_manager.get_current_env(config_name)
        version = env.get("PROTON_VERSION") if config["type"] == "proton" else env.get("WINE_VERSION", "Desconocida")
        wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "Desconocida")

        info = [
            f"<b>Nombre:</b> {config_name}",
            f"<b>Tipo:</b> {'Proton' if config['type'] == 'proton' else 'Wine'}",
            f"<b>Versión:</b> <span style='color: #27ae60; font-weight: bold;'>{version}</span>",
        ]

        if config['type'] == 'proton':
            info.extend([
                f"<b>Wine en Proton:</b> <span style='color: #27ae60; font-weight: bold;'>{wine_version_in_proton}</span>",
                f"<b>Directorio Proton:</b> {config.get('proton_dir', 'No especificado')}"
            ])
        else:
            wine_dir = config.get('wine_dir', 'Sistema')
            info.extend([
                f"<b>Directorio Wine:</b> {wine_dir}"
            ])

        info.extend([
            f"<b>Arquitectura:</b> {config.get('arch', 'win64')}",
            f"<b>Prefix:</b> <span style='color: #FFB347; font-weight: bold;'>{config.get('prefix', 'No especificado')}"
        ])

        self.config_info.setText("<br>".join(info))

    def update_config_fields(self):
        is_proton = self.config_type.currentText() == "Proton"
        self.proton_group.setVisible(is_proton)
        self.wine_group.setVisible(not is_proton)

    def browse_prefix(self):
        path = self.get_directory_path()
        if path:
            self.prefix_path.setText(path)

    def browse_wine(self):
        path = self.get_directory_path()
        if path:
            self.wine_dir.setText(path)

    def browse_proton(self):
        path = self.get_directory_path()
        if path:
            self.proton_dir.setText(path)

    def get_directory_path(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        
        self.apply_theme_to_dialog(dialog)
        
        if dialog.exec_() == QDialog.Accepted:
            return dialog.selectedFiles()[0]
        return None

    def apply_theme_to_dialog(self, dialog):
        theme = self.config_manager.get_theme()
        if theme == "dark":
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, STEAM_DECK_STYLE["dark_palette"]["window"])
            dark_palette.setColor(QPalette.WindowText, STEAM_DECK_STYLE["dark_palette"]["window_text"])
            dark_palette.setColor(QPalette.Base, STEAM_DECK_STYLE["dark_palette"]["base"])
            dark_palette.setColor(QPalette.Text, STEAM_DECK_STYLE["dark_palette"]["text"])
            dark_palette.setColor(QPalette.Button, STEAM_DECK_STYLE["dark_palette"]["button"])
            dark_palette.setColor(QPalette.ButtonText, STEAM_DECK_STYLE["dark_palette"]["button_text"])
            dark_palette.setColor(QPalette.Highlight, STEAM_DECK_STYLE["dark_palette"]["highlight"])
            dark_palette.setColor(QPalette.HighlightedText, STEAM_DECK_STYLE["dark_palette"]["highlight_text"])
            dialog.setPalette(dark_palette)

    def test_configuration(self):
        try:
            env = self.prepare_test_env()

            if self.config_type.currentText() == "Proton":
                proton_dir = Path(self.proton_dir.text().strip())
                wine_bin = str(proton_dir / "files/bin/wine")
                cmd = [wine_bin, "--version"]
            else:
                wine_dir = self.wine_dir.text().strip()
                if wine_dir:
                    wine_bin = str(Path(wine_dir) / "bin/wine")
                else:
                    wine_bin = "wine"
                cmd = [wine_bin, "--version"]

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                QMessageBox.information(
                    self,
                    "Prueba Exitosa",
                    f"Configuración válida\nVersión detectada: {version}"
                )
            else:
                raise subprocess.CalledProcessError(
                    result.returncode,
                    cmd,
                    result.stdout,
                    result.stderr
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error en Prueba",
                f"No se pudo ejecutar Wine/Proton:\n{str(e)}"
            )

    def prepare_test_env(self):
        env = os.environ.copy()
        env["WINEPREFIX"] = self.prefix_path.text().strip()
        env["WINEARCH"] = self.arch_combo.currentText()

        if self.config_type.currentText() == "Proton":
            proton_dir = Path(self.proton_dir.text().strip())
            env.update({
                "PROTON_DIR": str(proton_dir),
                "WINE": str(proton_dir / "files/bin/wine"),
                "WINESERVER": str(proton_dir / "files/bin/wineserver"),
                "PATH": f"{proton_dir / 'files/bin'}:{os.environ.get('PATH', '')}"
            })
        else:
            wine_dir = self.wine_dir.text().strip()
            if wine_dir:
                wine_dir = Path(wine_dir)
                env.update({
                    "WINE": str(wine_dir / "bin/wine"),
                    "WINESERVER": str(wine_dir / "bin/wineserver"),
                    "PATH": f"{wine_dir / 'bin'}:{os.environ.get('PATH', '')}"
                })
            else:
                env.update({
                    "WINE": "wine",
                    "WINESERVER": "wineserver"
                })

        return env