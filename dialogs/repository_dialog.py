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

class RepositoryDialog(QDialog):
    def __init__(self, repo_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Añadir Repositorio {repo_type}")
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
        layout.addRow("Nombre del repositorio:", self.name_edit)
        
        self.url_edit = QLineEdit()
        layout.addRow("URL de la API de GitHub:", self.url_edit)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
        
        self.setLayout(layout)
    
    def get_repository_info(self):
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        
        if not name or not url:
            raise ValueError("Debe especificar un nombre y una URL")
        
        if not url.startswith("https://api.github.com/repos/"):
            raise ValueError("La URL debe ser la API de GitHub (ej: https://api.github.com/repos/usuario/repositorio/releases)")
        
        return name, url