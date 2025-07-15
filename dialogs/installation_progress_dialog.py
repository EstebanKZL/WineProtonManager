from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QWidget
from PyQt5.QtCore import Qt

from config_manager import ConfigManager

class InstallationProgressDialog(QDialog):
    def __init__(self, item_name: str, config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"Instalando: {item_name}")
        self.config_manager = config_manager
        self.item_name = item_name
        self.setWindowModality(Qt.NonModal) 
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.label = QLabel(f"Instalando: <b>{self.item_name}</b>")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        self.log_output = QListWidget()
        self.log_output.setSelectionMode(QListWidget.NoSelection)
        self.log_output.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.log_output.setWordWrap(True)
        main_layout.addWidget(self.log_output)

        self.close_button = QPushButton("Cerrar")
        self.close_button.setAutoDefault(False)
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(True)

        main_layout.addWidget(self.close_button)
        self.setLayout(main_layout)

    def append_log(self, text: str):
        """Añade una línea al log de salida de la consola."""
        self.log_output.addItem(text)
        self.log_output.scrollToBottom()

    def set_status(self, status_text: str):
        """Actualiza el texto de estado en el diálogo."""
        self.label.setText(f"Estado de la Instalación: <b>{status_text}</b>")

    def closeEvent(self, event):
        """Permite el cierre del diálogo sin detener el hilo de instalación."""
        event.accept() # Siempre aceptar el evento de cierre
