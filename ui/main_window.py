import sys
import os
import subprocess
from pathlib import Path
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

# Actualiza esta importación para incluir SelectGroupsDialog
from dialogs import ConfigDialog, CustomProgramDialog, ManageProgramsDialog, SelectGroupsDialog
from installer_thread import InstallerThread
from styles import STEAM_DECK_STYLE

class InstallerApp(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.installer_thread = None
        self.selected_components = []
        self.custom_programs = []
        self.custom_program_types = []
        self.silent_mode = self.config_manager.get_silent_install()

        # Aplicar el tema guardado al iniciar
        self.apply_theme_on_startup()
        self.setup_ui()
        self.apply_steamdeck_style()
        self.setMinimumSize(1000, 700)  # Tamaño mínimo fijo

    def apply_theme_on_startup(self):
        theme = self.config_manager.get_theme()
        palette = QApplication.palette()
        
        if theme == "dark":
            palette.setColor(QPalette.Window, STEAM_DECK_STYLE["dark_palette"]["window"])
            palette.setColor(QPalette.WindowText, STEAM_DECK_STYLE["dark_palette"]["window_text"])
            palette.setColor(QPalette.Base, STEAM_DECK_STYLE["dark_palette"]["base"])
            palette.setColor(QPalette.Text, STEAM_DECK_STYLE["dark_palette"]["text"])
            palette.setColor(QPalette.Button, STEAM_DECK_STYLE["dark_palette"]["button"])
            palette.setColor(QPalette.ButtonText, STEAM_DECK_STYLE["dark_palette"]["button_text"])
            palette.setColor(QPalette.Highlight, STEAM_DECK_STYLE["dark_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, STEAM_DECK_STYLE["dark_palette"]["highlight_text"])
        else:
            palette = QApplication.style().standardPalette()
        
        QApplication.setPalette(palette)

    def apply_steamdeck_style(self):
        self.setFont(STEAM_DECK_STYLE["font"])
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(STEAM_DECK_STYLE["font"])

            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STEAM_DECK_STYLE["button_style"])
            
            # Aplicar a los QGroupBox
            if isinstance(widget, QGroupBox):
                widget.setFont(STEAM_DECK_STYLE["title_font"])
                
        # Conectar el cambio de estado de los checkboxes
        self.items_table.itemChanged.connect(self.on_item_check_changed)

    def setup_ui(self):
        self.setWindowTitle("WineProton Manager")
        self.resize(self.config_manager.get_window_size())
        self.setWindowIcon(QIcon.fromTheme("wine"))

        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout_content = QHBoxLayout(content)
        
        layout_content.addWidget(self.create_left_panel(), 1)
        layout_content.addWidget(self.create_right_panel(), 2)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        config_group = QGroupBox("Configuración del Entorno")
        config_layout = QVBoxLayout()
        self.config_label = QLabel()
        self.config_label.setWordWrap(True)
        self.update_config_info()  # Cambiado de update_config_label() a update_config_info()
        
        self.config_btn = QPushButton("Configurar Entornos...")
        self.config_btn.setAutoDefault(False)
        self.config_btn.clicked.connect(self.configure_environments)
        config_layout.addWidget(self.config_label)
        config_layout.addWidget(self.config_btn)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        action_group = QGroupBox("Acciones")
        action_layout = QVBoxLayout()
        
        comp_group = QGroupBox("Componentes")
        comp_layout = QVBoxLayout()
        self.select_components_btn = QPushButton("Seleccionar Componentes")
        self.select_components_btn.setAutoDefault(False)
        self.select_components_btn.clicked.connect(self.select_components)
        comp_layout.addWidget(self.select_components_btn)
        comp_group.setLayout(comp_layout)
        action_layout.addWidget(comp_group)
        
        custom_group = QGroupBox("Programas Personalizados")
        custom_layout = QVBoxLayout()
        self.add_custom_btn = QPushButton("Añadir Programa")
        self.add_custom_btn.setAutoDefault(False)
        self.add_custom_btn.clicked.connect(self.add_custom_program)
        custom_layout.addWidget(self.add_custom_btn)
        
        self.manage_custom_btn = QPushButton("Gestionar Programas Guardados")
        self.manage_custom_btn.setAutoDefault(False)
        self.manage_custom_btn.clicked.connect(self.manage_custom_programs)
        custom_layout.addWidget(self.manage_custom_btn)
        custom_group.setLayout(custom_layout)
        action_layout.addWidget(custom_group)
        
        options_group = QGroupBox("Opciones de Instalación")
        options_layout = QVBoxLayout()
        self.silent_checkbox = QCheckBox("Modo silencioso (solo para winetricks)")
        self.silent_checkbox.setChecked(self.silent_mode)
        self.silent_checkbox.stateChanged.connect(self.update_silent_mode)
        options_layout.addWidget(self.silent_checkbox)
        options_group.setLayout(options_layout)
        action_layout.addWidget(options_group)
        
        self.install_btn = QPushButton("Iniciar Instalación")
        self.install_btn.setAutoDefault(False)
        self.install_btn.clicked.connect(self.start_installation)
        self.install_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancelar Instalación")
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.clicked.connect(self.cancel_installation)
        self.cancel_btn.setEnabled(False)
        
        self.winetricks_btn = QPushButton("Abrir Winetricks GUI")
        self.winetricks_btn.setAutoDefault(False)
        self.winetricks_btn.clicked.connect(self.open_winetricks)
        
        # Crear layout para los botones en dos columnas
        tools_layout = QHBoxLayout()
        
        # Columna izquierda
        left_col = QVBoxLayout()
        self.shell_btn = QPushButton("Terminal")
        self.shell_btn.setAutoDefault(False)
        self.shell_btn.clicked.connect(self.open_shell)
        left_col.addWidget(self.shell_btn)
        
        self.prefix_btn = QPushButton("Prefix")
        self.prefix_btn.setAutoDefault(False)
        self.prefix_btn.clicked.connect(self.open_prefix_folder)
        left_col.addWidget(self.prefix_btn)
        
        # Columna derecha
        right_col = QVBoxLayout()
        self.cfgwine_btn = QPushButton("Winecfg")
        self.cfgwine_btn.setAutoDefault(False)
        self.cfgwine_btn.clicked.connect(self.open_cfgwine)
        right_col.addWidget(self.cfgwine_btn)
        
        self.explorer_btn = QPushButton("Explorer")
        self.explorer_btn.setAutoDefault(False)
        self.explorer_btn.clicked.connect(self.open_explorer)
        right_col.addWidget(self.explorer_btn)
        
        # Añadir columnas al layout horizontal
        tools_layout.addLayout(left_col)
        tools_layout.addLayout(right_col)
        
        action_layout.addWidget(self.install_btn)
        action_layout.addWidget(self.cancel_btn)
        action_layout.addWidget(self.winetricks_btn)
        action_layout.addLayout(tools_layout)
        action_layout.addStretch()
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        return panel

    def create_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        self.status_label = QLabel("Items a instalar:")
        layout.addWidget(self.status_label)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Acciones", "Nombre", "Tipo", "Estado"])
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.items_table)
        
        btn_layout = QHBoxLayout()
        buttons = [
            ("Limpiar Lista", self.clear_list),
            ("Eliminar Seleccionados", self.remove_selected),
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

    def set_theme(self, theme):
        self.config_manager.set_theme(theme)
        self.apply_theme()

    def closeEvent(self, event):
        self.config_manager.save_window_size(self.size())
        super().closeEvent(event)

    def configure_environments(self):
        dialog = ConfigDialog(self.config_manager, self)
        dialog.config_saved.connect(self.update_config_info)  # Cambiado de update_config_label a update_config_info
        dialog.exec_()
        self.update_config_info() 

    def update_config_info(self):
        current = self.config_manager.configs["last_used"]
        config = self.config_manager.get_config(current)

        if not config:
            self.config_label.setText("No hay configuración seleccionada")
            return

        env = self.config_manager.get_current_env(current)
        version = env.get("PROTON_VERSION") if config.get("type") == "proton" else env.get("WINE_VERSION", "Desconocida")
        wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "Desconocida")

        # Usar colores fijos (no basados en el tema actual)
        text = [
            f"<b>Configuración actual:</b> {current}",
            f"<b>Tipo:</b> {'Proton' if config.get('type') == 'proton' else 'Wine'}",
            f"<b>Versión:</b> <span style='color: #27ae60; font-weight: bold;'>{version}</span>",
        ]

        if config.get('type') == 'proton':
            text.extend([
                f"<b>Wine en Proton:</b> <span style='color: #27ae60; font-weight: bold;'>{wine_version_in_proton}</span>",
                f"<b>Directorio Proton:</b> {config.get('proton_dir', 'No especificado')}"
            ])
        else:
            wine_dir = config.get('wine_dir', 'Sistema')
            text.extend([
                f"<b>Directorio Wine:</b> {wine_dir}"
            ])

        text.extend([
            f"<b>Arquitectura:</b> {config.get('arch', 'win64')}",
            f"<b>Prefix:</b> <span style='color: #FFB347; font-weight: bold;'>{config.get('prefix', 'No especificado')}"
        ])

        self.config_label.setText("<br>".join(text))
    
    def on_item_check_changed(self, item):
        if item.column() == 0:  # Es la columna del checkbox
            row = item.row()
            status_item = self.items_table.item(row, 3)
            if status_item:
                if item.checkState() == Qt.Checked:
                    status_item.setText("Pendiente")
                else:
                    status_item.setText("Omitido")
    
    def add_custom_program(self):
        dialog = CustomProgramDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                program_info = dialog.get_program_info()
                program_path = program_info["path"]  # Ruta completa o comando Winetricks
                program_name = program_info["name"]
                program_type = program_info["type"]

                display_type = "EXE" if program_type == "exe" else "Winetricks"
                
                # Verificar si ya está instalado
                current_config = self.config_manager.configs["last_used"]
                config = self.config_manager.get_config(current_config)
                installed_components = []
                
                if config and "prefix" in config:
                    installed_components = self.config_manager.get_installed_winetricks(config["prefix"])
                
                # Para winetricks, usar el nombre del componente
                if program_type == "winetricks":
                    component_name = program_path
                    if component_name in installed_components:
                        reply = QMessageBox.question(
                            self,
                            "Componente ya instalado",
                            f"El componente '{component_name}' ya está instalado en este prefix. ¿Deseas instalarlo de todos modos?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            return
                # Para EXE, usar el nombre del archivo
                else:
                    exe_name = Path(program_path).name
                    if exe_name in installed_components:
                        reply = QMessageBox.question(
                            self,
                            "Programa ya instalado",
                            f"El programa '{exe_name}' ya está instalado en este prefix. ¿Deseas instalarlo de todos modos?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            return
                
                # Añadir a las listas internas (usando el path/command exacto)
                self.custom_programs.append(program_path)
                self.custom_program_types.append(program_type)
                
                # Mostrar en la tabla
                self.add_item_to_table(program_name, display_type)
                self.update_install_button()
                
                # Guardar en config.json
                program_data = {
                    "name": program_name,
                    "path": program_path,  # Guardamos el path/command exacto
                    "type": program_type
                }
                if "custom_programs" not in self.config_manager.configs:
                    self.config_manager.configs["custom_programs"] = []
                self.config_manager.configs["custom_programs"].append(program_data)
                self.config_manager.save_configs()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al añadir programa:\n{str(e)}")
                
    def add_item_to_table(self, name, item_type, status="Pendiente", command=None):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Checkbox
        checkbox = QTableWidgetItem()
        checkbox.setFlags(checkbox.flags() | Qt.ItemIsUserCheckable)
        checkbox.setCheckState(Qt.Checked)
        self.items_table.setItem(row, 0, checkbox)
        
        # Nombre
        name_item = QTableWidgetItem(name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 1, name_item)
        
        # Tipo
        type_item = QTableWidgetItem(item_type)
        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 2, type_item)
        
        # Estado
        status_item = QTableWidgetItem(status)
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 3, status_item)
    
    def update_silent_mode(self, state):
        self.silent_mode = state == Qt.Checked
        self.config_manager.set_silent_install(self.silent_mode)

    def manage_custom_programs(self):
        dialog = ManageProgramsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_programs = dialog.get_selected_programs()
            
            if not selected_programs:
                return
                
            # Verificar duplicados antes de añadir
            current_config = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config)
            installed_components = []
            
            if config and "prefix" in config:
                installed_components = self.config_manager.get_installed_winetricks(config["prefix"])
            
            for program in selected_programs:
                # Verificar si ya está instalado
                if program["type"] == "winetricks":
                    component_name = program["path"]
                    if component_name in installed_components:
                        reply = QMessageBox.question(
                            self,
                            "Componente ya instalado",
                            f"El componente '{component_name}' ya está instalado en este prefix. ¿Deseas instalarlo de todos modos?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            continue
                else:
                    exe_name = Path(program["path"]).name
                    if exe_name in installed_components:
                        reply = QMessageBox.question(
                            self,
                            "Programa ya instalado",
                            f"El programa '{exe_name}' ya está instalado en este prefix. ¿Deseas instalarlo de todos modos?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            continue
                
                # Añadir a la lista de instalación
                self.custom_programs.append(program["path"])
                self.custom_program_types.append(program["type"])
                display_type = "EXE" if program["type"] == "exe" else "Winetricks"
                self.add_item_to_table(program['name'], display_type)
            
            self.update_install_button()
            # No cerramos la ventana de gestión para permitir más selecciones

    def select_components(self):
        component_groups = {
            "Bibliotecas Visual Basic": ["vb2run", "vb3run", "vb4run", "vb5run", "vb6run"],
            "Visual C++ Runtime": [
                "vcrun6", "vcrun6sp6", "vcrun2003", "vcrun2005", "vcrun2008",
                "vcrun2010", "vcrun2012", "vcrun2013", "vcrun2015", "vcrun2017",
                "vcrun2019", "vcrun2022"
            ],
            ".NET Framework": [
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
            "Componentes de Sistema": [
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

        dialog = SelectGroupsDialog(component_groups)
        if dialog.exec_() == QDialog.Accepted:
            selected_components = dialog.get_selected_components()
            
            current_config = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config)
            installed_components = []
            
            if config and "prefix" in config:
                installed_components = self.config_manager.get_installed_winetricks(config["prefix"])
            
            for comp in selected_components:
                if comp in installed_components:
                    reply = QMessageBox.question(
                        self,
                        "Componente ya instalado",
                        f"El componente '{comp}' ya está instalado en este prefix. ¿Deseas instalarlo de todos modos?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        continue
                
                self.selected_components.append(comp)
                self.add_item_to_table(comp, "Winetricks")
            self.update_install_button()

    def clear_list(self):
        # Limpiar la lista como antes
        self.items_table.setRowCount(0)
        self.selected_components = []
        self.custom_programs = []
        self.custom_program_types = []
        
        # Restablecer los botones a su estado normal
        self.install_btn.setEnabled(False)
        self.add_custom_btn.setEnabled(True)
        self.manage_custom_btn.setEnabled(True)
        self.select_components_btn.setEnabled(True)
        
        # Actualizar estado del botón de instalación
        self.update_install_button()

    def remove_selected(self):
        selected_rows = set()
        for index in self.items_table.selectedIndexes():
            selected_rows.add(index.row())
        
        if not selected_rows:
            return

        for row in sorted(selected_rows, reverse=True):
            item_name = self.items_table.item(row, 1).text()
            
            if item_name in self.selected_components:
                self.selected_components.remove(item_name)
            else:
                for i, prog in enumerate(self.custom_programs[:]):
                    if item_name in prog:
                        del self.custom_programs[i]
                        del self.custom_program_types[i]
                        break
            
            self.items_table.removeRow(row)
        
        self.update_install_button()

    def move_item_up(self):
        selected_rows = set()
        for index in self.items_table.selectedIndexes():
            selected_rows.add(index.row())
        
        if not selected_rows or len(selected_rows) > 1:
            return

        current_row = list(selected_rows)[0]
        if current_row > 0:
            self.swap_table_rows(current_row, current_row - 1)
            self.items_table.selectRow(current_row - 1)
            self._reorder_internal_lists()

    def move_item_down(self):
        selected_rows = set()
        for index in self.items_table.selectedIndexes():
            selected_rows.add(index.row())
        
        if not selected_rows or len(selected_rows) > 1:
            return

        current_row = list(selected_rows)[0]
        if current_row < self.items_table.rowCount() - 1:
            self.swap_table_rows(current_row, current_row + 1)
            self.items_table.selectRow(current_row + 1)
            self._reorder_internal_lists()

    def swap_table_rows(self, row1, row2):
        for col in range(self.items_table.columnCount()):
            item1 = self.items_table.takeItem(row1, col)
            item2 = self.items_table.takeItem(row2, col)
            self.items_table.setItem(row2, col, item1)
            self.items_table.setItem(row1, col, item2)

    def _reorder_internal_lists(self):
        new_selected_components = []
        new_custom_programs = []
        new_custom_program_types = []
        
        for row in range(self.items_table.rowCount()):
            item_name = self.items_table.item(row, 1).text()
            item_type = self.items_table.item(row, 2).text()
            
            if item_type == "Winetricks":
                new_selected_components.append(item_name)
            else:
                for i, prog in enumerate(self.custom_programs):
                    if item_name in prog:
                        new_custom_programs.append(prog)
                        new_custom_program_types.append(self.custom_program_types[i])
                        break
        
        self.selected_components = new_selected_components
        self.custom_programs = new_custom_programs
        self.custom_program_types = new_custom_program_types

    def update_install_button(self):
        self.install_btn.setEnabled(self.items_table.rowCount() > 0)

    def start_installation(self):
        current_config = self.config_manager.configs["last_used"]
        config = self.config_manager.get_config(current_config)

        if not config:
            QMessageBox.critical(self, "Error", "No hay configuración seleccionada")
            return

        prefix_path = Path(config["prefix"])
        if not prefix_path.exists():
            reply = QMessageBox.question(
                self,
                "Prefix no encontrado",
                f"El prefix {config['prefix']} no existe. ¿Deseas crearlo?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    prefix_path.mkdir(parents=True, exist_ok=True, mode=0o755)
                    env = self.config_manager.get_current_env(current_config)

                    if config["type"] == "proton":
                        proton_dir = Path(config["proton_dir"])
                        wine_bin = str(proton_dir / "files/bin/wine")
                    else:
                        wine_dir = config.get("wine_dir")
                        if wine_dir:
                            wine_bin = str(Path(wine_dir) / "bin/wine")
                        else:
                            wine_bin = "wine"

                    subprocess.run(
                        ["konsole", "--noclose", "-e", wine_bin, "wineboot"],
                        env=env,
                        check=True
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"No se pudo crear el prefix: {str(e)}"
                    )
                    return
            else:
                return

        env = self.config_manager.get_current_env(current_config)
        
        all_items = []
        all_types = []
        
        for row in range(self.items_table.rowCount()):
            # Verificar si el elemento está marcado para instalación
            checkbox_item = self.items_table.item(row, 0)
            if checkbox_item.checkState() != Qt.Checked:
                self.items_table.item(row, 3).setText("Omitido")
                continue
                
            item_name = self.items_table.item(row, 1).text()  # Nombre mostrado en la tabla
            item_type = self.items_table.item(row, 2).text().lower()  # "exe" o "winetricks"
            
            # Buscamos el programa en config.json por su nombre
            custom_programs = self.config_manager.get_custom_programs()
            program_info = next((p for p in custom_programs if p['name'] == item_name), None)
            
            if program_info:
                # Usamos el path exacto guardado en config.json
                all_items.append(program_info['path'])
                all_types.append(program_info['type'])
            else:
                # Si no está en custom_programs, es un componente Winetricks seleccionado manualmente
                all_items.append(item_name)
                all_types.append("winetricks")
            
            self.items_table.item(row, 3).setText("Pendiente")

        if all_items:
            self.installer_thread = InstallerThread(
                all_items,
                env,
                item_types=all_types,
                silent_mode=self.silent_mode,
                winetricks_path=self.config_manager.get_winetricks_path(),
                config_manager=self.config_manager
            )
            self.installer_thread.progress.connect(self.update_progress)
            self.installer_thread.finished.connect(self.installation_finished)
            self.installer_thread.error.connect(self.show_error)
            self.installer_thread.canceled.connect(self.on_installation_canceled)

            self.install_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.installer_thread.start()

    def update_progress(self, idx, message):
        self.items_table.item(idx, 3).setText(message)

    def on_installation_canceled(self, idx):
        # Actualizar el estado del item en la fila idx a "Cancelado"
        status_item = self.items_table.item(idx, 3)
        if status_item:
            status_item.setText("Cancelado")

    def installation_finished(self):
        # Mostrar mensaje de completado pero NO limpiar la lista
        QMessageBox.information(self, "Completado", "Instalación finalizada. Limpie la lista para instalar nuevos programas.")
        
        # Deshabilitar botones relevantes
        self.install_btn.setEnabled(False)
        self.add_custom_btn.setEnabled(False)
        self.manage_custom_btn.setEnabled(False)
        self.select_components_btn.setEnabled(False)
        
        # Habilitar solo el botón de limpiar
        self.cancel_btn.setEnabled(False)

    def reset_ui(self):
        # Solo deshabilitar los botones de instalación/cancelación
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        # No cambiar el estado de los otros botones aquí

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        # Solo resetear la UI parcialmente
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

    def cancel_installation(self):
        if self.installer_thread and self.installer_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirmar",
                "¿Estás seguro de que deseas cancelar la instalación?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.installer_thread.stop()
                self.installer_thread.wait()
                self.reset_ui()

    def open_winetricks(self):
        try:
            current_config = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_env(current_config)
            
            winetricks_path = self.config_manager.get_winetricks_path()
            
            subprocess.Popen(
                [winetricks_path, "--gui"],
                env=env
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir Winetricks: {str(e)}"
            )

    def open_shell(self):
        try:
            current_config = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_env(current_config)
            subprocess.Popen(["konsole"], env=env)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir la terminal: {str(e)}"
            )
            
    def open_prefix_folder(self):
        try:
            current_config = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config)
            
            if config and "prefix" in config:
                prefix_path = Path(config["prefix"])
                if prefix_path.exists():
                    subprocess.Popen(["xdg-open", str(prefix_path)])
                else:
                    QMessageBox.warning(
                        self,
                        "Advertencia",
                        f"El prefix {config['prefix']} no existe"
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Advertencia",
                    "No hay un prefix configurado"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el directorio: {str(e)}"
            )
    
    def open_explorer(self):
        try:
            current_config = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config)
            
            if config and "prefix" in config:
                prefix_path = Path(config["prefix"])
                if prefix_path.exists():
                    env = self.config_manager.get_current_env(current_config)
                    
                    if config.get("type") == "proton":
                        proton_dir = Path(config["proton_dir"])
                        wine_bin = str(proton_dir / "files/bin/wine")
                    else:
                        wine_dir = config.get("wine_dir")
                        if wine_dir:
                            wine_bin = str(Path(wine_dir) / "bin/wine")
                        else:
                            wine_bin = "wine"
                    
                    subprocess.Popen(
                        [wine_bin, "explorer"],
                        env=env
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Advertencia",
                        f"El prefix {config['prefix']} no existe"
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Advertencia",
                    "No hay un prefix configurado"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el explorer: {str(e)}"
            )
    
    def open_cfgwine(self):
        try:
            current_config = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_env(current_config)
            
            if "WINE" in env:
                wine_bin = env["WINE"]
            else:
                wine_bin = "wine"
            
            subprocess.Popen(
                [wine_bin, "winecfg"],
                env=env
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir cfgwine: {str(e)}"
            )