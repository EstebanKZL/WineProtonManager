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

class CustomProgramDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir Programa Personalizado")
        self.setup_ui()
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
        layout = QFormLayout()
        self.name_edit = QLineEdit()
        layout.addRow("Nombre del programa:", self.name_edit)

        self.path_edit = QLineEdit()
        self.path_btn = QPushButton("Examinar...")
        self.path_btn.setAutoDefault(False)
        self.path_btn.clicked.connect(self.browse_program)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.path_btn)
        layout.addRow("Ruta del instalador o comando Winetricks:", path_layout)

        # Botones en dos filas
        buttons_layout = QVBoxLayout()
        
        # Fila 1: Botón OK
        ok_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setAutoDefault(False)
        self.ok_btn.setMinimumWidth(200)
        ok_layout.addWidget(self.ok_btn)
        buttons_layout.addLayout(ok_layout)
        
        # Fila 2: Botón Cancelar
        cancel_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setMinimumWidth(200)
        cancel_layout.addWidget(self.cancel_btn)
        buttons_layout.addLayout(cancel_layout)
        
        # Conectar botones
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        layout.addRow(buttons_layout)
        self.setLayout(layout)

    def browse_program(self):
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Ejecutables (*.exe *.msi);;Todos los archivos (*)")
        dialog.setFilter(QDir.AllEntries | QDir.Hidden)
        
        if hasattr(self, 'last_browse_dir') and self.last_browse_dir:
            dialog.setDirectory(self.last_browse_dir)
        
        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                path = Path(selected[0])
                self.last_browse_dir = str(path.parent)
                self.path_edit.setText(str(path.absolute()))

    def get_program_info(self):
        name = self.name_edit.text().strip()
        path = self.path_edit.text().strip()
        
        if not name:
            raise ValueError("Debe especificar un nombre para el programa")
        
        path_obj = Path(path)
        if path.lower().endswith(('.exe', '.msi')):
            if not path_obj.exists():
                raise FileNotFoundError(f"No se encontró el archivo: {path}")
            program_type = "exe"
            path = str(path_obj.absolute())  # <-- Guardamos ruta absoluta
        else:
            program_type = "winetricks"
            # Para Winetricks, path ya es el nombre del componente (ej: "vcrun6")
        
        return {
            "name": name,
            "path": path,
            "type": program_type
        }