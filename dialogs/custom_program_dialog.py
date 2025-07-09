from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QDialogButtonBox, QLabel, QGroupBox, QApplication, QWidget, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from pathlib import Path

from styles import STYLE_STEAM_DECK # Import the style constants
from config_manager import ConfigManager # Corrected import path

class CustomProgramDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Anadir Programa Personalizado")
        self.setup_ui()
        self.apply_steamdeck_style()

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

    def setup_ui(self):
        layout = QFormLayout()
        self.edit_name = QLineEdit()
        layout.addRow("Nombre del Programa:", self.edit_name)

        self.edit_path = QLineEdit()
        self.btn_path = QPushButton("Explorar...")
        self.btn_path.setAutoDefault(False)
        self.btn_path.clicked.connect(self.browse_program)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.edit_path)
        path_layout.addWidget(self.btn_path)
        layout.addRow("Ruta del Instalador o Comando Winetricks:", path_layout)

        # Botones en la misma fila
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        self.setLayout(layout)

    def browse_program(self):
        default_dir = self.config_manager.programs_dir
        
        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        # MODIFICATION START: Changed from QFileDialog.Directory to QFileDialog.ExistingFile
        dialog.setFileMode(QFileDialog.ExistingFile) 
        # MODIFICATION START: Added filters for common executable and script types
        dialog.setNameFilter("Windows Executables (*.exe *.msi);;Winetricks Scripts (*.wtr);;All Files (*)")
        # MODIFICATION END
        dialog.setDirectory(str(default_dir))
        
        # CORRECTED: Call apply_theme_to_dialog from the config_manager
        self.config_manager.apply_theme_to_dialog(dialog)

        if dialog.exec_():
            selected_file = dialog.selectedFiles()
            if selected_file:
                # selected_file[0] will now be the path to the selected file
                self.edit_path.setText(selected_file[0])

    def get_program_info(self) -> dict:
        name = self.edit_name.text().strip()
        path = self.edit_path.text().strip()
        
        if not name:
            raise ValueError("Debes especificar un nombre para el programa.")
            
        program_type = "winetricks" # Valor por defecto
        
        # Determinar el tipo de programa
        path_obj = Path(path)
        if path.lower().endswith(('.exe', '.msi')):
            if not path_obj.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {path}")
            program_type = "exe"
            path = str(path_obj.absolute()) # Asegurar ruta absoluta
        elif path.lower().endswith('.wtr'): # Nuevo tipo: script de winetricks
            if not path_obj.exists():
                raise FileNotFoundError(f"Archivo de script no encontrado: {path}")
            program_type = "wtr"
            path = str(path_obj.absolute())
        else: # Asumir que es un componente de winetricks (ej., vcrun2015)
            program_type = "winetricks"
            # La validacion para componentes de winetricks se realiza al ejecutar winetricks.
            
        return {
            "name": name,
            "path": path,
            "type": program_type
        }
