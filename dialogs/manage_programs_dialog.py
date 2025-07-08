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
from styles import STEAM_DECK_STYLE

class ManageProgramsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Programas Guardados")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.apply_steamdeck_style()
        self.selected_programs = []

    def apply_steamdeck_style(self):
        self.setFont(STEAM_DECK_STYLE["font"])
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(STEAM_DECK_STYLE["font"])
            if isinstance(widget, QGroupBox):
                widget.setFont(STEAM_DECK_STYLE["title_font"])
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STEAM_DECK_STYLE["button_style"])
        
        # Aplicar estilo de tabla según el tema actual
        theme = self.config_manager.get_theme()
        if theme == "dark":
            self.table.setStyleSheet(STEAM_DECK_STYLE["dark_table_style"])
        else:
            self.table.setStyleSheet(STEAM_DECK_STYLE["table_style"])

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)  # Solo 3 columnas ahora
        self.table.setHorizontalHeaderLabels(["Nombre", "Comando", "Tipo"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)  # Cambiado a selección múltiple
        self.load_programs()
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.load_selected_btn = QPushButton("Cargar Selección")
        self.load_selected_btn.setAutoDefault(False)
        self.load_selected_btn.clicked.connect(self.load_selected)
        btn_layout.addWidget(self.load_selected_btn)

        self.delete_btn = QPushButton("Eliminar Selección")
        self.delete_btn.setAutoDefault(False)
        self.delete_btn.clicked.connect(self.delete_programs)
        btn_layout.addWidget(self.delete_btn)

        self.close_btn = QPushButton("Cerrar")
        self.close_btn.setAutoDefault(False)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_programs(self):
        self.table.setRowCount(0)
        programs = self.config_manager.get_custom_programs()
        self.table.setRowCount(len(programs))
        
        for row, program in enumerate(programs):
            name_item = QTableWidgetItem(program['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            path_item = QTableWidgetItem(program['path'])
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, path_item)
            
            type_item = QTableWidgetItem("EXE" if program.get("type") == "exe" else "Winetricks")
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

    def load_selected(self):
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Advertencia", "No hay programas seleccionados")
            return

        programs = self.config_manager.get_custom_programs()
        self.selected_programs = [programs[row] for row in selected_rows]
        self.accept()

    def delete_programs(self):
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        if not selected_rows:
            return

        rows_to_delete = sorted(selected_rows, reverse=True)
        programs = self.config_manager.get_custom_programs()
        programs_to_delete = [programs[row]['name'] for row in rows_to_delete]

        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar los {len(programs_to_delete)} programas seleccionados?",
            QMessageBox.Yes | QMessageBox.No 
        )

        if reply == QMessageBox.Yes:
            success = True
            for program_name in programs_to_delete:
                if not self.config_manager.remove_custom_program(program_name):
                    success = False
            if success:
                self.load_programs()
                QMessageBox.information(self, "Éxito", "Programas eliminados correctamente")
            else:
                QMessageBox.warning(self, "Error", "Algunos programas no pudieron ser eliminados")

    def get_selected_programs(self):
        return self.selected_programs