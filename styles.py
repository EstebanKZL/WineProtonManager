from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

# --- Configuracion de Estilo ---
# Colores centralizados para facil modificacion.
COLOR_PRIMARY = "#3daee9"   # Azul de Steam Deck
COLOR_ACCENT = "#5dbff2"    # Azul mas claro para hover
COLOR_PRESSED = "#2980b9"  # Azul mas oscuro para presionado
COLOR_DISABLED_BG_LIGHT = "#d0d0d0"
COLOR_DISABLED_TEXT_LIGHT = "#9e9e9e"
COLOR_BORDER_LIGHT = "#cccccc"

COLOR_DARK_TEXT = "#FFFFFF"
COLOR_DARK_WINDOW = "#31363b"
COLOR_DARK_WINDOW_TEXT = "#FFFFFF"
COLOR_DARK_BASE = "#232629"
COLOR_DARK_BUTTON = "#40464d"
COLOR_DARK_BUTTON_TEXT = "#FFFFFF"
COLOR_DARK_HIGHLIGHT = "#3daee9" # Tambien Azul de Steam Deck
COLOR_DARK_HIGHLIGHT_TEXT = "#FFFFFF"
COLOR_DARK_BORDER = "#5c636a"

COLOR_LIGHT_WINDOW = "#F7F8F9"
COLOR_LIGHT_WINDOW_TEXT = "#212529"
COLOR_LIGHT_BASE = "#FFFFFF"
COLOR_LIGHT_TEXT = "#212529"
COLOR_LIGHT_BUTTON = "#F7F8F9"
COLOR_LIGHT_BUTTON_TEXT = "#212529"
COLOR_LIGHT_HIGHLIGHT = "#3daee9" # Azul de Steam Deck
COLOR_LIGHT_HIGHLIGHT_TEXT = "#FFFFFF"
COLOR_LIGHT_BORDER = "#BFC4C9"

STYLE_STEAM_DECK = {
    "font": QFont("Noto Sans", 11),
    "title_font": QFont("Noto Sans", 14, QFont.Bold),
    "button_style": f"""
        QPushButton {{
            background-color: {COLOR_PRIMARY};
            color: {COLOR_DARK_TEXT};
            border: 1px solid {COLOR_PRIMARY};
            border-radius: 6px;
            padding: 6px 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_ACCENT};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_DISABLED_BG_LIGHT};
            color: {COLOR_DISABLED_TEXT_LIGHT};
            border: 1px solid {COLOR_BORDER_LIGHT};
        }}
    """,
    "dark_button_style": f"""
        QPushButton {{
            background-color: {COLOR_PRIMARY}; /* Azul tambien en tema oscuro */
            color: {COLOR_DARK_BUTTON_TEXT};
            border: 1px solid {COLOR_PRIMARY}; /* Borde azul tambien en tema oscuro */
            border-radius: 6px;
            padding: 6px 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_ACCENT}; /* Azul mas claro para hover */
        }}
        QPushButton:pressed {{
            background-color: {COLOR_PRESSED}; /* Azul mas oscuro para presionado */
        }}
        QPushButton:disabled {{
            background-color: #555b61; /* Gris para deshabilitado */
            color: #b0b0b0;
            border: 1px solid #6a6f75;
        }}
    """,
    "light_palette": {
        "window": QColor(COLOR_LIGHT_WINDOW),
        "window_text": QColor(COLOR_LIGHT_WINDOW_TEXT),
        "base": QColor(COLOR_LIGHT_BASE),
        "text": QColor(COLOR_LIGHT_TEXT),
        "button": QColor(COLOR_LIGHT_BUTTON),
        "button_text": QColor(COLOR_LIGHT_BUTTON_TEXT),
        "highlight": QColor(COLOR_LIGHT_HIGHLIGHT),
        "highlight_text": Qt.white
    },
    "dark_palette": {
        "window": QColor(COLOR_DARK_WINDOW),
        "window_text": QColor(COLOR_DARK_WINDOW_TEXT),
        "base": QColor(COLOR_DARK_BASE),
        "text": QColor(COLOR_DARK_TEXT),
        "button": QColor(COLOR_DARK_BUTTON),
        "button_text": QColor(COLOR_DARK_BUTTON_TEXT),
        "highlight": QColor(COLOR_DARK_HIGHLIGHT),
        "highlight_text": Qt.white
    },
    "table_style": f"""
        QTableWidget {{
            background-color: {COLOR_LIGHT_BASE};
            alternate-background-color: #f9f9fa;
            gridline-color: #d0d0d0;
            border: 1px solid #c4c9cc;
        }}
        QTableWidget::item {{
            padding: 6px;
        }}
        QTableWidget::item:selected {{
            background-color: {COLOR_PRIMARY};
            color: white;
        }}
        QHeaderView::section {{
            background-color: #f1f3f4;
            padding: 8px;
            border: 1px solid #c4c9cc;
            font-weight: bold;
        }}
    """,
    "dark_table_style": f"""
        QTableWidget {{
            background-color: {COLOR_DARK_WINDOW};
            alternate-background-color: #2b3035;
            gridline-color: #555b61;
            border: 1px solid {COLOR_DARK_BORDER};
        }}
        QTableWidget::item {{
            padding: 6px;
            color: {COLOR_DARK_TEXT};
        }}
        QTableWidget::item:selected {{
            background-color: {COLOR_PRIMARY};
            color: white;
        }}
        QHeaderView::section {{
            background-color: {COLOR_DARK_BUTTON};
            padding: 8px;
            border: 1px solid {COLOR_DARK_BORDER};
            font-weight: bold;
            color: {COLOR_DARK_TEXT};
        }}
    """,
    "groupbox_style": f"""
        QGroupBox {{
            border: 1px solid {COLOR_LIGHT_BORDER};
            border-radius: 6px;
            margin-top: 20px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            font-weight: bold;
            color: {COLOR_LIGHT_WINDOW_TEXT};
        }}
    """,
    "dark_groupbox_style": f"""
        QGroupBox {{
            border: 1px solid {COLOR_DARK_BORDER};
            border-radius: 6px;
            margin-top: 20px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            font-weight: bold;
            color: {COLOR_DARK_TEXT};
        }}
    """
}
