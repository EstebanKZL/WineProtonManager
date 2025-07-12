import sys
import subprocess
import time
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
    QInputDialog, QRadioButton, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDir, QSize, QUrl, QTimer, QProcess
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QDesktopServices

from config_manager import ConfigManager
from installer_thread import InstallerThread, BackupThread
from downloader import DownloadThread, DecompressionThread, VersionSearchThread
from styles import STYLE_BREEZE, COLOR_BREEZE_PRIMARY
from dialogs import ConfigDialog, CustomProgramDialog, ManageProgramsDialog, SelectGroupsDialog

class InstallationProgressDialog(QDialog):
    def __init__(self, item_name: str, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"Instalando: {item_name}")
        self.config_manager = config_manager
        self.item_name = item_name
        self.setWindowModality(Qt.NonModal) # Cambiado a NonModal
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.label = QLabel(f"Instalando: <b>{self.item_name}</b>")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        self.log_output = QListWidget()
        self.log_output.setSelectionMode(QListWidget.NoSelection)
        self.log_output.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.log_output.setWordWrap(True)
        main_layout.addWidget(self.log_output)

        self.close_button = QPushButton("Cerrar")
        self.close_button.setAutoDefault(False)
        self.close_button.clicked.connect(self.accept)
        # MODIFICACIÓN 1: El botón de cerrar siempre está habilitado en modo NonModal,
        # pero la señal `accepted` solo se emite si el usuario hace clic.
        # El diálogo se puede cerrar normalmente.
        self.close_button.setEnabled(True)

        main_layout.addWidget(self.close_button)
        self.setLayout(main_layout)

    def append_log(self, text: str):
        """Añade una línea al log de salida de la consola."""
        self.log_output.addItem(text)
        self.log_output.scrollToBottom()

    def set_status(self, status_text: str):
        """Actualiza el texto de estado en el diálogo."""
        self.label.setText(f"Estado de la Instalación: <b>{status_text}</b>")

    def closeEvent(self, event):
        """Permite el cierre del diálogo sin detener el hilo de instalación."""
        event.accept() # Siempre aceptar el evento de cierre

