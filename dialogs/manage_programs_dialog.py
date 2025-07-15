from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QHeaderView, QHBoxLayout,
                             QPushButton, QMessageBox, QTableWidgetItem, QWidget)
from PyQt5.QtCore import Qt

from pathlib import Path
from config_manager import ConfigManager

class ManageProgramsDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager 
        self.setWindowTitle("Gestionar Programas Guardados")
        self.setMinimumSize(650, 450)
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)
        self.selected_programs_to_load = [] 

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
        self.btn_load_selected = QPushButton("Cargar Selección")
        self.btn_load_selected.setAutoDefault(False)
        self.btn_load_selected.clicked.connect(self.load_selection)
        btn_layout.addWidget(self.btn_load_selected)

        self.btn_delete = QPushButton("Eliminar Selección")
        self.btn_delete.setAutoDefault(False)
        self.btn_delete.clicked.connect(self.delete_programs)
        btn_layout.addWidget(self.btn_delete)

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setAutoDefault(False)
        self.btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_programs(self):
        """Carga y muestra la lista de programas personalizados en la tabla."""
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
            type_item = QTableWidgetItem(type_text)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

    def load_selection(self):
        """Carga los programas seleccionados en la lista de instalación principal."""
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())))
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron programas para cargar.")
            return

        all_programs = self.config_manager.get_custom_programs()

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
                    continue 

            programs_to_add.append(program_info)

        self.selected_programs_to_load = programs_to_add
        self.accept() 
        
    def delete_programs(self):
        """Elimina los programas seleccionados de la lista guardada."""
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())), reverse=True)
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No se seleccionaron programas para eliminar.")
            return

        program_names_to_delete = [self.table.item(row, 0).text() for row in selected_rows]

        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar {len(program_names_to_delete)} programa(s) guardado(s)?\n\n" + "\n".join(program_names_to_delete),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count = 0
            for name in program_names_to_delete:
                if self.config_manager.delete_custom_program(name):
                    deleted_count += 1

            if deleted_count > 0:
                self.load_programs()
                QMessageBox.information(self, "Éxito", f"{deleted_count} programa(s) eliminado(s) exitosamente.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar ningún programa.")

    def get_selected_programs_to_load(self) -> list[dict]:
        """Devuelve los programas seleccionados para cargar."""
        return self.selected_programs_to_load
