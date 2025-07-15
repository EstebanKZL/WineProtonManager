from PyQt5.QtWidgets import (QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout,
                             QDialogButtonBox, QFileDialog, QWidget)
from PyQt5.QtCore import QDir

from pathlib import Path
from config_manager import ConfigManager

class CustomProgramDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager 
        self.setWindowTitle("Añadir Programa Personalizado")

        self.setFixedSize(650, 140) 
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)

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

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def browse_program(self):
        """Abre un diálogo para seleccionar el programa o script."""
        default_dir = self.config_manager.get_last_browsed_dir("programs")

        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog) 
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Ejecutables de Windows (*.exe *.msi);;Scripts de Winetricks (*.wtr);;Todos los Archivos (*)")
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        dialog.setDirectory(str(default_dir))

        self.config_manager.apply_breeze_style_to_widget(dialog) 

        if dialog.exec_():
            selected_file = dialog.selectedFiles()
            if selected_file:
                self.edit_path.setText(selected_file[0])

                self.config_manager.set_last_browsed_dir("programs", str(Path(selected_file[0]).parent))

    def get_program_info(self) -> dict:
        """Obtiene la información del programa ingresado."""
        name = self.edit_name.text().strip()
        path = self.edit_path.text().strip()

        if not name:
            raise ValueError("Debes especificar un nombre para el programa.")

        program_type = "winetricks" 

        path_obj = Path(path)
        if path.lower().endswith(('.exe', '.msi')):
            if not path_obj.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {path}")
            program_type = "exe"
            path = str(path_obj.absolute()) 
        elif path.lower().endswith('.wtr'):
            if not path_obj.exists():
                raise FileNotFoundError(f"Archivo de script no encontrado: {path}")
            program_type = "wtr"
            path = str(path_obj.absolute()) 
        else:

            program_type = "winetricks"

        return {
            "name": name,
            "path": path, 
            "type": program_type
        }