# --- Ventana Principal ---
class InstallerApp(QWidget):
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.installer_thread = None
        self.backup_thread = None
        self.installation_progress_dialog = None
        self.backup_progress_dialog = None

        self.items_for_installation: list[dict] = [] # Almacena {name, path, type, current_status}

        # Cargar ajustes de sesión al inicio
        self.silent_mode = self.config_manager.get_silent_install()
        self.force_mode = self.config_manager.get_force_winetricks_install()
        self.ask_for_backup_before_action = self.config_manager.get_ask_for_backup_before_action()

        self.apply_theme_at_startup() # Aplicar el tema global de la app
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self) # Reaplicar estilos a todos los widgets de la ventana principal
        self.setMinimumSize(1000, 700)
        self.update_installation_button_state() # Actualizar estado inicial de botones

    def apply_theme_at_startup(self):
        """Aplica el tema inicial de la aplicación a la QApplication."""
        theme = self.config_manager.get_theme()
        palette = QApplication.palette() # Iniciar con la paleta actual de la app
        style_settings = STYLE_BREEZE

        if theme == "dark":
            palette.setColor(QPalette.Window, style_settings["dark_palette"]["window"])
            palette.setColor(QPalette.WindowText, style_settings["dark_palette"]["window_text"])
            palette.setColor(QPalette.Base, style_settings["dark_palette"]["base"])
            palette.setColor(QPalette.Text, style_settings["dark_palette"]["text"])
            palette.setColor(QPalette.Button, style_settings["dark_palette"]["button"])
            palette.setColor(QPalette.ButtonText, style_settings["dark_palette"]["button_text"])
            palette.setColor(QPalette.Highlight, style_settings["dark_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, style_settings["dark_palette"]["highlight_text"])
            palette.setColor(QPalette.ToolTipBase, style_settings["dark_palette"]["base"])
            palette.setColor(QPalette.ToolTipText, style_settings["dark_palette"]["text"])
        else:
            palette.setColor(QPalette.Window, style_settings["light_palette"]["window"])
            palette.setColor(QPalette.WindowText, style_settings["light_palette"]["window_text"])
            palette.setColor(QPalette.Base, style_settings["light_palette"]["base"])
            palette.setColor(QPalette.Text, style_settings["light_palette"]["text"])
            palette.setColor(QPalette.Button, style_settings["light_palette"]["button"])
            palette.setColor(QPalette.ButtonText, style_settings["light_palette"]["button_text"])
            palette.setColor(QPalette.Highlight, style_settings["light_palette"]["highlight"])
            palette.setColor(QPalette.HighlightedText, style_settings["light_palette"]["highlight_text"])
            palette.setColor(QPalette.ToolTipBase, style_settings["light_palette"]["base"])
            palette.setColor(QPalette.ToolTipText, style_settings["light_palette"]["text"])

        QApplication.setPalette(palette)
        # La fuente de QApplication ya se establece en el main, no es necesario aquí.

    def setup_ui(self):
        """Configura la interfaz de usuario de la ventana principal."""
        self.setWindowTitle("WineProton Manager")
        self.resize(self.config_manager.get_window_size())
        self.setWindowIcon(QIcon.fromTheme("wine")) # Icono desde el tema del sistema

        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QHBoxLayout(content)

        content_layout.addWidget(self.create_left_panel(), 1) # Panel izquierdo, más pequeño
        content_layout.addWidget(self.create_right_panel(), 2) # Panel derecho, más grande
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def create_left_panel(self) -> QWidget:
        """Crea y devuelve el panel izquierdo de la interfaz."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Grupo de Configuración del Entorno Actual
        config_group = QGroupBox("Configuración del Entorno Actual")
        config_layout = QVBoxLayout()
        self.lbl_config = QLabel()
        self.lbl_config.setWordWrap(True)
        self.update_config_info() # Cargar info al inicio

        self.btn_manage_environments = QPushButton("Gestionar Entornos")
        self.btn_manage_environments.setAutoDefault(False)
        self.btn_manage_environments.clicked.connect(self.configure_environments)
        config_layout.addWidget(self.lbl_config)
        config_layout.addWidget(self.btn_manage_environments)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Grupo de Acciones de Instalación
        actions_group = QGroupBox("Acciones de Instalación")
        actions_layout = QVBoxLayout()

        # Subgrupo de Componentes de Winetricks
        components_group = QGroupBox("Componentes de Winetricks")
        components_layout = QVBoxLayout()
        self.btn_select_components = QPushButton("Seleccionar Componentes de Winetricks")
        self.btn_select_components.setAutoDefault(False)
        self.btn_select_components.clicked.connect(self.select_components)
        components_layout.addWidget(self.btn_select_components)
        components_group.setLayout(components_layout)
        actions_layout.addWidget(components_group)

        # Subgrupo de Programas Personalizados
        custom_group = QGroupBox("Programas Personalizados")
        custom_layout = QVBoxLayout()
        self.btn_add_custom = QPushButton("Añadir Programa/Script")
        self.btn_add_custom.setAutoDefault(False)
        self.btn_add_custom.clicked.connect(self.add_custom_program)
        custom_layout.addWidget(self.btn_add_custom)

        self.btn_manage_custom = QPushButton("Cargar/Eliminar Programas Guardados")
        self.btn_manage_custom.setAutoDefault(False)
        self.btn_manage_custom.clicked.connect(self.manage_custom_programs)
        custom_layout.addWidget(self.btn_manage_custom)
        custom_group.setLayout(custom_layout)
        actions_layout.addWidget(custom_group)

        # Subgrupo de Opciones de Instalación
        options_group = QGroupBox("Opciones de Instalación")
        options_layout = QVBoxLayout()
        self.checkbox_silent_session = QCheckBox("Habilitar modo silencioso para esta instalación Winetricks (-q)")
        self.checkbox_silent_session.setChecked(self.silent_mode)
        self.checkbox_silent_session.stateChanged.connect(self.update_silent_mode_session)
        options_layout.addWidget(self.checkbox_silent_session)

        self.checkbox_force_winetricks_session = QCheckBox("Forzar instalación de Winetricks para esta instalación (--force)")
        self.checkbox_force_winetricks_session.setChecked(self.force_mode)
        self.checkbox_force_winetricks_session.stateChanged.connect(self.update_force_mode_session)
        options_layout.addWidget(self.checkbox_force_winetricks_session)

        options_group.setLayout(options_layout)
        actions_layout.addWidget(options_group)

        # Botones de iniciar/cancelar instalación
        self.btn_install = QPushButton("Iniciar Instalación")
        self.btn_install.setAutoDefault(False)
        self.btn_install.clicked.connect(self.start_installation)
        self.btn_install.setEnabled(False) # Deshabilitado hasta que haya ítems

        self.btn_cancel = QPushButton("Cancelar Instalación")
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.clicked.connect(self.cancel_installation)
        self.btn_cancel.setEnabled(False) # Deshabilitado hasta que haya una instalación en curso

        actions_layout.addWidget(self.btn_install)
        actions_layout.addWidget(self.btn_cancel)

        # Grupo de Herramientas del Prefijo
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

        self.backup_prefix_button = QPushButton("Backup Prefijo")
        self.backup_prefix_button.setAutoDefault(False)
        self.backup_prefix_button.clicked.connect(self.perform_backup)
        left_column.addWidget(self.backup_prefix_button)

        right_column = QVBoxLayout()
        self.btn_winetricks_gui = QPushButton("Winetricks GUI")
        self.btn_winetricks_gui.setAutoDefault(False)
        self.btn_winetricks_gui.clicked.connect(self.open_winetricks)
        right_column.addWidget(self.btn_winetricks_gui)

        self.btn_winecfg = QPushButton("Winecfg")
        self.btn_winecfg.setAutoDefault(False)
        self.btn_winecfg.clicked.connect(self.open_winecfg)
        right_column.addWidget(self.btn_winecfg)

        self.btn_explorer = QPushButton("Explorer")
        self.btn_explorer.setAutoDefault(False)
        self.btn_explorer.clicked.connect(self.open_explorer)
        right_column.addWidget(self.btn_explorer)

        tools_layout.addLayout(left_column)
        tools_layout.addLayout(right_column)
        tools_group.setLayout(tools_layout)
        actions_layout.addWidget(tools_group)

        actions_layout.addStretch() # Empujar los elementos hacia arriba
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        return panel

    def create_right_panel(self) -> QWidget:
        """Crea y devuelve el panel derecho (lista de instalación)."""
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
        self.items_table.verticalHeader().setVisible(False) # Ocultar los números de fila
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows) # Seleccionar filas completas
        self.items_table.setSelectionMode(QTableWidget.SingleSelection) # Permitir solo una selección para mover
        self.items_table.itemChanged.connect(self.on_table_item_changed) # Conectar para manejar el checkbox
        layout.addWidget(self.items_table)

        btn_layout = QHBoxLayout()
        self.btn_clear_list = QPushButton("Limpiar Lista")
        self.btn_clear_list.setAutoDefault(False)
        self.btn_clear_list.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.btn_clear_list)

        self.btn_delete_selection = QPushButton("Eliminar Selección")
        self.btn_delete_selection.setAutoDefault(False)
        self.btn_delete_selection.clicked.connect(self.delete_selected_from_table)
        btn_layout.addWidget(self.btn_delete_selection)

        self.btn_move_up = QPushButton("Mover Arriba")
        self.btn_move_up.setAutoDefault(False)
        self.btn_move_up.clicked.connect(self.move_item_up)
        btn_layout.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("Mover Abajo")
        self.btn_move_down.setAutoDefault(False)
        self.btn_move_down.clicked.connect(self.move_item_down)
        btn_layout.addWidget(self.btn_move_down)

        layout.addLayout(btn_layout)
        return panel

    def on_table_item_changed(self, item: QTableWidgetItem):
        """Maneja los cambios en las casillas de verificación de la tabla y actualiza el estado interno.
           MODIFICACIÓN 1: Al volver a tildar un programa, se restablece a "Pendiente"."""
        # Desconectar temporalmente para evitar llamadas recursivas
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass

        if item.column() == 0: # Si el cambio es en la columna del checkbox
            row = item.row()
            status_item = self.items_table.item(row, 3) # Obtener el ítem de estado

            if status_item:
                if item.checkState() == Qt.Checked:
                    new_status = "Pendiente"
                    status_item.setForeground(QColor(STYLE_BREEZE["dark_palette"]["text"] if self.config_manager.get_theme() == "dark" else STYLE_BREEZE["light_palette"]["text"]))
                else: # Qt.Unchecked
                    new_status = "Omitido"
                    status_item.setForeground(QColor("darkorange"))

                status_item.setText(new_status)
                if 0 <= row < len(self.items_for_installation):
                    self.items_for_installation[row]['current_status'] = new_status
            # else: print(f"DEBUG: El elemento de estado es None para la fila {row}.")

        self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar la señal
        self.update_installation_button_state() # Actualizar estado del botón Instalar

    def update_silent_mode_session(self, state: int):
        """Actualiza el modo silencioso para la sesión actual."""
        self.silent_mode = state == Qt.Checked

    def update_force_mode_session(self, state: int):
        """Actualiza el modo forzado para la sesión actual."""
        self.force_mode = state == Qt.Checked

    def closeEvent(self, event):
        """Guarda el tamaño de la ventana al cerrar."""
        self.config_manager.save_window_size(self.size())
        super().closeEvent(event)

    def configure_environments(self):
        """Abre el diálogo para configurar entornos de Wine/Proton."""
        dialog = ConfigDialog(self.config_manager, self)
        dialog.update_save_settings_button_state()
        dialog.config_saved.connect(self.handle_config_saved_and_restart) # Conectar a la nueva función de reinicio
        dialog.exec_()
        self.update_config_info() # Asegurarse de actualizar la info al cerrar el diálogo

    def handle_config_saved_and_restart(self):
        """
        Maneja la señal de que la configuración ha sido guardada.
        Cierra la aplicación actual y la reinicia.
        """
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)


    def update_config_info(self):
        """Actualiza la información del entorno actual en la GUI."""
        current_config_name = self.config_manager.configs.get("last_used", "Wine-System")
        config = self.config_manager.get_config(current_config_name)

        if not config:
            self.lbl_config.setText("No se ha seleccionado ninguna configuración o la configuración es inválida.")
            return

        try:
            env = self.config_manager.get_current_environment(current_config_name)
            version = env.get("PROTON_VERSION") if config.get("type") == "proton" else env.get("WINE_VERSION", "Desconocida")
            wine_version_in_proton = env.get("WINE_VERSION_IN_PROTON", "N/A")

            # Construir el texto de información con formato HTML
            text = [
                f"<b>Configuración Actual:</b> {current_config_name}",
                f"<b>Tipo:</b> {'Proton' if config.get('type') == 'proton' else 'Wine'}",
                f"<b>Versión Detectada:</b> <span style='color: {COLOR_BREEZE_PRIMARY}; font-weight: bold;'>{version}</span>",
            ]

            if config.get('type') == 'proton':
                text.extend([
                    f"<b>Wine en Proton:</b> <span style='color: {COLOR_BREEZE_PRIMARY}; font-weight: bold;'>{wine_version_in_proton}</span>",
                    f"<b>Directorio de Proton:</b> {config.get('proton_dir', 'No especificado')}"
                ])
                if "steam_appid" in config:
                    text.append(f"<b>APPID de Steam:</b> {config['steam_appid']}")
                    text.append(f"<b>Prefijo gestionado por Steam:</b> Sí")
                else:
                    text.append(f"<b>Prefijo personalizado:</b> Sí")
            else: # Tipo Wine
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
            self.lbl_config.setText(f"ERROR: {str(e)}<br>Por favor, revisa la configuración.")
            QMessageBox.critical(self, "Error de Configuración", str(e))
        except Exception as e:
            self.lbl_config.setText(f"ERROR: No se pudo obtener información de configuración: {str(e)}")

    def add_custom_program(self):
        """Abre el diálogo para añadir un nuevo programa/script personalizado."""
        dialog = CustomProgramDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                program_info = dialog.get_program_info()

                # Evitar duplicados en la lista de instalación actual
                current_paths_in_table = [item['path'] for item in self.items_for_installation]
                if program_info['path'] in current_paths_in_table:
                    QMessageBox.warning(self, "Duplicado", f"El programa '{program_info['name']}' ya está en la lista de instalación.")
                    return

                # Verificar si ya está "instalado" en el prefijo actual (registrado en el log)
                current_config_name = self.config_manager.configs["last_used"]
                config = self.config_manager.get_config(current_config_name)

                installed_items = []
                if config and "prefix" in config:
                    installed_items = self.config_manager.get_installed_winetricks(config["prefix"])

                # Lógica para preguntar si ya está instalado y si aún así desea añadirlo
                already_registered = False
                if program_info["type"] == "winetricks" and program_info["path"] in installed_items:
                    already_registered = True
                elif program_info["type"] == "exe":
                    exe_filename = Path(program_info["path"]).name
                    # La lógica de detección de EXE instalado es básica; podría mejorarse con hashes o nombres más robustos.
                    # Aquí asume que si el nombre del ejecutable está en el .ini, ya está "instalado".
                    if exe_filename in installed_items:
                        already_registered = True
                elif program_info["type"] == "wtr":
                    wtr_filename = Path(program_info["path"]).name

                    if wtr_filename in installed_items: # Esto asume que el nombre del script se registra.
                        already_registered = True

                if already_registered:
                    reply = QMessageBox.question(self, "Programa ya Instalado/Ejecutado",
                                                 f"El programa/componente '{program_info['name']}' ya está registrado como instalado en este prefijo. ¿Deseas agregarlo a la lista de instalación de todos modos?",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.No: return

                self.config_manager.add_custom_program(program_info) # Guardar en la configuración persistente
                self.add_item_to_table(program_info) # Añadir a la tabla de instalación de la UI
                self.update_installation_button_state() # Actualizar estado del botón Instalar

            except ValueError as e:
                QMessageBox.warning(self, "Entrada Inválida", str(e))
            except FileNotFoundError as e:
                QMessageBox.warning(self, "Archivo no Encontrado", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al añadir programa: {str(e)}")

    def add_item_to_table(self, program_data: dict):
        """Añade un elemento a la tabla de instalación."""
        # Desconectar temporalmente para evitar on_table_item_changed inesperadas
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass

        row_count = self.items_table.rowCount()
        self.items_table.insertRow(row_count)

        # Columna 0: Checkbox
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checkbox_item.setCheckState(Qt.Checked) # Por defecto marcado para instalar
        self.items_table.setItem(row_count, 0, checkbox_item)

        # Columna 1: Nombre
        name_item = QTableWidgetItem(program_data["name"])
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable) # No editable
        self.items_table.setItem(row_count, 1, name_item)

        # Columna 2: Tipo
        type_text = program_data["type"].upper()
        type_item = QTableWidgetItem(type_text)
        type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row_count, 2, type_item)

        # Columna 3: Estado
        status_item = QTableWidgetItem("Pendiente")
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row_count, 3, status_item)

        program_data['current_status'] = "Pendiente" # Añadir estado al diccionario interno
        self.items_for_installation.append(program_data) # Añadir al modelo interno

        self.update_installation_button_state()
        # Reconectar la señal
        self.items_table.itemChanged.connect(self.on_table_item_changed)

    def manage_custom_programs(self):
        """Abre el diálogo para gestionar (cargar/eliminar) programas personalizados."""
        dialog = ManageProgramsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted: # Si el diálogo se cerró con "Aceptar"
            selected_programs = dialog.get_selected_programs_to_load()
            for program_info in selected_programs:
                # Añadir solo si no está ya en la lista de instalación actual para evitar duplicados
                if not any(item['path'] == program_info['path'] and item['type'] == program_info['type'] for item in self.items_for_installation):
                    self.add_item_to_table(program_info)
            self.update_installation_button_state()

    def select_components(self):
        """Abre el diálogo para seleccionar componentes de Winetricks."""
        # Definición de grupos de componentes de Winetricks
        component_groups = {
            "Librerias de Visual Basic": ["vb2run", "vb3run", "vb4run", "vb5run", "vb6run"],
            "Librerias de Visual Basic C++": [
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
            ],
            "Fuentes": [
                "allfonts", "andale", "arial", "baekmuk", "calibri", "cambria",
                "candara", "cjkfonts", "comicsans", "consolas", "constantia",
                "corbel", "corefonts", "courier", "droid", "eufonts", "fakechinese",
                "fakejapanese", "fakejapanese_ipamona", "fakejapanese_vlgothic",
                "fakekorean", "georgia", "impact", "ipamona", "liberation",
                "lucida", "meiryo", "micross", "opensymbol", "pptfonts",
                "sourcehansans", "tahoma", "takao", "times", "trebuchet",
                "uff", "unifont", "verdana", "vlgothic", "webdings",
                "wenquanyi", "wenquanyizenhei"
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
                # Comprobar si ya está en la lista de instalación
                if any(item.get('path') == comp_name and item.get('type') == 'winetricks' for item in self.items_for_installation):
                    QMessageBox.warning(self, "Duplicado", f"El componente '{comp_name}' ya está en la lista de instalación.")
                    continue

                # Comprobar si ya está registrado como instalado en el prefijo
                if comp_name in installed_components:
                    reply = QMessageBox.question(self, "Componente ya instalado",
                                                 f"El componente '{comp_name}' ya está registrado como instalado en este prefijo. ¿Deseas agregarlo a la lista de instalación de todos modos?",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.No:
                        continue # No añadir si el usuario elige no hacerlo

                # Añadir a la tabla de instalación
                self.add_item_to_table({"name": comp_name, "path": comp_name, "type": "winetricks"})
            self.update_installation_button_state() # Actualizar estado del botón Instalar

    def cancel_installation(self):
        """Detiene la instalación actual."""
        if self.installer_thread and self.installer_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirmar Cancelación",
                "¿Estás seguro de que quieres cancelar la instalación en curso? Esto puede dejar el prefijo en un estado inconsistente.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.installer_thread.stop() # Enviar señal de parada al hilo
                self.installer_thread.wait(5000) # Esperar a que el hilo termine (hasta 5 segundos)
                if self.installer_thread.isRunning():
                    print("Advertencia: El hilo de instalación no terminó a tiempo.")

                QMessageBox.information(self, "Cancelado", "La instalación ha sido cancelada por el usuario.")

                # Actualizar el estado de los ítems en la tabla que aún no han sido procesados o están en curso
                for row, item_data in enumerate(self.items_for_installation):
                    status_item = self.items_table.item(row, 3)
                    checkbox_item = self.items_table.item(row, 0)
                    if item_data['current_status'] == "Instalando":
                        item_data['current_status'] = "Cancelado"
                        if status_item:
                            status_item.setText("Cancelado")
                            status_item.setForeground(QColor("red"))
                        if checkbox_item:
                            checkbox_item.setCheckState(Qt.Checked) # Dejar marcado si se canceló
                    elif item_data['current_status'] == "Pendiente":
                        item_data['current_status'] = "Omitido"
                        if status_item:
                            status_item.setText("Omitido")
                            status_item.setForeground(QColor("darkorange"))
                        if checkbox_item:
                            checkbox_item.setCheckState(Qt.Unchecked) # Desmarcar si se omitió

                if self.installation_progress_dialog:
                    self.installation_progress_dialog.set_status("Cancelado")

                self.installation_finished() # Llamar al manejador de finalización para restablecer la UI
        else:
            QMessageBox.information(self, "Información", "No hay ninguna instalación en progreso para cancelar.")

    def clear_list(self):
        """Borra la tabla y el modelo de datos interno."""
        reply = QMessageBox.question(self, "Confirmar", "¿Estás seguro de que quieres borrar toda la lista de instalación?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Desconectar para evitar que itemChanged se dispare durante la limpieza
            try:
                self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            except TypeError:
                pass

            self.items_table.setRowCount(0) # Limpiar la tabla de la UI
            self.items_for_installation.clear() # Limpiar el modelo de datos interno
            self.update_installation_button_state() # Actualizar estado del botón Instalar

            # Reconectar la señal
            self.items_table.itemChanged.connect(self.on_table_item_changed)

    def delete_selected_from_table(self):
        """Elimina los elementos seleccionados de la tabla y el modelo interno."""
        # Obtener filas seleccionadas y ordenarlas de mayor a menor para evitar problemas de índice al eliminar
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())), reverse=True)

        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron elementos para eliminar.")
            return

        program_names_to_delete = [self.items_table.item(row, 1).text() for row in selected_rows]

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Estás seguro de que quieres eliminar {len(selected_rows)} elemento(s) de la lista de instalación?\n\n" + "\n".join(program_names_to_delete),
                                     QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Desconectar para evitar que itemChanged se dispare durante la eliminación
            try:
                self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            except TypeError:
                pass

            for row in selected_rows:
                if 0 <= row < len(self.items_for_installation):
                    del self.items_for_installation[row] # Eliminar del modelo interno
                self.items_table.removeRow(row) # Eliminar de la tabla de la UI

            self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar
            self.update_installation_button_state()

    def move_item_up(self):
        """Mueve el elemento seleccionado en la tabla una posición hacia arriba."""
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())))

        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Advertencia", "Selecciona solo un elemento para mover.")
            return

        current_row = selected_rows[0]
        if current_row > 0: # Solo si no es la primera fila
            # Desconectar temporalmente para evitar problemas con itemChanged
            try:
                self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            except TypeError:
                pass

            # Intercambiar elementos en la tabla de la UI
            self.swap_table_rows(current_row, current_row - 1)

            # Intercambiar elementos en el modelo interno
            self.items_for_installation[current_row], self.items_for_installation[current_row - 1] = \
                self.items_for_installation[current_row - 1], self.items_for_installation[current_row]

            self.items_table.selectRow(current_row - 1) # Mantener la selección en el ítem movido
            self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar

    def move_item_down(self):
        """Mueve el elemento seleccionado en la tabla una posición hacia abajo."""
        selected_rows = sorted(list(set(index.row() for index in self.items_table.selectedIndexes())))

        if len(selected_rows) != 1:
            QMessageBox.warning(self, "Advertencia", "Selecciona solo un elemento para mover.")
            return

        current_row = selected_rows[0]
        if current_row < self.items_table.rowCount() - 1: # Solo si no es la última fila
            # Desconectar temporalmente
            try:
                self.items_table.itemChanged.disconnect(self.on_table_item_changed)
            except TypeError:
                pass

            # Intercambiar elementos en la tabla de la UI
            self.swap_table_rows(current_row, current_row + 1)

            # Intercambiar elementos en el modelo interno
            self.items_for_installation[current_row], self.items_for_installation[current_row + 1] = \
                self.items_for_installation[current_row + 1], self.items_for_installation[current_row]

            self.items_table.selectRow(current_row + 1) # Mantener la selección
            self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar

    def swap_table_rows(self, row1: int, row2: int):
        """Intercambia dos filas en la tabla."""
        # Se necesita deshabilitar la señal itemChanged antes de llamar a esto
        row1_items = [self.items_table.takeItem(row1, col) for col in range(self.items_table.columnCount())]
        row2_items = [self.items_table.takeItem(row2, col) for col in range(self.items_table.columnCount())]

        for col in range(self.items_table.columnCount()):
            self.items_table.setItem(row2, col, row1_items[col])
            self.items_table.setItem(row1, col, row2_items[col])

    def update_installation_button_state(self):
        """Habilita/deshabilita los botones de acción según el estado de la aplicación."""
        any_checked = False
        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 0).checkState() == Qt.Checked:
                any_checked = True

        is_installer_running = self.installer_thread is not None and self.installer_thread.isRunning()
        is_backup_running = self.backup_thread is not None and self.backup_thread.isRunning()

        # Botones de instalación
        self.btn_install.setEnabled(any_checked and not is_installer_running and not is_backup_running)
        # MODIFICACIÓN 1: El botón de cancelar siempre está habilitado si la instalación está en curso
        self.btn_cancel.setEnabled(is_installer_running)

        can_modify_list = not is_installer_running and not is_backup_running
        self.btn_select_components.setEnabled(can_modify_list)
        self.btn_add_custom.setEnabled(can_modify_list)
        self.btn_manage_custom.setEnabled(can_modify_list)
        self.btn_clear_list.setEnabled(can_modify_list)
        self.btn_delete_selection.setEnabled(can_modify_list)
        self.btn_move_up.setEnabled(can_modify_list)
        self.btn_move_down.setEnabled(can_modify_list)

        can_use_prefix_tools = not is_backup_running
        self.btn_shell.setEnabled(can_use_prefix_tools)
        self.btn_prefix_folder.setEnabled(can_use_prefix_tools)
        self.btn_winetricks_gui.setEnabled(can_use_prefix_tools)
        self.btn_winecfg.setEnabled(can_use_prefix_tools)
        self.btn_explorer.setEnabled(can_use_prefix_tools)
        self.backup_prefix_button.setEnabled(can_use_prefix_tools) # Incluir el botón de backup aquí también

    def start_installation(self):
        """Inicia el proceso de instalación de los elementos seleccionados."""
        # Filtrar solo los elementos que están marcados para instalar
        items_to_process = [
            item_data for row, item_data in enumerate(self.items_for_installation)
            if self.items_table.item(row, 0).checkState() == Qt.Checked
        ]

        if not items_to_process:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron elementos para instalar. Marca los elementos que deseas instalar.")
            return

        for row in range(self.items_table.rowCount()):
            item_data = self.items_for_installation[row]
            checkbox_item = self.items_table.item(row, 0)
            status_item = self.items_table.item(row, 3)

            if checkbox_item.checkState() == Qt.Checked:
                item_data['current_status'] = "Pendiente"
                if status_item:
                    status_item.setText("Pendiente")
                    theme = self.config_manager.get_theme()
                    text_color = STYLE_BREEZE["dark_palette"]["text"] if theme == "dark" else STYLE_BREEZE["light_palette"]["text"]
                    status_item.setForeground(QColor(text_color))
            else:
                item_data['current_status'] = "Omitido"
                if status_item:
                    status_item.setText("Omitido")
                    status_item.setForeground(QColor("darkorange"))


        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_start_installation())
        else:
            self._continue_start_installation()

    def _continue_start_installation(self):
        """Continúa con la instalación después de la posible solicitud de backup."""
        current_config_name = self.config_manager.configs.get("last_used")
        config = self.config_manager.get_config(current_config_name)

        if not config:
            QMessageBox.critical(self, "Error", "No se ha seleccionado ninguna configuración de Wine/Proton o es inválida.")
            return

        items_to_process_data_for_thread = [
            (item_data['path'], item_data['type'], item_data['name'])
            for item_data in self.items_for_installation
            if item_data['current_status'] == "Pendiente"
        ]

        if not items_to_process_data_for_thread:
            QMessageBox.warning(self, "Advertencia", "No hay elementos seleccionados con estado 'Pendiente' para instalar.")
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
                return # No continuar si el usuario no quiere crear el prefijo

        try:
            env = self.config_manager.get_current_environment(current_config_name)
        except Exception as e:
            QMessageBox.critical(self, "Error de Entorno", f"No se pudo configurar el entorno para la instalación:\n{str(e)}")
            return

        # Mostrar diálogo de progreso de instalación
        first_item_name_for_dialog = items_to_process_data_for_thread[0][2] if items_to_process_data_for_thread else "elementos"
        self.installation_progress_dialog = InstallationProgressDialog(first_item_name_for_dialog, self.config_manager, self)

        # Iniciar el hilo de instalación
        self.installer_thread = InstallerThread(
            items_to_process_data_for_thread,
            env,
            silent_mode=self.silent_mode,
            force_mode=self.force_mode,
            winetricks_path=self.config_manager.get_winetricks_path(),
            config_manager=self.config_manager
        )

        # Conectar señales del hilo a slots de la UI
        self.installer_thread.progress.connect(self.update_progress)
        self.installer_thread.finished.connect(self.installation_finished)
        # [MODIFICACIÓN 1] Manejar errores de ítems individualmente, y errores fatales globales.
        self.installer_thread.error.connect(self.show_global_installation_error) # Para errores que detienen todo
        self.installer_thread.item_error.connect(self.show_item_installation_error) # Para errores de ítems que continúan
        self.installer_thread.canceled.connect(self.on_installation_canceled)
        self.installer_thread.console_output.connect(self.installation_progress_dialog.append_log)

        # Deshabilitar botones que modifican la lista o inician nueva instalación
        self.update_installation_button_state()

        # Deshabilitar interacción con checkboxes de la tabla durante la instalación
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass
        for row in range(self.items_table.rowCount()):
            checkbox_item = self.items_table.item(row, 0)
            if checkbox_item:
                checkbox_item.setFlags(checkbox_item.flags() & ~Qt.ItemIsUserCheckable & ~Qt.ItemIsEnabled)
                # Cambiar estado visual del primer ítem a "Instalando" si es Pendiente
                if self.items_for_installation[row]['current_status'] == "Pendiente":
                    self.items_table.item(row, 3).setText("Instalando")
                    self.items_for_installation[row]['current_status'] = "Instalando"
                    self.items_table.item(row, 3).setForeground(QColor("blue"))
        self.items_table.itemChanged.connect(self.on_table_item_changed)

        # MODIFICACIÓN 1: Mostrar el diálogo de progreso después de configurar todo, no bloquear la UI principal
        self.installation_progress_dialog.show()
        self.installer_thread.start()

    def _create_prefix(self, config: dict, config_name: str, prefix_path: Path):
        """Crea un nuevo prefijo de Wine/Proton y lo inicializa con wineboot."""
        prefix_path.mkdir(parents=True, exist_ok=True, mode=0o755)

        # Temporalmente asignar la config para que get_current_environment funcione
        original_configs = self.config_manager.configs.copy()
        temp_configs_dict = {k: v.copy() if isinstance(v, dict) else v for k, v in original_configs.get("configs", {}).items()}
        temp_configs_dict[config_name] = config
        self.config_manager.configs["configs"] = temp_configs_dict
        self.config_manager.configs["last_used"] = config_name

        env = self.config_manager.get_current_environment(config_name)

        wine_executable = env.get("WINE")
        if not wine_executable or not Path(wine_executable).is_file():
            # Restaurar configs antes de levantar el error
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
            process.wait(timeout=60) # Tiempo de espera para wineboot

            self.config_manager.write_to_log("Creación del Prefijo", f"Salida de Wineboot para {config_name}:\n{log_output}")

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "wineboot", output=log_output)

        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception("La inicialización del prefijo de Wine/Proton agotó el tiempo de espera.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"No se pudo inicializar el prefijo de Wine/Proton. Código de salida: {e.returncode}\nSalida: {e.output}")
        finally:
            progress_dialog.close()
            # Asegurarse de restaurar el estado original de configs
            self.config_manager.configs = original_configs
            self.config_manager.save_configs()

    def update_progress(self, name: str, status: str):
        """Actualiza el estado de un elemento en la tabla y en el modelo interno."""
        found_in_model = False
        for item_data in self.items_for_installation:
            if item_data['name'] == name:
                item_data['current_status'] = status
                found_in_model = True
                break

        if self.installation_progress_dialog and self.installation_progress_dialog.isVisible():
            # Actualizar el label principal del diálogo de progreso
            self.installation_progress_dialog.set_status(f"Instalando {name}: {status}")

        # Actualizar el ítem de estado en la tabla
        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 1).text() == name:
                status_item = self.items_table.item(row, 3)
                if status_item:
                    status_item.setText(status)
                    # Colorear según el estado
                    if "Error" in status:
                        status_item.setForeground(QColor(255, 0, 0)) # Rojo
                    elif "Finalizado" in status:
                        status_item.setForeground(QColor(0, 128, 0)) # Verde
                    elif "Omitido" in status:
                        status_item.setForeground(QColor("darkorange")) # Naranja
                    elif "Instalando" in status:
                        status_item.setForeground(QColor("blue")) # Azul
                    else:
                        theme = self.config_manager.get_theme()
                        text_color = STYLE_BREEZE["dark_palette"]["text"] if theme == "dark" else STYLE_BREEZE["light_palette"]["text"]
                        status_item.setForeground(QColor(text_color)) # Color por defecto
                # else: print(f"DEBUG: El elemento de estado es None para la fila {row}, nombre '{name}'.")
                break

    def on_installation_canceled(self, item_name: str):
        """Actualiza el estado de un elemento cuando la instalación es cancelada."""
        for item_data in self.items_for_installation:
            if item_data['name'] == item_name:
                item_data['current_status'] = "Cancelado"
                break

        for row in range(self.items_table.rowCount()):
            if self.items_table.item(row, 1).text() == item_name:
                status_item = self.items_table.item(row, 3)
                checkbox_item = self.items_table.item(row, 0)
                if status_item:
                    status_item.setText("Error") # Marcar como error en la UI al cancelar
                    status_item.setForeground(QColor(255, 0, 0))
                if checkbox_item:
                    checkbox_item.setFlags(checkbox_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled) # Habilitar checkbox
                    checkbox_item.setCheckState(Qt.Checked) # Dejar marcado si se canceló
                break

        if self.installation_progress_dialog:
            self.installation_progress_dialog.set_status("Cancelado")

    def installation_finished(self):
        """
        MODIFICACIÓN 1: Maneja el estado final de la instalación, actualizando la GUI y mostrando un resumen.
        Limpia la lista de selección, pero mantiene los estados de los ítems.
        Los ítems "Finalizado" y "Omitido" se desmarcan. Los "Error" o "Cancelado" se mantienen marcados.
        """
        installed_count = 0
        failed_count = 0
        skipped_count = 0

        # Desconectar temporalmente para evitar problemas de eventos
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass

        for row in range(self.items_table.rowCount()):
            item_data = self.items_for_installation[row]
            current_status = item_data['current_status']
            checkbox_item = self.items_table.item(row, 0)
            status_item = self.items_table.item(row, 3)

            if "Finalizado" in current_status:
                installed_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Unchecked) # Desmarcar
                if status_item:
                    status_item.setForeground(QColor(0, 128, 0)) # Verde
            elif "Error" in current_status or "Cancelado" in current_status:
                failed_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Checked) # Mantener marcado
                if status_item:
                    status_item.setForeground(QColor(255, 0, 0)) # Rojo
            elif "Omitido" in current_status:
                skipped_count += 1
                if checkbox_item:
                    checkbox_item.setCheckState(Qt.Unchecked) # Desmarcar
                if status_item:
                    status_item.setForeground(QColor("darkorange")) # Naranja

            # Re-habilitar los checkboxes para edición después de la instalación
            if checkbox_item:
                checkbox_item.setFlags(checkbox_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

        self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar

        # Restablecer el estado de los botones
        self.update_installation_button_state()

        if self.installation_progress_dialog:
            self.installation_progress_dialog.set_status("Finalizado")

        QMessageBox.information(
            self,
            "Instalación Completada",
            f"Resumen de la Instalación:\n\n"
            f"• Instalado exitosamente: {installed_count}\n"
            f"• Fallido o Cancelado: {failed_count}\n"
            f"• Omitido (no seleccionado inicialmente): {skipped_count}\n\n"
            f"Los elementos se han desmarcado o dejado marcados según el resultado." # Mensaje actualizado
        )
        self.installer_thread = None # Asegurarse de limpiar la referencia al hilo

    def show_global_installation_error(self, message: str):
        """[MODIFICACIÓN 1] Muestra un mensaje de error crítico que detiene *toda* la instalación."""
        if self.installation_progress_dialog:
            self.installation_progress_dialog.append_log(f"ERROR FATAL: {message}")
            self.installation_progress_dialog.set_status("Error Crítico")

        QMessageBox.critical(self, "Error Crítico de Instalación", message + "\nLa instalación se ha detenido.")
        self.update_installation_button_state() # Restablecer botones

        # Re-habilitar los checkboxes para edición
        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass
        for row in range(self.items_table.rowCount()):
            checkbox_item = self.items_table.item(row, 0)
            if checkbox_item:
                checkbox_item.setFlags(checkbox_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        self.items_table.itemChanged.connect(self.on_table_item_changed) # Reconectar

        self.installer_thread = None # Asegurarse de limpiar la referencia al hilo

    def show_item_installation_error(self, item_name: str, error_message: str):
        """[MODIFICACIÓN 1] Maneja errores de ítems individuales (la instalación continúa)."""
        if self.installation_progress_dialog:
            self.installation_progress_dialog.append_log(f"ERROR para '{item_name}': {error_message}")
            # El diálogo de progreso principal seguirá mostrando "Instalando [siguiente item]"

    def _get_backup_destination_path(self, current_config_name: str, source_to_backup: Path, is_full_backup: bool) -> Path | None:
        """
        Determina la ruta de destino correcta para el backup.
        Si is_full_backup es True, creará una subcarpeta con timestamp.
        Si es incremental, intentará usar la ruta del último backup completo para *esa* configuración.
        """
        base_backup_path_for_config = self.config_manager.backup_dir / current_config_name
        base_backup_path_for_config.mkdir(parents=True, exist_ok=True)

        if is_full_backup:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            # El destino final incluye el nombre de la carpeta a copiar (source_to_backup.name)
            return base_backup_path_for_config / f"{source_to_backup.name}_backup_{timestamp}"
        else:
            # Para backup incremental, el destino es la última ruta de backup completo guardada para *esta* configuración.
            last_full_backup_path_str = self.config_manager.get_last_full_backup_path(current_config_name) # MODIFICACIÓN: Pasar config_name
            if last_full_backup_path_str and Path(last_full_backup_path_str).is_dir():
                return Path(last_full_backup_path_str)
            return None # Indicar que no hay un backup completo previo para incremental para esta configuración

    def perform_backup(self):
        """
        Inicia el proceso de backup para el prefijo actual.
        Presenta un diálogo con opciones para backup Rsync (Incremental) o Backup Completo (Nuevo con timestamp).
        """
        current_config_name = self.config_manager.configs.get("last_used")
        config = self.config_manager.get_config(current_config_name)

        if not config or "prefix" not in config:
            QMessageBox.warning(self, "No hay prefijo", "No hay un prefijo de Wine/Proton configurado para hacer backup.")
            return

        source_prefix_path = Path(config["prefix"])
        if config.get("steam_appid"):
            steam_compat_data_root = Path.home() / ".local/share/Steam/steamapps/compatdata"
            source_to_backup = steam_compat_data_root / config["steam_appid"]
        else:
            source_to_backup = source_prefix_path

        if not source_to_backup.exists():
            QMessageBox.warning(self, "Prefijo no existe", f"El directorio de origen para backup '{source_to_backup}' no existe.")
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Opciones de Backup")
        msg_box.setText(f"¿Qué tipo de backup deseas realizar para el prefijo '{source_to_backup.name}' de la configuración '{current_config_name}'?")
        msg_box.setIcon(QMessageBox.Question)

        btn_rsync = msg_box.addButton("Rsync (Incremental)", QMessageBox.ActionRole)
        btn_full_backup = msg_box.addButton("Backup Completo (Nuevo)", QMessageBox.ActionRole)
        btn_cancel = msg_box.addButton("Cancelar", QMessageBox.RejectRole)

        msg_box.setDefaultButton(btn_rsync)
        self.config_manager.apply_breeze_style_to_widget(msg_box)

        msg_box.exec_()

        clicked_button = msg_box.clickedButton()

        if clicked_button == btn_rsync:
            destination_path = self._get_backup_destination_path(current_config_name, source_to_backup, is_full_backup=False)
            if not destination_path or not destination_path.is_dir():
                QMessageBox.warning(self, "No hay Backup Completo Previo",
                                    "No se encontró un backup completo previo para realizar un backup incremental para esta configuración. "
                                    "Por favor, realiza un 'Backup Completo (Nuevo)' primero.")
                return
            self._start_backup_process(source_to_backup, destination_path, is_full_backup=False, config_name=current_config_name, prompt_callback=None) # MODIFICACIÓN: Pasar config_name
        elif clicked_button == btn_full_backup:
            destination_path = self._get_backup_destination_path(current_config_name, source_to_backup, is_full_backup=True)
            self._start_backup_process(source_to_backup, destination_path, is_full_backup=True, config_name=current_config_name, prompt_callback=None) # MODIFICACIÓN: Pasar config_name
        elif clicked_button == btn_cancel:
            QMessageBox.information(self, "Backup Cancelado", "La operación de backup ha sido cancelada.")

    def prompt_for_backup(self, callback_func):
        """
        Muestra un diálogo preguntando si se desea hacer un backup antes de una acción.
        Ahora ofrece las mismas opciones (Rsync/Completo) que el backup manual, sin "Cancelar Acción".
        """
        current_config_name = self.config_manager.configs.get("last_used")
        config = self.config_manager.get_config(current_config_name)

        if not config or "prefix" not in config:
            callback_func() # No hay prefijo, continuar sin backup
            return

        source_prefix_path = Path(config["prefix"])
        if config.get("steam_appid"):
            steam_compat_data_root = Path.home() / ".local/share/Steam/steamapps/compatdata"
            source_to_backup = steam_compat_data_root / config["steam_appid"]
        else:
            source_to_backup = source_prefix_path

        if not source_to_backup.exists():
            callback_func() # Prefijo no existe, continuar sin backup
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Realizar Backup Antes de Continuar")
        msg_box.setText(f"Se recomienda realizar un backup del prefijo '{source_to_backup.name}' de la configuración '{current_config_name}' antes de continuar con la operación.")

        btn_rsync = msg_box.addButton("Rsync (Incremental)", QMessageBox.YesRole)
        btn_full_backup = msg_box.addButton("Backup Completo (Nuevo)", QMessageBox.YesRole)
        btn_no_backup = msg_box.addButton("No hacer Backup y Continuar", QMessageBox.NoRole)

        msg_box.setDefaultButton(btn_rsync)
        self.config_manager.apply_breeze_style_to_widget(msg_box)

        msg_box.exec_()

        clicked_button = msg_box.clickedButton()

        if clicked_button == btn_rsync:
            destination_path = self._get_backup_destination_path(current_config_name, source_to_backup, is_full_backup=False)
            if not destination_path or not destination_path.is_dir():
                QMessageBox.warning(self, "No hay Backup Completo Previo",
                                    "No se encontró un backup completo previo para realizar un backup incremental para esta configuración. "
                                    "Por favor, realiza un 'Backup Completo (Nuevo)' primero o selecciona 'No hacer Backup y Continuar'.")
                callback_func() # Continuar con la acción original si el rsync no es posible
                return
            self._start_backup_process(source_to_backup, destination_path, is_full_backup=False, config_name=current_config_name, prompt_callback=callback_func) # MODIFICACIÓN: Pasar config_name
        elif clicked_button == btn_full_backup:
            destination_path = self._get_backup_destination_path(current_config_name, source_to_backup, is_full_backup=True)
            self._start_backup_process(source_to_backup, destination_path, is_full_backup=True, config_name=current_config_name, prompt_callback=callback_func) # MODIFICACIÓN: Pasar config_name
        elif clicked_button == btn_no_backup:
            callback_func() # Continuar con la operación original sin backup

    def _start_backup_process(self, source_to_backup: Path, destination_path: Path, is_full_backup: bool, config_name: str, prompt_callback=None): # MODIFICACIÓN: Añadir config_name
        """Método auxiliar para iniciar el hilo de backup."""
        self.backup_progress_dialog = QProgressDialog("Preparando backup...", "", 0, 100, self)
        self.backup_progress_dialog.setWindowTitle("Progreso del Backup")
        self.backup_progress_dialog.setWindowModality(Qt.WindowModal)
        self.backup_progress_dialog.setCancelButton(None)
        self.backup_progress_dialog.setRange(0, 0)
        self.backup_progress_dialog.setFixedSize(450, 150)
        self.config_manager.apply_breeze_style_to_widget(self.backup_progress_dialog)
        self.backup_progress_dialog.show()

        self.backup_thread = BackupThread(source_to_backup, destination_path, self.config_manager, is_full_backup, config_name) # MODIFICACIÓN: Pasar config_name
        self.backup_thread.progress_update.connect(self.update_backup_progress_dialog)
        if prompt_callback:
            # MODIFICACIÓN: Ajustar el lambda para recibir el nuevo parámetro config_name
            self.backup_thread.finished.connect(lambda success, msg, path, current_conf_name: self.on_prompted_backup_finished(success, msg, path, current_conf_name, prompt_callback))
        else:
            # MODIFICACIÓN: Ajustar el lambda para recibir el nuevo parámetro config_name
            self.backup_thread.finished.connect(lambda success, msg, path, current_conf_name: self.on_manual_backup_finished(success, msg, path, current_conf_name))
        self.backup_thread.start()
        self.update_installation_button_state()

    def on_prompted_backup_finished(self, success: bool, message: str, final_backup_path: str, config_name: str, callback_func): # MODIFICACIÓN: Añadir config_name
        """Callback para backups iniciados por un prompt."""
        self.backup_progress_dialog.close()
        self.backup_thread = None
        self.update_installation_button_state()

        if success:
            QMessageBox.information(self, "Backup Completo", message)
            callback_func()
        else:
            reply = QMessageBox.question(self, "Backup Fallido",
                                         f"{message}\n\n¿Deseas continuar con la operación original a pesar de que el backup falló?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                callback_func()
            else:
                QMessageBox.information(self, "Operación Cancelada", "La operación ha sido cancelada debido a un error en el backup.")

    def update_backup_progress_dialog(self, message: str):
        """Actualiza el progreso del diálogo de backup."""
        self.backup_progress_dialog.setLabelText(f"Backup en progreso...\n{message}")
        QApplication.processEvents()

    def on_manual_backup_finished(self, success: bool, message: str, final_backup_path: str, config_name: str): # MODIFICACIÓN: Añadir config_name
        """Callback para backups iniciados por el botón manual."""
        self.backup_progress_dialog.close()
        self.backup_thread = None
        self.update_installation_button_state()
        if success:
            QMessageBox.information(self, "Backup Completo", message)
        else:
            QMessageBox.critical(self, "Error de Backup", message)

    def open_winetricks(self):
        """Abre la GUI de Winetricks para el prefijo actual."""
        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_open_winetricks())
        else:
            self._continue_open_winetricks()

    def _continue_open_winetricks(self):
        """Abre la GUI de Winetricks para el prefijo actual."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            winetricks_path = self.config_manager.get_winetricks_path()

            # Esto se ejecuta en un subproceso no bloqueante
            subprocess.Popen([winetricks_path, "--gui"], env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) # Redirigir salida a DEVNULL
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Winetricks: {str(e)}")

    def open_shell(self):
        """Abre una terminal (Konsole) con el entorno de Wine/Proton configurado."""
        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_open_shell())
        else:
            self._continue_open_shell()

    def _continue_open_shell(self):
        """Continúa abriendo la terminal después de la posible solicitud de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            # Abre Konsole, heredando el entorno. Puede ser 'xterm', 'gnome-terminal', etc.
            subprocess.Popen(["konsole"], env=env)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la terminal: {str(e)}")

    def open_prefix_folder(self):
        """Abre la carpeta del prefijo de Wine/Proton en el explorador de archivos."""
        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_open_prefix_folder())
        else:
            self._continue_open_prefix_folder()

    def _continue_open_prefix_folder(self):
        """Continúa abriendo la carpeta del prefijo después de la posible solicitud de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config_name)

            if config and "prefix" in config:
                prefix_path = Path(config["prefix"])
                if prefix_path.exists():
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(prefix_path)))
                else:
                    QMessageBox.warning(self, "Advertencia", f"El prefijo '{prefix_path}' no existe. Por favor, asegúrate de que esté configurado o créalo.")
            else:
                QMessageBox.warning(self, "Advertencia", "No hay ningún prefijo configurado para el entorno actual.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la carpeta del prefijo: {str(e)}")

    def open_explorer(self):
        """Ejecuta wine explorer para el prefijo actual."""
        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_open_explorer())
        else:
            self._continue_open_explorer()

    def _continue_open_explorer(self):
        """Continúa abriendo el explorador de Wine después de la posible solicitud de backup."""
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

                    subprocess.Popen([wine_executable, "explorer"], env=env,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    QMessageBox.warning(self, "Advertencia", f"El prefijo '{prefix_path}' no existe. Por favor, asegúrate de que esté configurado o créalo.")
            else:
                QMessageBox.warning(self, "Advertencia", "No hay ningún prefijo configurado para el entorno actual.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el Explorador de Wine: {str(e)}")

    def open_winecfg(self):
        """Ejecuta winecfg para el prefijo actual."""
        if self.config_manager.get_ask_for_backup_before_action():
            self.prompt_for_backup(lambda: self._continue_open_winecfg())
        else:
            self._continue_open_winecfg()

    def _continue_open_winecfg(self):
        """Continúa abriendo winecfg después de la posible solicitud de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)

            wine_executable = env.get("WINE")
            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")

            subprocess.Popen([wine_executable, "winecfg"], env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Winecfg: {str(e)}")