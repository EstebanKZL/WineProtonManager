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

class SelectGroupsDialog(QDialog):
    def __init__(self, component_groups, parent=None):
        super().__init__(parent)
        self.component_groups = component_groups
        self.setWindowTitle("Seleccionar Componentes")
        self.setMinimumSize(450, 350)
        self.setup_ui()
        self.apply_steamdeck_style()

    def apply_steamdeck_style(self):
        self.setFont(STEAM_DECK_STYLE["font"])
        
        # Estilo único para ambos temas (fondo blanco, texto negro)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #ffffff;
                color: black;
            }
        """)

        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(STEAM_DECK_STYLE["font"])
            if isinstance(widget, QGroupBox):
                widget.setFont(STEAM_DECK_STYLE["title_font"])
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STEAM_DECK_STYLE["button_style"])
                
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Componente", "Descripción"])
        self.tree.setColumnCount(2)
        self.tree.setSelectionMode(QTreeWidget.MultiSelection)
        
        self.component_descriptions = {
            "vb2run": "Visual Basic 2.0 Runtime",
            "vb3run": "Visual Basic 3.0 Runtime",
            "vb4run": "Visual Basic 4.0 Runtime",
            "vb5run": "Visual Basic 5.0 Runtime",
            "vb6run": "Visual Basic 6.0 Runtime",
            "vcrun6": "Visual C++ 6.0 Runtime (SP6 recomendado)",
            "vcrun2005": "Visual C++ 2005 Runtime",
            "vcrun2008": "Visual C++ 2008 Runtime",
            "dotnet40": "Microsoft .NET Framework 4.0",
            "dotnet48": "Microsoft .NET Framework 4.8",
        }
        
        for group_name, components in self.component_groups.items():
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, group_name)
            group_item.setFlags(group_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            
            for comp in components:
                child_item = QTreeWidgetItem(group_item)
                child_item.setText(0, comp)
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.Unchecked)
                
                description = self.component_descriptions.get(comp, "Componente Winetricks estándar")
                child_item.setText(1, description)
        
        self.tree.expandAll()
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.tree)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_selected_components(self):
        selected = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                if child_item.checkState(0) == Qt.Checked:
                    selected.append(child_item.text(0))
        return selected