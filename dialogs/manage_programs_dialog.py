from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout, QMessageBox, QLabel, QGroupBox, QApplication, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from pathlib import Path

from styles import STYLE_STEAM_DECK # Import the style constants
from config_manager import ConfigManager # Corrected import path

class ManageProgramsDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Gestionar Programas Guardados")
        self.setMinimumSize(650, 450)
        self.setup_ui()
        self.apply_steamdeck_style()
        self.selected_programs_to_load = [] # Almacenar programas seleccionados para cargar

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
        
        self.table.setStyleSheet(STYLE_STEAM_DECK["dark_table_style"] if theme == "dark" else STYLE_STEAM_DECK["table_style"])

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nombre", "Comando/Ruta", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.load_programs()
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_load_selected = QPushButton("Cargar Seleccion")
        self.btn_load_selected.setAutoDefault(False)
        self.btn_load_selected.clicked.connect(self.load_selection)
        btn_layout.addWidget(self.btn_load_selected)

        self.btn_delete = QPushButton("Eliminar Seleccion")
        self.btn_delete.setAutoDefault(False)
        self.btn_delete.clicked.connect(self.delete_programs)
        btn_layout.addWidget(self.btn_delete)

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setAutoDefault(False)
        self.btn_close.clicked.connect(self.reject) # Usar reject para cerrar sin cargar
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_programs(self):
        self.table.setRowCount(0)
        programs = self.config_manager.get_custom_programs()
        self.table.setRowCount(len(programs))
        
        for row, program in enumerate(programs):
            name_item = QTableWidgetItem(program.get('name', 'N/A'))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            path_item = QTableWidgetItem(program.get('path', 'N/A'))
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, path_item)
            
            type_text = program.get("type", "winetricks").upper()
            type_item = QTableWidgetItem(type_text) # Mostrar EXE, WINETRICKS, WTR
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

    def load_selection(self):
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())))
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron programas para cargar.")
            return

        all_programs = self.config_manager.get_custom_programs()
        
        # Get current prefix details for checking installed programs
        current_config_name = self.config_manager.configs.get("last_used")
        config = self.config_manager.get_config(current_config_name)
        if not config or "prefix" not in config:
            QMessageBox.critical(self, "Error de Configuración", "No hay un prefijo de Wine/Proton activo para verificar instalaciones.")
            return

        prefix_path = config["prefix"]
        installed_items_in_prefix = self.config_manager.get_installed_winetricks(prefix_path)

        programs_to_add = []
        for row in selected_rows:
            program_info = all_programs[row]
            item_already_installed = False

            if program_info["type"] == "winetricks":
                if program_info["path"] in installed_items_in_prefix:
                    item_already_installed = True
            elif program_info["type"] == "exe":
                exe_filename = Path(program_info["path"]).name
                if exe_filename in installed_items_in_prefix:
                    item_already_installed = True
            elif program_info["type"] == "wtr":
                wtr_filename = Path(program_info["path"]).name
                if wtr_filename in installed_items_in_prefix:
                    item_already_installed = True
            
            if item_already_installed:
                reply = QMessageBox.question(self, "Programa ya Instalado",
                                             f"El programa '{program_info['name']}' ya está registrado como instalado en este prefijo ({current_config_name}). ¿Deseas agregarlo a la lista de instalación de todos modos?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    continue # Skip this program

            programs_to_add.append(program_info)
        
        self.selected_programs_to_load = programs_to_add
        self.accept() # Close the dialog and return ACCEPTED

    def delete_programs(self):
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())), reverse=True)
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron programas para eliminar.")
            return

        program_names_to_delete = [self.table.item(row, 0).text() for row in selected_rows]

        reply = QMessageBox.question(
            self, "Confirmar Eliminacion",
            f"Estas seguro de que quieres eliminar {len(program_names_to_delete)} programa(s) guardado(s)?\n\n" + "\n".join(program_names_to_delete),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count = 0
            for name in program_names_to_delete:
                if self.config_manager.delete_custom_program(name):
                    deleted_count += 1
            
            if deleted_count > 0:
                self.load_programs() # Recargar la tabla despues de la eliminacion
                QMessageBox.information(self, "Exito", f"{deleted_count} programa(s) eliminado(s) exitosamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar ningun programa.")

    def get_selected_programs_to_load(self) -> list[dict]:
        return self.selected_programs_to_load
