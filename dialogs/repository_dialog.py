from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QPushButton, QLabel, QApplication, QWidget
from PyQt5.QtGui import QPalette, QColor
from styles import STYLE_STEAM_DECK # Import the style constants

class RepositoryDialog(QDialog):
    def __init__(self, repo_type: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.repo_type = repo_type
        self.setWindowTitle(f"Anadir Repositorio de {self.repo_type.capitalize()}")
        self.setup_ui()
        self.apply_steamdeck_style()

    def apply_steamdeck_style(self):
        self.setFont(STYLE_STEAM_DECK["font"])
        # Comprobar la paleta de la aplicacion actual para determinar si el tema oscuro esta activo
        # This will be handled by the parent ConfigDialog's apply_theme_to_dialog method now.
        # But we can still ensure internal elements use the correct button/label styles.
        theme_is_dark = QApplication.palette().color(QPalette.Window).name() == QColor(STYLE_STEAM_DECK["dark_palette"]["window"]).name()

        for widget in self.findChildren(QWidget):
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STYLE_STEAM_DECK["dark_button_style"] if theme_is_dark else STYLE_STEAM_DECK["button_style"])
            elif isinstance(widget, QLabel):
                widget.setFont(STYLE_STEAM_DECK["font"])

    def setup_ui(self):
        layout = QFormLayout()

        self.edit_name = QLineEdit()
        layout.addRow("Nombre del Repositorio:", self.edit_name)

        self.edit_url = QLineEdit()
        layout.addRow("URL de la API de GitHub:", self.edit_url)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def get_repository_info(self) -> tuple[str, str]:
        name = self.edit_name.text().strip()
        url = self.edit_url.text().strip()

        if not name:
            raise ValueError("El nombre del repositorio no puede estar vacio.")
        if not url:
            raise ValueError("La URL de la API de GitHub no puede estar vacia.")
        if not url.startswith("https://api.github.com/repos/"):
            raise ValueError("URL de la API de GitHub invalida. Debe comenzar con 'https://api.github.com/repos/'.")

        return name, url
