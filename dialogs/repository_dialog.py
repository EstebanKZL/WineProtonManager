from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QWidget

from config_manager import ConfigManager

class RepositoryDialog(QDialog):
    def __init__(self, repo_type: str, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.repo_type = repo_type
        self.config_manager = config_manager 
        self.setWindowTitle(f"Añadir Repositorio de {self.repo_type.capitalize()}")
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)

    def setup_ui(self):
        layout = QFormLayout()

        self.edit_name = QLineEdit()
        layout.addRow("Nombre del Repositorio:", self.edit_name)

        self.edit_url = QLineEdit()
        self.edit_url.setPlaceholderText("Ej: https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases")
        layout.addRow("URL de la API de GitHub:", self.edit_url)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def get_repository_info(self) -> tuple[str, str]:
        """Obtiene el nombre y la URL del repositorio ingresados."""
        name = self.edit_name.text().strip()
        url = self.edit_url.text().strip()

        if not name:
            raise ValueError("El nombre del repositorio no puede estar vacío.")
        if not url:
            raise ValueError("La URL de la API de GitHub no puede estar vacía.")
        if not url.startswith("https://api.github.com/repos/"):
            raise ValueError("URL de la API de GitHub inválida. Debe comenzar con 'https://api.github.com/repos/'.")

        return name, url
