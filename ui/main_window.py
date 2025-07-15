import sys
import shutil
import vdf
import subprocess
import time
import re

from functools import wraps
from pathlib import Path

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QCheckBox, QGroupBox, QScrollArea,
                             QTabWidget, QTableWidget, QHeaderView, QMessageBox,
                             QProgressDialog, QTableWidgetItem, QApplication, QDialog, QComboBox)
from PyQt5.QtCore import Qt, QUrl, QTimer, QProcess
from PyQt5.QtGui import QIcon, QPalette, QColor, QDesktopServices

# Importaciones de tus módulos
from config_manager import ConfigManager
from styles import STYLE_BREEZE, COLOR_BREEZE_PRIMARY # Importa solo lo necesario
from dialogs.config_dialog import ConfigDialog
from dialogs.custom_program_dialog import CustomProgramDialog
from dialogs.manage_programs_dialog import ManageProgramsDialog
from dialogs.select_groups_dialog import SelectGroupsDialog
from dialogs.installation_progress_dialog import InstallationProgressDialog
from threads.installer_thread import InstallerThread
from threads.backup_thread import BackupThread
from threads.protondb_thread import ProtonDBThread

class InstallerApp(QWidget):
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.installer_thread = None
        self.backup_thread = None
        self.installation_progress_dialog = None
        self.backup_progress_dialog = None

        self.steam_root = self._locate_steam_root()
        self.available_proton_versions = []
        self.steam_games_data = {}

        self.worker_threads = []

        self.items_for_installation: list[dict] = []

        self.silent_mode = self.config_manager.get_silent_install()
        self.force_mode = self.config_manager.get_force_winetricks_install()
        self.ask_for_backup_before_action = self.config_manager.get_ask_for_backup_before_action()

        self.apply_theme_at_startup()
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)
        self.setMinimumSize(1000, 700)
        self.update_installation_button_state()

    def apply_theme_at_startup(self):
        """Aplica el tema inicial de la aplicación a la QApplication."""
        theme = self.config_manager.get_theme()
        palette = QApplication.palette() 
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

    def setup_ui(self):
        """Configura la interfaz de usuario de la ventana principal."""
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
        """Crea y devuelve el panel izquierdo de la interfaz."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Grupo de Configuración del Entorno Actual
        config_group = QGroupBox("Configuración del Entorno Actual")
        config_layout = QVBoxLayout()
        self.lbl_config = QLabel()
        self.lbl_config.setWordWrap(True)
        self.update_config_info() 

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
        self.btn_install.setEnabled(False) 

        self.btn_cancel = QPushButton("Cancelar Instalación")
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.clicked.connect(self.cancel_installation)
        self.btn_cancel.setEnabled(False) 

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

        actions_layout.addStretch() 
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        return panel

    def create_right_panel(self) -> QWidget:
        """Crea el panel derecho con pestañas para la lista de instalación y juegos de Steam."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.right_tabs = QTabWidget()
        self.config_manager.apply_breeze_style_to_widget(self.right_tabs)

        # Pestaña 1: Lista de Instalación (con nuevo diseño de QGroupBox)
        install_group_box = QGroupBox("Lista de Elementos a Instalar")
        install_layout = QVBoxLayout(install_group_box)
        install_layout.setContentsMargins(10, 10, 10, 10)

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
        install_layout.addWidget(self.items_table)

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
        install_layout.addLayout(btn_layout)
        
        install_tab_page = QWidget()
        install_page_layout = QVBoxLayout(install_tab_page)
        install_page_layout.setContentsMargins(10, 10, 10, 10)
        install_page_layout.addWidget(install_group_box)

        # --- Pestaña 2: Juegos de Steam ---
        steam_tab_page = QWidget()
        steam_page_layout = QVBoxLayout(steam_tab_page)
        steam_page_layout.setContentsMargins(10, 10, 10, 10)

        steam_group_box = self.create_steam_games_panel()
        steam_page_layout.addWidget(steam_group_box)

        self.right_tabs.addTab(install_tab_page, "Lista de Instalación")
        self.right_tabs.addTab(steam_tab_page, "Juegos de Steam")

        layout.addWidget(self.right_tabs)
        return panel

    def _convert_to_unsigned(self, signed_id: int) -> int:
        """Convierte un AppID de 32 bits con signo a su equivalente positivo."""
        return signed_id & 0xffffffff

    def create_steam_games_panel(self) -> QWidget:
        """
        Crea el panel de Juegos de Steam, con la columna APPID oculta,
        botón para aplicar cambios y sin números de fila.
        """
        panel_group = QGroupBox("Juegos de Steam Detectados")
        layout = QVBoxLayout(panel_group)
        layout.setContentsMargins(10, 5, 10, 10)
        
        top_button_layout = QHBoxLayout()
        self.btn_load_steam_games = QPushButton("Cargar Juegos de Steam")
        self.btn_load_steam_games.setAutoDefault(False)
        self.btn_load_steam_games.clicked.connect(self._load_steam_games)
        top_button_layout.addWidget(self.btn_load_steam_games)

        self.btn_apply_steam_changes = QPushButton("Aplicar Cambios de Proton")
        self.btn_apply_steam_changes.setAutoDefault(False)
        self.btn_apply_steam_changes.clicked.connect(self._apply_steam_proton_changes)
        self.btn_apply_steam_changes.setEnabled(False) 
        top_button_layout.addWidget(self.btn_apply_steam_changes)
        layout.addLayout(top_button_layout)

        self.steam_status_label = QLabel("Presiona 'Cargar Juegos de Steam' para empezar.")
        self.steam_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.steam_status_label)

        self.steam_games_table = QTableWidget()
        self.steam_games_table.setColumnCount(4)

        self.steam_games_table.setHorizontalHeaderLabels(["Juego", "APPID", "Versión de Proton", "ProtonDB"])
        self.steam_games_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.steam_games_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.steam_games_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.steam_games_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.steam_games_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.steam_games_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.steam_games_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.steam_games_table)

        self.config_manager.apply_breeze_style_to_widget(panel_group)

        return panel_group

    def _apply_steam_proton_changes(self):
        """
        Recopila los cambios de versión de Proton, pide confirmación,
        cierra Steam, aplica los cambios y fuerza el reinicio de Steam.
        """
        if not self.steam_root:
            QMessageBox.critical(self, "Error", "No se puede aplicar cambios, el directorio de Steam no fue encontrado.")
            return

        changes_to_apply = {}
        for row in range(self.steam_games_table.rowCount()):

            combo_box = self.steam_games_table.cellWidget(row, 2)
            appid = combo_box.property("appid")

            original_tool = self.steam_games_data.get(appid, {}).get('original_tool')
            current_tool = combo_box.currentText()

            if original_tool != current_tool:
                game_name = self.steam_games_table.item(row, 0).text()
                changes_to_apply[appid] = {
                    "name": game_name,
                    "new_tool": current_tool,
                    "old_tool": original_tool
                }

        if not changes_to_apply:
            QMessageBox.information(self, "Sin Cambios", "No se han detectado cambios en las versiones de Proton seleccionadas.")
            return

        summary_text = f"Se van a aplicar {len(changes_to_apply)} cambio(s) en la configuración de Proton."

        confirm_dialog = QMessageBox(self)
        confirm_dialog.setWindowTitle("Confirmar Cambios de Proton")
        confirm_dialog.setText("<b>¡Atención!</b> Para aplicar estos cambios, es necesario cerrar Steam.")
        confirm_dialog.setInformativeText(summary_text)
        confirm_dialog.setIcon(QMessageBox.Warning)

        btn_proceed = confirm_dialog.addButton("Cerrar Steam y Continuar", QMessageBox.AcceptRole)
        btn_cancel = confirm_dialog.addButton("Cancelar", QMessageBox.RejectRole)
        confirm_dialog.setDefaultButton(btn_proceed)
        self.config_manager.apply_breeze_style_to_widget(confirm_dialog)
        confirm_dialog.exec_()

        if confirm_dialog.clickedButton() == btn_cancel:
            QMessageBox.information(self, "Cancelado", "La operación ha sido cancelada.")
            return

        wait_dialog = QMessageBox(self)
        wait_dialog.setWindowTitle("Esperando Cierre de Steam")
        wait_dialog.setIcon(QMessageBox.Information)

        try:
            subprocess.Popen(["steam", "-shutdown"])
            wait_dialog.setText("Se ha enviado la orden de cierre a Steam.\n\n"
                        "Por favor, espera a que Steam se cierre por completo.")
        except FileNotFoundError:
            wait_dialog.setText("No se pudo enviar la orden de cierre automática.\n\n"
                        "Por favor, cierra Steam manualmente.")

        wait_dialog.setInformativeText("Una vez que el icono de Steam desaparezca, presiona 'Aplicar Cambios' para continuar.")
        wait_dialog.addButton("Aplicar Cambios", QMessageBox.AcceptRole)
        self.config_manager.apply_breeze_style_to_widget(wait_dialog)
        wait_dialog.exec_()

        all_success = True
        for appid, change in changes_to_apply.items():
            if not self._save_steam_config(appid, change["new_tool"]):
                QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar la configuración para el juego {change['name']}. Se ha restaurado un backup del archivo de configuración.")
                all_success = False
                break

        if all_success:
            QMessageBox.information(self, "Cambios Aplicados", "¡Éxito! Los cambios han sido aplicados.\n\nSe intentará reiniciar Steam ahora.")

            try:
                subprocess.Popen(["steam"])
            except FileNotFoundError:
                QMessageBox.warning(self, "Error al reiniciar", "No se pudo reiniciar Steam automáticamente. Por favor, inícialo manually.")

            self._load_steam_games()
        else:
            self._load_steam_games()

    def _locate_steam_root(self) -> Path | None:
        """
        Localiza el directorio raíz de Steam, dando prioridad a la ruta guardada en la configuración.
        Si no hay una ruta configurada o no es válida, recurre a la detección automática.
        """
        # Intentar con la ruta de la configuración
        configured_path_str = self.config_manager.get_steam_root_path()
        if configured_path_str:
            configured_path = Path(configured_path_str)
            # Validar que la ruta parece correcta (existe y tiene la carpeta steamapps)
            if configured_path.is_dir() and (configured_path / "steamapps").exists():
                print(f"Usando ruta de Steam configurada: {configured_path}")
                return configured_path

        # Si falla lo anterior, usar la detección automática 
        home = Path.home()
        possible_paths = [
            home / ".steam/steam",
            home / ".local/share/Steam",
            home / ".steam/root"
        ]
        for path in possible_paths:
            if path.exists() and (path / "steamapps").exists():
                print(f"Ruta de Steam detectada automáticamente: {path}")
                return path
        
        print("No se pudo encontrar la ruta de Steam.")
        return None
            
    def _get_available_proton_versions(self) -> list[str]:
        """
        Obtiene la lista de TODAS las herramientas de compatibilidad de Proton disponibles:
        - Versiones personalizadas (GE-Proton) desde 'compatibilitytools.d'.
        - Versiones oficiales de Steam (Proton 8.0, Experimental, etc.) desde los manifiestos.
        """
        if self.available_proton_versions:
            return self.available_proton_versions
        if not self.steam_root:
            return []

        # Usamos un set para manejar automáticamente los duplicados
        versions = {"default"}

        # Buscar versiones personalizadas (como GE-Proton)
        compat_dir = self.steam_root / "compatibilitytools.d"
        if compat_dir.exists():
            for entry in compat_dir.iterdir():
                if entry.is_dir() and (entry / "toolmanifest.vdf").exists():
                    versions.add(entry.name)

        # Buscar versiones oficiales de Steam
        library_folders_vdf_path = self.steam_root / "steamapps/libraryfolders.vdf"
        lib_paths = {self.steam_root} 
        if library_folders_vdf_path.exists():
            try:
                with open(library_folders_vdf_path, 'r', encoding='utf-8') as f:
                    lib_folders_data = vdf.load(f)
                for lib_info in lib_folders_data.get("libraryfolders", {}).values():
                    if "path" in lib_info and Path(lib_info["path"]).exists():
                        lib_paths.add(Path(lib_info["path"]))
            except Exception as e:
                print(f"Advertencia: No se pudo parsear libraryfolders.vdf: {e}")

        for lib_path in lib_paths:
            steamapps_path = lib_path / "steamapps"
            if not steamapps_path.exists():
                continue

            for acf_file in steamapps_path.glob("appmanifest_*.acf"):
                try:
                    with open(acf_file, 'r', encoding='utf-8') as f:
                        app_data = vdf.load(f).get("AppState", {})
                    
                    name = app_data.get("name")
                    if name and "proton" in name.lower():
                        versions.add(name)
                except Exception:
                    continue
        
        # Ordenar la lista de forma "natural" para que las versiones aparezcan correctamente
        sorted_versions = sorted(list(versions), key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('([0-9]+)', s)], reverse=True)

        if 'default' in sorted_versions:
            sorted_versions.remove('default')
            sorted_versions.append('default')

        self.available_proton_versions = sorted_versions
        return self.available_proton_versions

    def _load_steam_games(self):
        """Orquesta la carga de juegos de Steam y Non-Steam en la tabla."""
        self.btn_load_steam_games.setEnabled(False)
        self.btn_load_steam_games.setText("Cargando...")
        self.btn_apply_steam_changes.setEnabled(False)
        QTimer.singleShot(100, self._execute_steam_games_load) # Ejecutar la carga tras actualizar la UI

    def _execute_steam_games_load(self):
        """Realiza la carga real de los juegos de Steam."""
        if not self.steam_root:
            QMessageBox.warning(self, "Steam no encontrado", "No se pudo localizar el directorio raíz de Steam.")
            self.steam_status_label.setText("Error: Directorio raíz de Steam no encontrado.")
            self.btn_load_steam_games.setText("Cargar Juegos de Steam")
            self.btn_load_steam_games.setEnabled(True)
            return

        self.steam_status_label.setText("Buscando juegos en bibliotecas de Steam...")
        self.steam_games_table.setRowCount(0)
        self.steam_games_data.clear()
        processed_appids = set()

        try:
            compat_tools_config, global_tool, lib_paths = self._get_steam_config_data()

            for lib_path in lib_paths:
                self._process_steam_library(lib_path, compat_tools_config, global_tool, processed_appids)

            self._process_non_steam_games(compat_tools_config, global_tool, processed_appids)

        except Exception as e:
            QMessageBox.critical(self, "Error al leer archivos de Steam", f"Ocurrió un error general:\n{e}")

        game_count = self.steam_games_table.rowCount()
        self.steam_status_label.setText(f"Búsqueda completada. {game_count} juegos encontrados.")
        self.btn_apply_steam_changes.setEnabled(game_count > 0)
        self.btn_load_steam_games.setText("Cargar Juegos de Steam")
        self.btn_load_steam_games.setEnabled(True)

    def _get_steam_config_data(self) -> tuple[dict, str | None, set]:
        """Lee y parsea los archivos de configuración de Steam para obtener datos necesarios."""
        config_path = self.steam_root / "config/config.vdf"
        compat_tools_config = {}
        global_default_tool = None
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = vdf.load(f)
            steam_section = config_data.get("InstallConfigStore", {}).get("Software", {}).get("Valve", {}).get("Steam", {})
            compat_tools_config = steam_section.get("CompatToolMapping", {})
            global_default_tool = steam_section.get("DefaultCompatTool")

        lib_paths = {self.steam_root}
        library_folders_path = self.steam_root / "steamapps/libraryfolders.vdf"
        if library_folders_path.exists():
            with open(library_folders_path, 'r', encoding='utf-8') as f:
                lib_folders_data = vdf.load(f)
            for lib_info in lib_folders_data.get("libraryfolders", {}).values():
                if "path" in lib_info and Path(lib_info["path"]).exists():
                    lib_paths.add(Path(lib_info["path"]))
        return compat_tools_config, global_default_tool, lib_paths

    def _process_steam_library(self, lib_path: Path, compat_config: dict, global_tool: str | None, processed_appids: set):
        """Procesa una única biblioteca de Steam, buscando juegos en archivos .acf."""
        steamapps_path = lib_path / "steamapps"
        if not steamapps_path.exists(): return
        
        TOOL_KEYWORDS = ["runtime", "sdk", "redist", "proton", "steamworks"]
        for acf_file in steamapps_path.glob("appmanifest_*.acf"):
            try:
                with open(acf_file, 'r', encoding='utf-8') as f:
                    game_data = vdf.load(f).get("AppState", {})
                
                appid = game_data.get("appid")
                name = game_data.get("name")
                
                if not all([appid, name]) or appid in processed_appids or any(k in name.lower() for k in TOOL_KEYWORDS):
                    continue

                processed_appids.add(appid)
                tool_info = compat_config.get(appid, {})
                tool_name = tool_info.get("name", global_tool or "Nativo/No Proton")
                self._add_game_to_table(appid, name, tool_name, tool_name, is_steam_game=True)
            except Exception:
                continue

    def _process_non_steam_games(self, compat_config: dict, global_tool: str | None, processed_appids: set):
        """Procesa los juegos Non-Steam desde los archivos shortcuts.vdf."""
        userdata_root = self.steam_root / "userdata"
        if not userdata_root.exists(): return

        for user_folder in (d for d in userdata_root.iterdir() if d.is_dir() and d.name != "0"):
            shortcuts_path = user_folder / "config/shortcuts.vdf"
            if not shortcuts_path.exists(): continue
            
            with open(shortcuts_path, "rb") as f:
                shortcuts_data = vdf.binary_load(f)

            for entry_data in shortcuts_data.get('shortcuts', {}).values():
                app_name = entry_data.get('AppName')
                signed_appid = entry_data.get('appid')
                if not app_name or signed_appid is None: continue

                unsigned_appid = str(self._convert_to_unsigned(signed_appid))
                if unsigned_appid in processed_appids: continue

                processed_appids.add(unsigned_appid)
                tool_info = compat_config.get(unsigned_appid, {})
                
                tool_name = tool_info.get("name", global_tool or "Predeterminado de Steam")

                tooltip = f"{app_name}\nRuta: {entry_data.get('Exe', 'N/A')}"
                self._add_game_to_table(unsigned_appid, app_name, tool_name, tool_name, tooltip, is_steam_game=False)

    def _add_game_to_table(self, appid: str, name: str, compat_tool: str, original_tool: str, tooltip: str = "", is_steam_game: bool = True):
        """Añade una fila a la tabla de juegos de Steam."""
        self.steam_games_data[appid] = {'name': name, 'compat_tool': compat_tool, 'original_tool': original_tool}
        row = self.steam_games_table.rowCount()
        self.steam_games_table.insertRow(row)

        name_item = QTableWidgetItem(name)
        name_item.setToolTip(tooltip or name)
        self.steam_games_table.setItem(row, 0, name_item)
        self.steam_games_table.setItem(row, 1, QTableWidgetItem(appid))

        combo_proton = QComboBox()
        versions = self._get_available_proton_versions()
        if compat_tool not in versions:
            combo_proton.insertItem(0, compat_tool)
        combo_proton.addItems(versions)
        combo_proton.setCurrentText(compat_tool)
        combo_proton.setProperty("appid", appid)
        self.steam_games_table.setCellWidget(row, 2, combo_proton)

        status_text = "Cargando..." if is_steam_game else "No aplicable"
        db_status_item = QTableWidgetItem(status_text)
        self.steam_games_table.setItem(row, 3, db_status_item)

        if is_steam_game:
            thread = ProtonDBThread(appid)
            thread.db_status_ready.connect(self._update_protondb_rating)
            thread.finished.connect(lambda t=thread: self.worker_threads.remove(t))
            self.worker_threads.append(thread)
            thread.start()
        
    def _update_protondb_rating(self, appid: str, rating: str):
        """
        Actualiza la celda de estado de ProtonDB y le aplica un color según la calificación.
        """
        # Mapa de calificaciones a colores ---
        tier_colors = {
            "platinum": QColor("#89cff0"),  # 💎 Azul claro (Platino)
            "gold": QColor("#FFD700"),      # 🟡 Dorado
            "silver": QColor("#C0C0C0"),    # ⚪️ Plata
            "bronze": QColor("#CD7F32"),    # 🥉 Bronce
            "borked": QColor("#E34234"),    # 🔴 Rojo (Roto)
            "native": QColor("#7CFC00"),    # 🟢 Verde lima (Nativo)
        }

        for row in range(self.steam_games_table.rowCount()):
            # Buscamos la fila correcta comparando el APPID
            if self.steam_games_table.item(row, 1).text() == appid:
                status_item = self.steam_games_table.item(row, 3)
                if status_item:
                    # Ponemos el texto de la calificación (ej. "Gold")
                    status_item.setText(rating)
                    
                    # Buscamos el color en nuestro diccionario (en minúsculas para asegurar la coincidencia)
                    color = tier_colors.get(rating.lower())
                    
                    if color:
                        # Si encontramos un color, lo aplicamos al texto de la celda
                        status_item.setForeground(color)
                break

    def _parse_shortcuts_vdf(self, path):
        """
        Lee y decodifica el archivo binario shortcuts.vdf, emulando la lógica
        de librerías especializadas para obtener una lista de diccionarios.
        """
        shortcuts = []
        with open(path, 'rb') as f:
            content = f.read()

        import re
        # Buscamos patrones de 'AppName' seguido de su valor y luego 'exe' seguido del suyo
        pattern = re.compile(
            b'\x01AppName\x00(.*?)\x00'  # Captura el nombre de la app
            b'.*?'                     # Caracteres intermedios
            b'\x01exe\x00(.*?)\x00',    # Captura la ruta del ejecutable
            re.DOTALL                  # Permite que '.' incluya saltos de línea
        )

        matches = pattern.findall(content)

        for appname_bytes, exe_bytes in matches:
            try:
                entry = {
                    'appname': appname_bytes.decode('utf-8'),
                    'exe': exe_bytes.decode('utf-8')
                }
                shortcuts.append(entry)
            except UnicodeDecodeError:
                continue

        return shortcuts

    def _update_steam_game_proton_version(self, new_tool_name: str):
        """Se activa cuando el usuario cambia la versión de Proton en un ComboBox."""
        sender_combo = self.sender()
        appid = sender_combo.property("appid")
        if not appid: return

        reply = QMessageBox.question(self, "Confirmar Cambio",
                                     f"¿Estás seguro de que quieres cambiar la versión de Proton para el juego con APPID {appid} a '{new_tool_name}'?\n"
                                     "Esto modificará tu archivo de configuración de Steam.",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self._save_steam_config(appid, new_tool_name):
                QMessageBox.information(self, "Éxito", "La versión de Proton se ha actualizado. Puede que necesites reiniciar Steam para que el cambio surta efecto.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo guardar la configuración de Steam. Se ha restaurado un backup.")
                self._load_steam_games()

    def _vdf_to_dict(self, vdf_text: str) -> dict:
        """
        Parser manual y flexible para leer archivos VDF que no son estricos,
        como los appmanifest.acf.
        """
        root = {}
        stack = [root]
        pattern = re.compile(r'"([^"]+)"\s*(?:"([^"]+)")?')

        for line in vdf_text.splitlines():
            line = line.split('//')[0].strip()
            if not line: continue
            if line == '{': continue
            if line == '}':
                if len(stack) > 1: stack.pop()
                continue

            match = pattern.search(line)
            if match:
                key, value = match.groups()
                current_dict = stack[-1]

                if value is not None:
                    current_dict[key] = value
                else:
                    new_dict = {}
                    current_dict[key] = new_dict
                    stack.append(new_dict)
        return root

    def _save_steam_config(self, appid: str, new_tool_name: str) -> bool:
        """
        Versión final que utiliza 'vdf' para guardar la configuración de forma segura.
        """
        if not self.steam_root: return False

        config_path = self.steam_root / "config/config.vdf"
        backup_path = self.steam_root / "config/config.vdf.wpm_backup"
        if not config_path.exists(): return False

        try:
            shutil.copy(config_path, backup_path)

            # Leer y parsear el archivo con vdf.load()
            full_config_data = {}
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config_data = vdf.load(f)

            # Navegar y modificar el diccionario en memoria
            compat_mapping = full_config_data \
                .setdefault("InstallConfigStore", {}) \
                .setdefault("Software", {}) \
                .setdefault("Valve", {}) \
                .setdefault("Steam", {}) \
                .setdefault("CompatToolMapping", {})

            current_game_mapping = compat_mapping.setdefault(appid, {})
            current_game_mapping["name"] = new_tool_name
            current_game_mapping.setdefault("config", "")

            # Guardar el diccionario modificado con vdf.dump()
            with open(config_path, 'w', encoding='utf-8') as f:
                vdf.dump(full_config_data, f, pretty=True)

            self.steam_compat_tools_config = compat_mapping
            return True

        except Exception as e:
            print(f"Error guardando config.vdf: {e}")
            if backup_path.exists():
                shutil.move(str(backup_path), str(config_path))
            return False
        finally:
            if backup_path.exists():
                backup_path.unlink(missing_ok=True)

    def on_table_item_changed(self, item: QTableWidgetItem):
        """Maneja los cambios en las casillas de verificación de la tabla y actualiza el estado interno.
           Al volver a tildar un programa, se restablece a "Pendiente"."""
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

    def backup_prompt_wrapper(func):
        """
        Decorador para gestionar la lógica de "preguntar por backup" antes de ejecutar una acción
        sobre el prefijo.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 'self' es la instancia de InstallerApp
            if self.config_manager.get_ask_for_backup_before_action():
                # Pasa la función original (vinculada a la instancia) como el callback
                self.prompt_for_backup(lambda: func(self, *args, **kwargs))
            else:
                func(self, *args, **kwargs) # Ejecuta la función directamente si la opción está desactivada
        return wrapper

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
        # El botón de cancelar siempre está habilitado si la instalación está en curso
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
                return

        try:
            env = self.config_manager.get_current_environment(current_config_name)
        except Exception as e:
            QMessageBox.critical(self, "Error de Entorno", f"No se pudo configurar el entorno para la instalación:\n{str(e)}")
            return

        first_item_name_for_dialog = items_to_process_data_for_thread[0][2] if items_to_process_data_for_thread else "elementos"
        self.installation_progress_dialog = InstallationProgressDialog(first_item_name_for_dialog, self.config_manager, self)

        # Iniciar el hilo de instalación
        self.installer_thread = InstallerThread(
            items_to_process_data_for_thread,
            env,
            silent_mode=self.silent_mode,
            force_mode=self.force_mode,
            winetricks_path=self.config_manager.get_winetricks_path(),
            config_manager=self.config_manager,
            config_name=current_config_name 
        )

        # Conectar señales del hilo a slots de la UI
        self.installer_thread.progress.connect(self.update_progress)
        self.installer_thread.finished.connect(self.installation_finished)
        self.installer_thread.error.connect(self.show_global_installation_error)
        self.installer_thread.item_error.connect(self.show_item_installation_error)
        self.installer_thread.canceled.connect(self.on_installation_canceled)
        self.installer_thread.console_output.connect(self.installation_progress_dialog.append_log)

        self.update_installation_button_state()

        try:
            self.items_table.itemChanged.disconnect(self.on_table_item_changed)
        except TypeError:
            pass
        for row in range(self.items_table.rowCount()):
            checkbox_item = self.items_table.item(row, 0)
            if checkbox_item:
                checkbox_item.setFlags(checkbox_item.flags() & ~Qt.ItemIsUserCheckable & ~Qt.ItemIsEnabled)
                if self.items_for_installation[row]['current_status'] == "Pendiente":
                    self.items_table.item(row, 3).setText("Instalando")
                    self.items_for_installation[row]['current_status'] = "Instalando"
                    self.items_table.item(row, 3).setForeground(QColor("blue"))
        self.items_table.itemChanged.connect(self.on_table_item_changed)

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
        Maneja el estado final de la instalación, actualizando la GUI y mostrando un resumen.
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
            f"Los elementos se han desmarcado o dejado marcados según el resultado."
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
        """Maneja errores de ítems individuales (la instalación continúa)."""
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
            last_full_backup_path_str = self.config_manager.get_last_full_backup_path(current_config_name)
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
            self._start_backup_process(source_to_backup, destination_path, is_full_backup=False, config_name=current_config_name, prompt_callback=callback_func) 
        elif clicked_button == btn_full_backup:
            destination_path = self._get_backup_destination_path(current_config_name, source_to_backup, is_full_backup=True)
            self._start_backup_process(source_to_backup, destination_path, is_full_backup=True, config_name=current_config_name, prompt_callback=callback_func) 
        elif clicked_button == btn_no_backup:
            callback_func() # Continuar con la operación original sin backup

    def _start_backup_process(self, source_to_backup: Path, destination_path: Path, is_full_backup: bool, config_name: str, prompt_callback=None): 
        """Método auxiliar para iniciar el hilo de backup."""
        self.backup_progress_dialog = QProgressDialog("Preparando backup...", "", 0, 100, self)
        self.backup_progress_dialog.setWindowTitle("Progreso del Backup")
        self.backup_progress_dialog.setWindowModality(Qt.WindowModal)
        self.backup_progress_dialog.setCancelButton(None)
        self.backup_progress_dialog.setRange(0, 0)
        self.backup_progress_dialog.setFixedSize(450, 150)
        self.config_manager.apply_breeze_style_to_widget(self.backup_progress_dialog)
        self.backup_progress_dialog.show()

        self.backup_thread = BackupThread(source_to_backup, destination_path, self.config_manager, is_full_backup, config_name)
        self.backup_thread.progress_update.connect(self.update_backup_progress_dialog)
        if prompt_callback:

            self.backup_thread.finished.connect(lambda success, msg, path, current_conf_name: self.on_prompted_backup_finished(success, msg, path, current_conf_name, prompt_callback))
        else:

            self.backup_thread.finished.connect(lambda success, msg, path, current_conf_name: self.on_manual_backup_finished(success, msg, path, current_conf_name))
        self.backup_thread.start()
        self.update_installation_button_state()

    def on_prompted_backup_finished(self, success: bool, message: str, final_backup_path: str, config_name: str, callback_func): 
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

    def on_manual_backup_finished(self, success: bool, message: str, final_backup_path: str, config_name: str): 
        """Callback para backups iniciados por el botón manual."""
        self.backup_progress_dialog.close()
        self.backup_thread = None
        self.update_installation_button_state()
        if success:
            QMessageBox.information(self, "Backup Completo", message)
        else:
            QMessageBox.critical(self, "Error de Backup", message)

    def open_winetricks(self):
        """Abre la GUI de Winetricks para el prefijo actual, con manejo de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            winetricks_path = self.config_manager.get_winetricks_path()
            
            subprocess.Popen([winetricks_path, "--gui"], env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir Winetricks: {str(e)}")

    def open_shell(self):
        """Abre una terminal con el entorno de Wine/Proton, con manejo de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            subprocess.Popen(["konsole"], env=env)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la terminal: {str(e)}")

    def open_prefix_folder(self):
        """Abre la carpeta del prefijo en el explorador de archivos, con manejo de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            config = self.config_manager.get_config(current_config_name)

            if config and "prefix" in config:
                prefix_path = Path(config["prefix"])
                if prefix_path.exists():
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(prefix_path)))
                else:
                    QMessageBox.warning(self, "Advertencia", f"El prefijo '{prefix_path}' no existe.")
            else:
                QMessageBox.warning(self, "Advertencia", "No hay ningún prefijo configurado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la carpeta del prefijo: {str(e)}")

    def open_explorer(self):
        """Ejecuta wine explorer para el prefijo actual, con manejo de backup."""
        try:
            current_config_name = self.config_manager.configs["last_used"]
            env = self.config_manager.get_current_environment(current_config_name)
            wine_executable = env.get("WINE")

            if not wine_executable or not Path(wine_executable).is_file():
                raise FileNotFoundError(f"Ejecutable de Wine no encontrado en el entorno: {wine_executable}")

            subprocess.Popen([wine_executable, "explorer"], env=env,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el Explorador de Wine: {str(e)}")

    def open_winecfg(self):
        """Ejecuta winecfg para el prefijo actual, con manejo de backup."""
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
