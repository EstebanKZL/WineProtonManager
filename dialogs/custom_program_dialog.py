from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QFileDialog,
    QDialogButtonBox, QMessageBox, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt, QDir
from config_manager import ConfigManager

class CustomProgramDialog(QDialog):
    def __init__(self, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.config_manager = config_manager # Pasar config_manager para aplicar estilos
        self.setWindowTitle("Añadir Programa Personalizado")
        # MODIFICACIÓN 2: Establecer tamaño fijo
        self.setFixedSize(650, 140) # Establecer un tamaño fijo
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
        # MODIFICACIÓN 4: Usar la última carpeta explorada para programas
        default_dir = self.config_manager.get_last_browsed_dir("programs")

        dialog = QFileDialog(self)
        dialog.setOption(QFileDialog.DontUseNativeDialog) # Usar diálogo nativo de Qt para un control más consistente
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Ejecutables de Windows (*.exe *.msi);;Scripts de Winetricks (*.wtr);;Todos los Archivos (*)")
        dialog.setFilter(QDir.AllEntries | QDir.Hidden | QDir.NoDotAndDotDot)
        dialog.setDirectory(str(default_dir))

        self.config_manager.apply_breeze_style_to_widget(dialog) # Aplicar estilo al diálogo de archivo

        if dialog.exec_():
            selected_file = dialog.selectedFiles()
            if selected_file:
                self.edit_path.setText(selected_file[0])
                # MODIFICACIÓN 4: Guardar la nueva ruta explorada
                self.config_manager.set_last_browsed_dir("programs", str(Path(selected_file[0]).parent))


    def get_program_info(self) -> dict:
        """Obtiene la información del programa ingresado."""
        name = self.edit_name.text().strip()
        path = self.edit_path.text().strip()

        if not name:
            raise ValueError("Debes especificar un nombre para el programa.")

        program_type = "winetricks" # Valor por defecto si no se puede determinar por extensión

        path_obj = Path(path)
        if path.lower().endswith(('.exe', '.msi')):
            if not path_obj.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {path}")
            program_type = "exe"
            path = str(path_obj.absolute()) # Guardar la ruta absoluta
        elif path.lower().endswith('.wtr'):
            if not path_obj.exists():
                raise FileNotFoundError(f"Archivo de script no encontrado: {path}")
            program_type = "wtr"
            path = str(path_obj.absolute()) # Guardar la ruta absoluta
        else:
            # Si no es .exe, .msi o .wtr, se asume que es un comando de winetricks (ej. "vcrun2019")
            program_type = "winetricks"

        return {
            "name": name,
            "path": path, # path puede ser un nombre de componente o una ruta de archivo
            "type": program_type
        }