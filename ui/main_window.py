import sys
import os
import subprocess
import json
import re
import time
import tempfile
import ssl
import tarfile
import zipfile
import shutil
from pathlib import Path
from functools import partial 

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

from styles import STYLE_STEAM_DECK
from config_manager import ConfigManager
from installer_thread import InstallerThread # Corrected import path
# Import dialogs from their new locations
from dialogs.config_dialog import ConfigDialog 
from dialogs.custom_program_dialog import CustomProgramDialog
from dialogs.manage_programs_dialog import ManageProgramsDialog
from dialogs.select_groups_dialog import SelectGroupsDialog


class InstallerApp(QWidget):
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.installer_thread = None
        
        self.items_for_installation: list[dict] = []
        
        self.silent_mode = self.config_manager.get_silent_install()
        self.force_mode = self.config_manager.get_force_winetricks_install()

        self.apply_theme_at_startup()
        self.setup_ui()
        self.apply_steamdeck_style()
        self.setMinimumSize(1000, 700)

    def apply_theme_at_startup(self):
        theme = self.config_manager.get_theme()
        palette = QPalette()
        
        if theme == "dark":
            palette.setColor(QPalette.Window, STYLE_STEAM_DECK["dark_palette"]["window"])
            palette.setColor(QPalette.WindowText, STYLE_STEAM_DECK["dark_palette"]["window_text"])
            palette.setColor(QPalette.Base, STYLE_STEAM_DECK["dark_palette"]["base"])
            palette.setColor(QPalette.Text, STYLE_STEAM_DECK["dark_palette"]["text"])
            palette.setColor(QPalette.Button, STYLE_STEAM_DECK["dark_palette"]["button"])
            palette.setColor(QPalette.ButtonText, STYLE_STEAM_DECK["dark_palette"]["button_text"])
            palette.setColor(QPalette.Highlight, STYLE_STEAM_DECK["dark_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, STYLE_STEAM_DECK["dark_palette"]["highlight_text"])
        else:
            palette = QApplication.style().standardPalette()
            
        QApplication.setPalette(palette)

    def apply_steamdeck_style(self):
        self.setFont(STYLE_STEAM_DECK["font"])
        theme = self.config_manager.get_theme() 
        
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme == "dark" else STYLE_STEAM_DECK["button_style"])
            elif isinstance(widget, QGroupBox):
                widget.setFont(STYLE_STEAM_DECK["title_font"])
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_groupbox_style"] if theme == "dark" else STYLE_STEAM_DECK["groupbox_style"])
            elif isinstance(widget, QLabel):
                widget.setFont(STYLE_STEAM_DECK["font"])
        
        self.items_table.setStyleSheet(STYLE_STEAM_DECK["dark_table_style"] if theme == "dark" else STYLE_STEAM_DECK["table_style"])

    def setup_ui(self):
        self.setWindowTitle("WineProton Manager")
        self.resize(self.config_manager.get_window_size())
        self.setWindowIcon(QIcon.fromTheme("wine"))

        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QHBoxLayout(content)
        
        content_layout.addWidget(self.create_left_panel(), 1)
        content_layout.addWidget(self.create_right_panel(), 2)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        config_group = QGroupBox("Configuracion del Entorno Actual")
        config_layout = QVBoxLayout()
        self.lbl_config = QLabel()
        self.lbl_config.setWordWrap(True)
        self.update_config_info()
        
        self.btn_manage_environments = QPushButton("Gestionar Entornos...")
        self.btn_manage_environments.setAutoDefault(False)
        self.btn_manage_environments.clicked.connect(self.configure_environments)
        config_layout.addWidget(self.lbl_config)
        config_layout.addWidget(self.btn_manage_environments)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        actions_group = QGroupBox("Acciones de Instalacion")
        actions_layout = QVBoxLayout()
        
        components_group = QGroupBox("Componentes de Winetricks")
        components_layout = QVBoxLayout()
        self.btn_select_components = QPushButton("Seleccionar Componentes de Winetricks")
        self.btn_select_components.setAutoDefault(False)
        self.btn_select_components.clicked.connect(self.select_components)
        components_layout.addWidget(self.btn_select_components)
        components_group.setLayout(components_layout)
        actions_layout.addWidget(components_group)
        
        custom_group = QGroupBox("Programas Personalizados")
        custom_layout = QVBoxLayout()
        self.btn_add_custom = QPushButton("Anadir Programa/Script")
        self.btn_add_custom.setAutoDefault(False)
        self.btn_add_custom.clicked.connect(self.add_custom_program)
        custom_layout.addWidget(self.btn_add_custom)
        
        self.btn_manage_custom = QPushButton("Cargar/Eliminar Programas Guardados")
        self.btn_manage_custom.setAutoDefault(False)
        self.btn_manage_custom.clicked.connect(self.manage_custom_programs)
        custom_layout.addWidget(self.btn_manage_custom)
        custom_group.setLayout(custom_layout)
        actions_layout.addWidget(custom_group)
        
        options_group = QGroupBox("Opciones de Instalacion")
        options_layout = QVBoxLayout()
        self.checkbox_silent_session = QCheckBox("Habilitar modo silencioso para esta instalacion Winetricks (-q)")
        self.checkbox_silent_session.setChecked(self.silent_mode) 
        self.checkbox_silent_session.stateChanged.connect(self.update_silent_mode_session)
        options_layout.addWidget(self.checkbox_silent_session)
        
        self.checkbox_force_winetricks_session = QCheckBox("Forzar instalacion de Winetricks para esta instalacion (--force)")
        self.checkbox_force_winetricks_session.setChecked(self.force_mode) 
        self.checkbox_force_winetricks_session.stateChanged.connect(self.update_force_mode_session)
        options_layout.addWidget(self.checkbox_force_winetricks_session)
        
        options_group.setLayout(options_layout)
        actions_layout.addWidget(options_group)
        
        self.btn_install = QPushButton("Iniciar Instalacion")
        self.btn_install.setAutoDefault(False)
        self.btn_install.clicked.connect(self.start_installation)
        self.btn_install.setEnabled(False) 
        
        self.btn_cancel = QPushButton("Cancelar Instalacion")
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.clicked.connect(self.cancel_installation)
        self.btn_cancel.setEnabled(False) 
        
        actions_layout.addWidget(self.btn_install)
        actions_layout.addWidget(self.btn_cancel)
        
        tools_group = QGroupBox("Herramientas del Prefijo")
        tools_layout = QHBoxLayout()
        
        left_column = QVBoxLayout()
        self.btn_shell = QPushButton("Terminal")
        self.btn_shell.setAutoDefault(False)
        self.btn_shell.clicked.connect(self.open_shell)
        left_column.addWidget(self.btn_shell)
        
        self.btn_prefix_folder = QPushButton("Carpeta del Prefijo")
        self.btn_prefix_folder.setAutoDefault(False)
        self.btn_prefix_folder.clicked.connect(self.open_prefix_folder)
        left_column.addWidget(self.btn_prefix_folder)

        right_column = QVBoxLayout()
        self.btn_winetricks_gui = QPushButton("Winetricks GUI")
        self.btn_winetricks_gui.setAutoDefault(False)
        self.btn_winetricks_gui.clicked.connect(self.open_winetricks)
        right_column.addWidget(self.btn_winetricks_gui)
        
        self.btn_winecfg = QPushButton("Winecfg")
        self.btn_winecfg.setAutoDefault(False)
        self.btn_winecfg.clicked.connect(self.open_winecfg)
        right_column.addWidget(self.btn_winecfg)
        
        self.btn_explorer = QPushButton("Explorador del Prefijo")
        self.btn_explorer.setAutoDefault(False)
        self.btn_explorer.clicked.connect(self.open_explorer)
        right_column.addWidget(self.btn_explorer)

        tools_layout.addLayout(left_column)
        tools_layout.addLayout(right_column)
        tools_group.setLayout(tools_layout)
        actions_layout.addWidget(tools_group)

        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        return panel

    def create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.lbl_status = QLabel("Lista de elementos a instalar:")
        layout.addWidget(self.lbl_status)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Seleccionar", "Nombre", "Tipo", "Estado"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) 
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) 
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) 
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) 
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setSelectionMode(QTableWidget.SingleSelection) 
        self.items_table.itemChanged.connect(self.on_table_item_changed)
        layout.addWidget(self.items_table)
        
        btn_layout = QHBoxLayout()
        buttons = [
            ("Limpiar Lista", self.clear_list),
            ("Eliminar Seleccion", self.delete_selected_from_table),
            ("Mover Arriba", self.move_item_up),
            ("Mover Abajo", self.move_item_down)
        ]
        
        for text, handler in buttons:
            btn = QPushButton(text)
            btn.setAutoDefault(False)
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)
            
        layout.addLayout(btn_layout)
        return panel

    def on_table_item_changed(self, item: QTableWidgetItem):
        """Maneja los cambios en las casillas de verificacion de la tabla."""
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError: 
            pass

        if item.column() == 0: 
            row = item.row()
            status_item = self.items_table.item(row, 3)

            if status_item:
                # Only change status if it's currently "Pendiente" or "Omitido"
                # This prevents overwriting "Finalizado" or "Error" after installation.
                current_status_text = status_item.text()
                if current_status_text in ["Pendiente", "Omitido"]:
                    new_status = "Pendiente" if item.checkState() == Qt.Checked else "Omitido"
                    status_item.setText(new_status)
                    
                    if new_status == "Omitido":
                        status_item.setForeground(QColor("darkorange")) 
                    else:
                        theme = self.config_manager.get_theme()
                        status_item.setForeground(QColor(STYLE_STEAM_DECK["dark_palette"]["text"]) if theme == "dark" else QColor(STYLE_STEAM_DECK["light_palette"]["text"]))
            else:
                print(f"DEBUG: El elemento de estado es None para la fila {row}, columna 3 cuando la casilla de verificacion cambio. Saltando setText.")

        self.items_table.itemChanged.connect(self.on_table_item_changed)
        self.update_installation_button_state()

    def update_silent_mode_session(self, state: int):
        self.silent_mode = state == Qt.Checked

    def update_force_mode_session(self, state: int):
        self.force_mode = state == Qt.Checked

    def closeEvent(self, event):
        """Guarda el tamano de la ventana al cerrar."""
        self.config_manager.save_window_size(self.size())
        super().closeEvent(event)

    def configure_environments(self):
        """Abre el dialogo para configurar entornos de Wine/Proton."""
        dialog = ConfigDialog(self.config_manager, self)
        dialog.config_saved.connect(self.update_config_info)
        dialog.exec_()
        self.update_config_info() 

    def update_config_info(self):
        """Actualiza la informacion del entorno actual en la GUI."""
        current_config_name = self.config_manager.configs.get("last_used", "Wine-System")
        config = self.config_manager.get_config(current_config_name)

        if not config:
            self.lbl_config.setText("No se ha seleccionado ninguna configuracion o la configuracion es invalida.")
            return

        try:
            env = self.config_manager.get_current_environment(current_config_name)
            version = env.get("PROTON_VERSION") if config.get("type") == "proton" else env.get("WINE_VERSION", "Desconocida")
            wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "N/A")

            text = [
                f"<b>Configuracion Actual:</b> {current_config_name}",
                f"<b>Tipo:</b> {'Proton' if config.get('type') == 'proton' else 'Wine'}",
                f"<b>Version Detectada:</b> <span style='color: #27ae60; font-weight: bold;'>{version}</span>",
            ]

            if config.get('type') == 'proton':
                text.extend([
                    f"<b>Wine en Proton:</b> <span style='color: #27ae60; font-weight: bold;'>{wine_version_in_proton}</span>",
                    f"<b>Directorio de Proton:</b> {config.get('proton_dir', 'No especificado')}"
                ])
            else:
                wine_dir = config.get('wine_dir', 'Sistema (PATH)')
                text.extend([
                    f"<b>Directorio de Wine:</b> {wine_dir}"
                ])

            text.extend([
                f"<b>Arquitectura:</b> {config.get('arch', 'win64')}",
                f"<b>Prefijo:</b> <span style='color: #FFB347; font-weight: bold;'>{config.get('prefix', 'No especificado')}</span>"
            ])

            self.lbl_config.setText("<br>".join(text))
        except FileNotFoundError as e:
            self.lbl_config.setText(f"ERROR: {str(e)}<br>Por favor, revisa la configuracion.")
            QMessageBox.critical(self, "Error de Configuracion", str(e))
        except Exception as e:
            self.lbl_config.setText(f"ERROR: No se pudo obtener informacion de configuracion: {str(e)}")


    def add_custom_program(self):
        """Abre el dialogo para anadir un nuevo programa/script personalizado."""
        dialog = CustomProgramDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                program_info = dialog.get_program_info()
                
                current_paths_in_table = [item['path'] for item in self.items_for_installation]
                if program_info['path'] in current_paths_in_table:
                    QMessageBox.warning(self, "Duplicado", f"El programa '{program_info['name']}' ya esta en la lista de instalacion.")
                    return
                
                current_config_name = self.config_manager.configs["last_used"]
                config = self.config_manager.get_config(current_config_name)
                
                if config and "prefix" in config:
                    installed_items = self.config_manager.get_installed_winetricks(config["prefix"])
                    
                    if program_info["type"] == "winetricks" and program_info["path"] in installed_items:
                        reply = QMessageBox.question(self, "Componente ya instalado",
                                                     f"El componente '{program_info['path']}' ya esta registrado como instalado en este prefijo. Deseas agregarlo a la lista de instalacion de todos modos?",
                                                     QMessageBox.Yes | QMessageBox.No)
                        if reply == QMessageBox.No: return
                    
                    elif program_info["type"] == "exe":
                        exe_filename = Path(program_info["path"]).name
                        if exe_filename in installed_items:
                            reply = QMessageBox.question(self, "Programa ya instalado",
                                                         f"El programa '{exe_filename}' ya esta registrado como instalado en este prefijo. Deseas agregarlo a la lista de instalacion de todos modos?",
                                                         QMessageBox.Yes | QMessageBox.No)
                            if reply == QMessageBox.No: return
                    elif program_info["type"] == "wtr":
                        wtr_filename = Path(program_info["path"]).name
                        if wtr_filename in installed_items:
                             reply = QMessageBox.question(self, "Script ya ejecutado",
                                                          f"El script '{wtr_filename}' ya esta registrado como ejecutado en este prefijo. Deseas agregarlo a la lista de instalacion de todos modos?",
                                                          QMessageBox.Yes | QMessageBox.No)
                             if reply == QMessageBox.No: return
                
                self.config_manager.add_custom_program(program_info) 
                self.add_item_to_table(program_info) 
                self.update_installation_button_state()
                
            except ValueError as e:
                QMessageBox.warning(self, "Entrada Invalida", str(e))
            except FileNotFoundError as e:
                QMessageBox.warning(self, "Archivo no Encontrado", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al anadir programa: {str(e)}")

    def add_item_to_table(self, program_data: dict):
        """Añade un elemento a la tabla de instalación."""
        # Disconnect signal to prevent unintended triggers during programmatic changes
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass
        
        row_count = self.items_table.rowCount()
        self.items_table.insertRow(row_count)
        
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checkbox_item.setCheckState(Qt.Checked)
        self.items_table.setItem(row_count, 0, checkbox_item)
        
        name_item = QTableWidgetItem(program_data["name"])
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row_count, 1, name_item)
        
        type_text = program_data["type"].upper()
        type_item = QTableWidgetItem(type_text)
        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row_count, 2, type_item)
        
        status_item = QTableWidgetItem("Pendiente")
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row_count, 3, status_item)
        
        # Add 'status' directly to the program_data dictionary for the internal model
        program_data['current_status'] = "Pendiente" 
        self.items_for_installation.append(program_data)
        
        self.update_installation_button_state()

        # Reconnect the signal after all programmatic changes for the row are done
        self.items_table.itemChanged.connect(self.on_table_item_changed)

    def manage_custom_programs(self):
        """Abre el dialogo para gestionar (cargar/eliminar) programas personalizados."""
        dialog = ManageProgramsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_programs = dialog.get_selected_programs_to_load()
            for program_info in selected_programs:
                if program_info not in self.items_for_installation:
                    self.add_item_to_table(program_info)
            self.update_installation_button_state()

    def select_components(self):
        """Abre el dialogo para seleccionar componentes de Winetricks."""
        component_groups = {
            "Librerias de Visual Basic": ["vb2run", "vb3run", "vb4run", "vb5run", "vb6run"],
            "Tiempo de Ejecucion de Visual C++": [
                "vcrun6", "vcrun6sp6", "vcrun2003", "vcrun2005", "vcrun2008",
                "vcrun2010", "vcrun2012", "vcrun2013", "vcrun2015", "vcrun2017",
                "vcrun2019", "vcrun2022"
            ],
            "Framework .NET": [
                "dotnet11", "dotnet11sp1", "dotnet20", "dotnet20sp1", "dotnet20sp2",
                "dotnet30", "dotnet30sp1", "dotnet35", "dotnet35sp1", "dotnet40",
                "dotnet40_kb2468871", "dotnet45", "dotnet452", "dotnet46", "dotnet461",
                "dotnet462", "dotnet471", "dotnet472", "dotnet48", "dotnet6", "dotnet7",
                "dotnet8", "dotnet9", "dotnetcore2", "dotnetcore3", "dotnetcoredesktop3",
                "dotnetdesktop6", "dotnetdesktop7", "dotnetdesktop8", "dotnetdesktop9"
            ],
            "DirectX y Multimedia": [
                "d3dcompiler_42", "d3dcompiler_43", "d3dcompiler_46", "d3dcompiler_47",
                "d3dx9", "d3dx9_24", "d3dx9_25", "d3dx9_26", "d3dx9_27", "d3dx9_28",
                "d3dx9_29", "d3dx9_30", "d3dx9_31", "d3dx9_32", "d3dx9_33", "d3dx9_34",
                "d3dx9_35", "d3dx9_36", "d3dx9_37", "d3dx9_38", "d3dx9_39", "d3dx9_40",
                "d3dx9_41", "d3dx9_42", "d3dx9_43", "d3dx10", "d3dx10_43", "d3dx11_42",
                "d3dx11_43", "d3dxof", "devenum", "dinput", "dinput8", "directmusic",
                "directplay", "directshow", "directx9", "dmband", "dmcompos", "dmime",
                "dmloader", "dmscript", "dmstyle", "dmsynth", "dmusic", "dmusic32",
                "dx8vb", "dxdiag", "dxdiagn", "dxdiagn_feb2010", "dxtrans", "xact",
                "xact_x64", "xaudio29", "xinput", "xna31", "xna40"
            ],
            "DXVK y VKD3D": [
                "dxvk", "dxvk1000", "dxvk1001", "dxvk1002", "dxvk1003", "dxvk1011",
                "dxvk1020", "dxvk1021", "dxvk1022", "dxvk1023", "dxvk1030", "dxvk1031",
                "dxvk1032", "dxvk1033", "dxvk1034", "dxvk1040", "dxvk1041", "dxvk1042",
                "dxvk1043", "dxvk1044", "dxvk1045", "dxvk1046", "dxvk1050", "dxvk1051",
                "dxvk1052", "dxvk1053", "dxvk1054", "dxvk1055", "dxvk1060", "dxvk1061",
                "dxvk1070", "dxvk1071", "dxvk1072", "dxvk1073", "dxvk1080", "dxvk1081",
                "dxvk1090", "dxvk1091", "dxvk1092", "dxvk1093", "dxvk1094", "dxvk1100",
                "dxvk1101", "dxvk1102", "dxvk1103", "dxvk2000", "dxvk2010", "dxvk2020",
                "dxvk2030", "dxvk2040", "dxvk2041", "dxvk2050", "dxvk2051", "dxvk2052",
                "dxvk2053", "dxvk2060", "dxvk2061", "dxvk2062", "vkd3d"
            ],
            "Codecs Multimedia": [
                "allcodecs", "avifil32", "binkw32", "cinepak", "dirac", "ffdshow",
                "icodecs", "l3codecx", "lavfilters", "lavfilters702", "ogg", "qasf",
                "qcap", "qdvd", "qedit", "quartz", "quartz_feb2010", "quicktime72",
                "quicktime76", "wmp9", "wmp10", "wmp11", "wmv9vcm", "xvid"
            ],
            "Componentes del Sistema": [
                "amstream", "atmlib", "cabinet", "cmd", "comctl32", "comctl32ocx",
                "comdlg32ocx", "crypt32", "crypt32_winxp", "dbghelp", "esent", "filever",
                "gdiplus", "gdiplus_winxp", "glidewrapper", "glut", "gmdls", "hid",
                "jet40", "mdac27", "mdac28", "msaa", "msacm32", "msasn1", "msctf",
                "msdelta", "msdxmocx", "msflxgrd", "msftedit", "mshflxgd", "msls31",
                "msmask", "mspatcha", "msscript", "msvcirt", "msvcrt40", "msxml3",
                "msxml4", "msxml6", "ole32", "oleaut32", "pdh", "pdh_nt4", "peverify",
                "pngfilt", "prntvpt", "python26", "python27", "riched20", "riched30",
                "richtx32", "sapi", "sdl", "secur32", "setupapi", "shockwave",
                "speechsdk", "tabctl32", "ucrtbase2019", "uiribbon", "updspapi",
                "urlmon", "usp10", "webio", "windowscodes", "winhttp", "wininet",
                "wininet_win2k", "wmi", "wsh57", "xmllite"
            ],
            "Controladores y Utilidades": [
                "art2k7min", "art2kmin", "cnc_ddraw", "d2gl", "d3drm", "dpvoice",
                "dsdmo", "dsound", "dswave", "faudio", "faudio1901", "faudio1902",
                "faudio1903", "faudio1904", "faudio1905", "faudio1906", "faudio190607",
                "galliumnine", "galliumnine02", "galliumnine03", "galliumnine04",
                "galliumnine05", "galliumnine06", "galliumnine07", "galliumnine08",
                "galliumnine09", "gfw", "ie6", "ie7", "ie8", "ie8_kb2936068",
                "ie8_tls12", "iertutil", "itircl", "itss", "mdx", "mf", "mfc40",
                "mfc42", "mfc70", "mfc71", "mfc80", "mfc90", "mfc100", "mfc110",
                "mfc120", "mfc140", "nuget", "openal", "otvdm", "otvdm090",
                "physx", "powershell", "powershell_core"
            ]
        }

        dialog = SelectGroupsDialog(component_groups, self.config_manager, self) 
        if dialog.exec_() == QDialog.Accepted:
            selected_components = dialog.get_selected_components()
            
            current_config_name = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config_name)
            installed_components = []
            if config and "prefix" in config:
                installed_components = self.config_manager.get_installed_winetricks(config["prefix"])
                
            for comp_name in selected_components:
                if any(item.get('path') == comp_name and item.get('type') == 'winetricks' for item in self.items_for_installation):
                    QMessageBox.warning(self, "Duplicado", f"El componente '{comp_name}' ya esta en la lista de instalacion.")
                    continue

                if comp_name in installed_components:
                    reply = QMessageBox.question(self, "Componente ya instalado",
                                                 f"El componente '{comp_name}' ya esta registrado como instalado en este prefijo. Deseas agregarlo a la lista de instalacion de todos modos?",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.No:
                        continue
                    
                self.add_item_to_table({"name": comp_name, "path": comp_name, "type": "winetricks"})
            self.update_installation_button_state()

    def cancel_installation(self):
        """
        Detiene la instalacion actual si hay un hilo instalador en ejecucion.
        Pide confirmacion al usuario antes de cancelar.
        """
        if self.installer_thread and self.installer_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirmar Cancelacion",
                "Estas seguro de que quieres cancelar la instalacion en curso?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.installer_thread.stop() 
                self.installer_thread.wait() 
                QMessageBox.information(self, "Cancelado", "La instalacion ha sido cancelada por el usuario.")
        else:
            QMessageBox.information(self, "Informacion", "No hay ninguna instalacion en progreso para cancelar.")

    def clear_list(self):
        """Borra la tabla y el modelo de datos interno, restableciendo los estados de los botones."""
        reply = QMessageBox.question(self, "Confirmar", "Estas seguro de que quieres borrar toda la lista de instalacion?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.items_table.setRowCount(0)
            self.items_for_installation.clear()
            self.update_installation_button_state()

    def delete_selected_from_table(self):
        """Elimina los elementos seleccionados de la tabla y el modelo de datos interno."""
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())), reverse=True)
        
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron elementos para eliminar.")
            return

        reply = QMessageBox.question(self, "Confirmar Eliminacion", 
                                     f"Estas seguro de que quieres eliminar {len(selected_rows)} elemento(s) de la lista de instalacion?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            
            for row in selected_rows:
                if 0 <= row < len(self.items_for_installation):
                    del self.items_for_installation[row]
                self.items_table.removeRow(row)
                
            self.items_table.itemChanged.connect(self.on_table_item_changed)
            self.update_installation_button_state()

    def move_item_up(self):
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())))
        
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Advertencia", "Selecciona solo un elemento para mover.")
            return

        current_row = selected_rows[0]
        if current_row > 0:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            self.swap_table_rows(current_row, current_row - 1)
            self.items_for_installation[current_row], self.items_for_installation[current_row - 1] = \
                self.items_for_installation[current_row - 1], self.items_for_installation[current_row]
            self.items_table.selectRow(current_row - 1)
            self.items_table.itemChanged.connect(self.on_table_item_changed)


    def move_item_down(self):
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())))
        
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Advertencia", "Selecciona solo un elemento para mover.")
            return

        current_row = selected_rows[0]
        if current_row < self.items_table.rowCount() - 1:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            self.swap_table_rows(current_row, current_row + 1)
            self.items_for_installation[current_row], self.items_for_installation[current_row + 1] = \
                self.items_for_installation[current_row + 1], self.items_for_installation[current_row]
            self.items_table.selectRow(current_row + 1)
            self.items_table.itemChanged.connect(self.on_table_item_changed)

    def swap_table_rows(self, row1: int, row2: int):
        row1_items = [self.items_table.takeItem(row1, col) for col in range(self.items_table.columnCount())]
        row2_items = [self.items_table.takeItem(row2, col) for col in range(self.items_table.columnCount())]

        for col in range(self.items_table.columnCount()):
            self.items_table.setItem(row2, col, row1_items[col])
            self.items_table.setItem(row1, col, row2_items[col])

    def update_installation_button_state(self):
        """Habilita/deshabilita el boton de instalacion si hay elementos marcados."""
        any_checked = False
        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 0).checkState() == Qt.Checked:
                any_checked = True
                break
        self.btn_install.setEnabled(any_checked)

    def start_installation(self):
        """Inicia el proceso de instalación de los elementos seleccionados."""
        current_config_name = self.config_manager.configs.get("last_used")
        config = self.config_manager.get_config(current_config_name)

        if not config:
            QMessageBox.critical(self, "Error", "No se ha seleccionado ninguna configuración de Wine/Proton o es inválida.")
            return

        items_to_process_data_for_thread = []
        for row in range(self.items_table.rowCount()):
            item_data = self.items_for_installation[row]
            checkbox_item = self.items_table.item(row, 0)

            if checkbox_item.checkState() == Qt.Checked:
                # IMPORTANT: Now pass the user_defined_name as the third element
                items_to_process_data_for_thread.append((item_data['path'], item_data['type'], item_data['name']))
                item_data['current_status'] = "Pendiente" 
                self.items_table.item(row, 3).setText("Pendiente") 
                self.items_table.item(row, 3).setForeground(QColor(STYLE_STEAM_DECK["dark_palette"]["text"]) if self.config_manager.get_theme() == "dark" else QColor(STYLE_STEAM_DECK["light_palette"]["text"]))
            else:
                item_data['current_status'] = "Omitido"
                self.items_table.item(row, 3).setText("Omitido")
                self.items_table.item(row, 3).setForeground(QColor("darkorange"))


        if not items_to_process_data_for_thread:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron elementos para instalar. Marca los elementos que deseas instalar.")
            return

        prefix_path = Path(config["prefix"])
        if not prefix_path.exists():
            reply = QMessageBox.question(
                self, "Prefijo No Encontrado",
                f"El prefijo de Wine/Proton en '{config['prefix']}' no existe. ¿Deseas crearlo ahora? Esto inicializará el prefijo.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    self._create_prefix(config, current_config_name, prefix_path)
                    QMessageBox.information(self, "Prefijo Creado", "El prefijo de Wine/Proton ha sido creado exitosamente.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo crear el prefijo:\n{str(e)}")
                    return
            else:
                return 

        try:
            env = self.config_manager.get_current_environment(current_config_name)
        except Exception as e:
            QMessageBox.critical(self, "Error de Entorno", f"No se pudo configurar el entorno para la instalación:\n{str(e)}")
            return
            
        self.installer_thread = InstallerThread(
            items_to_process_data_for_thread, # Pass the filtered and prepared list in new format
            env,
            silent_mode=self.silent_mode,
            force_mode=self.force_mode, 
            winetricks_path=self.config_manager.get_winetricks_path(),
            config_manager=self.config_manager
        )
        
        self.installer_thread.progress.connect(self.update_progress)
        self.installer_thread.finished.connect(self.installation_finished)
        self.installer_thread.error.connect(self.show_installation_error)
        self.installer_thread.canceled.connect(self.on_installation_canceled)

        self.btn_install.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_select_components.setEnabled(False)
        self.btn_add_custom.setEnabled(False)
        self.btn_manage_custom.setEnabled(False)
        
        self.installer_thread.start()

    def _create_prefix(self, config: dict, config_name: str, prefix_path: Path):
        """Crea un nuevo prefijo de Wine/Proton y lo inicializa."""
        prefix_path.mkdir(parents=True, exist_ok=True, mode=0o755)
        env = self.config_manager.get_current_environment(config_name)

        wine_executable = env.get("WINE")
        if not wine_executable or not Path(wine_executable).is_file():
            raise FileNotFoundError(f"Ejecutable de Wine no encontrado: {wine_executable}")

        progress_dialog = QProgressDialog("Inicializando Prefijo de Wine/Proton...", "Cancelar", 0, 0, self) 
        progress_dialog.setWindowTitle("Inicializacion del Prefijo")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None) 
        progress_dialog.show() 

        try:
            process = subprocess.Popen(
                ["konsole", "--noclose", "-e", wine_executable, "wineboot"],
                env=env,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True
            )
            log_output = ""
            for line in process.stdout:
                log_output += line
                QApplication.processEvents() 
            process.wait(timeout=60) 
            
            self.config_manager.write_to_log("Creacion del Prefijo", f"Salida de Wineboot para {config_name}:\n{log_output}")
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "wineboot", output=log_output)

        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception("La inicializacion del prefijo de Wine/Proton agoto el tiempo de espera.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"No se pudo inicializar el prefijo de Wine/Proton. Codigo de salida: {e.returncode}\nSalida: {e.output}")
        finally:
            progress_dialog.close()

    def update_progress(self, name: str, status: str):
        """Actualiza el estado de un elemento en la tabla y en el modelo interno."""
        # First, update the internal data model
        found_in_model = False
        for item_data in self.items_for_installation:
            # Match against the 'name' field in our internal model
            if item_data['name'] == name:
                item_data['current_status'] = status
                found_in_model = True
                break
        
        if not found_in_model:
            print(f"DEBUG: Item '{name}' not found in internal items_for_installation list for status update.")

        # Then, update the table's visual representation
        for row in range(self.items_table.rowCount()):
            # Match by the displayed name in the table
            if self.items_table.item(row, 1).text() == name:
                status_item = self.items_table.item(row, 3)
                if status_item: # Ensure item exists
                    status_item.setText(status)
                    if "Error" in status:
                        status_item.setForeground(QColor(255, 0, 0)) # Red
                    elif "Finalizado" in status:
                        status_item.setForeground(QColor(0, 128, 0)) # Green
                    elif "Cancelado" in status:
                        status_item.setForeground(QColor("orange")) # Orange
                    else: # Pending, Installing...
                        theme = self.config_manager.get_theme()
                        status_item.setForeground(QColor(STYLE_STEAM_DECK["dark_palette"]["text"]) if theme == "dark" else QColor(STYLE_STEAM_DECK["light_palette"]["text"]))
                else:
                    print(f"DEBUG: Status item is None for row {row}, name '{name}'.")
                break # Stop after finding and updating the item in the table

    def on_installation_canceled(self, item_name: str):
        """Actualiza el estado de un elemento cuando la instalación es cancelada."""
        # Update internal model
        for item_data in self.items_for_installation:
            if item_data['name'] == item_name:
                item_data['current_status'] = "Cancelado"
                break

        # Update table display
        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 1).text() == item_name:
                status_item = self.items_table.item(row, 3)
                checkbox_item = self.items_table.item(row, 0)
                if status_item:
                    status_item.setText("Cancelado")
                    status_item.setForeground(QColor("orange"))
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Checked) # Keep checked to allow re-attempt
                break

    def installation_finished(self):
        """Maneja el estado final de la instalación, actualizando la GUI y mostrando un resumen."""
        installed_count = 0
        failed_count = 0
        skipped_count = 0
        
        # Disconnect itemChanged signal to prevent unintended updates when updating checkboxes
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass

        # Iterate through the *internal data model* (self.items_for_installation)
        # to get accurate counts and update table checkboxes
        for row, item_data in enumerate(self.items_for_installation):
            current_status = item_data['current_status']
            checkbox_item = self.items_table.item(row, 0) # Get the checkbox for the corresponding row

            if "Finalizado" in current_status:
                installed_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Unchecked) # Desmarcar elementos exitosos
            elif "Error" in current_status or "Cancelado" in current_status:
                failed_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Checked) # Keep checkbox checked for failed/canceled items, so user can retry
            elif "Omitido" in current_status:
                skipped_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Unchecked) # Keep checkbox unchecked for skipped items

        # Reconnect the signal
        self.items_table.itemChanged.connect(self.on_table_item_changed)

        # Re-enable controls
        self.btn_install.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_select_components.setEnabled(True)
        self.btn_add_custom.setEnabled(True)
        self.btn_manage_custom.setEnabled(True)

        QMessageBox.information(
            self,
            "Instalacion Completada",
            f"Resumen de la Instalacion:\n\n"
            f"• Instalado exitosamente: {installed_count}\n"
            f"• Fallido o Cancelado: {failed_count}\n"
            f"• Omitido (no seleccionado): {skipped_count}\n\n"
            f"Los elementos instalados exitosamente han sido deseleccionados de la lista."
        )
        self.update_installation_button_state()

    def show_installation_error(self, message: str):
        """Muestra un mensaje de error critico durante la instalacion y restablece los controles."""
        QMessageBox.critical(self, "Error de Instalacion", message)
        # Asegurarse de que los botones se vuelvan a habilitar despues de un error
        self.btn_install.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_select_components.setEnabled(True)
        self.btn_add_custom.setEnabled(True)
        self.btn_manage_custom.setEnabled(True)
        self.update_installation_button_state()


    def open_winetricks(self):
        """Abre la GUI de Winetricks para el prefijo actual."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            winetricks_path = self.config_manager.get_winetricks_path()
            
            subprocess.Popen([winetricks_path, "--gui"], env=env)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Winetricks: {str(e)}")

    def open_shell(self):
        """Abre una terminal (Konsole) con el entorno de Wine/Proton configurado."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            subprocess.Popen(["konsole"], env=env)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la terminal: {str(e)}")
            
    def open_prefix_folder(self):
        """Abre la carpeta del prefijo de Wine/Proton en el explorador de archivos."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config_name)
            
            if config and "prefix" in config:
                prefix_path = Path(config["prefix"])
                if prefix_path.exists():
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(prefix_path)))
                else:
                    QMessageBox.warning(self, "Advertencia", f"El prefijo '{prefix_path}' no existe. Por favor, asegurate de que este configurado o crealo.")
            else:
                QMessageBox.warning(self, "Advertencia", "No hay ningun prefijo configurado para el entorno actual.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la carpeta del prefijo: {str(e)}")
            
    def open_explorer(self):
        """Ejecuta wine explorer para el prefijo actual."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config_name)
            
            if config and "prefix" in config:
                prefix_path = Path(config["prefix"])
                if prefix_path.exists():
                    env = self.config_manager.get_current_environment(current_config_name)
                    wine_executable = env.get("WINE")
                    
                    if not wine_executable or not Path(wine_executable).is_file():
                        raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")
                    
                    subprocess.Popen([wine_executable, "explorer"], env=env)
                else:
                    QMessageBox.warning(self, "Advertencia", f"El prefijo '{prefix_path}' no existe. Por favor, asegurate de que este configurado o crealo.")
            else:
                QMessageBox.warning(self, "Advertencia", "No hay ningun prefijo configurado para el entorno actual.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el Explorador de Wine: {str(e)}")
            
    def open_winecfg(self):
        """Ejecuta winecfg para el prefijo actual."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            
            wine_executable = env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")
                
            subprocess.Popen([wine_executable, "winecfg"], env=env)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Winecfg: {str(e)}")
