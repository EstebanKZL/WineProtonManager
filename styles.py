from PyQt5.QtGui import QFont, QColor

# Configuración de Estilo Breeze
COLOR_BREEZE_PRIMARY = "#3daee9"  # Azul Breeze estándar
COLOR_BREEZE_ACCENT = "#5dbff2"   # Azul más claro para efectos de hover y foco
COLOR_BREEZE_PRESSED = "#2980b9"  # Azul más oscuro para estado presionado

# Colores del Tema Claro
COLOR_BREEZE_LIGHT_WINDOW = "#F7F8F9" # Fondo de ventanas
COLOR_BREEZE_LIGHT_WINDOW_TEXT = "#212529" # Color de texto general
COLOR_BREEZE_LIGHT_BASE = "#FFFFFF" # Fondo para widgets (listas, tablas)
COLOR_BREEZE_LIGHT_TEXT = "#212529" # Texto en widgets base
COLOR_BREEZE_LIGHT_BUTTON = "#F0F0F0" # Fondo para botones
COLOR_BREEZE_LIGHT_BUTTON_TEXT = "#212529" # Texto en botones
COLOR_BREEZE_LIGHT_HIGHLIGHT = COLOR_BREEZE_PRIMARY # Color de resaltado
COLOR_BREEZE_LIGHT_HIGHLIGHT_TEXT = "#FFFFFF" # Texto en resaltado
COLOR_BREEZE_LIGHT_BORDER = "#BFC4C9" # Color de borde
COLOR_BREEZE_LIGHT_DISABLED_BG = "#E0E0E0"
COLOR_BREEZE_LIGHT_DISABLED_TEXT = "#A0A0A0"

# Colores del Tema Oscuro
COLOR_BREEZE_DARK_WINDOW = "#2A2E32" # Fondo de ventanas
COLOR_BREEZE_DARK_WINDOW_TEXT = "#D0D0D0" # Color de texto general
COLOR_BREEZE_DARK_BASE = "#31363B" # Fondo para widgets (listas, tablas)
COLOR_BREEZE_DARK_TEXT = "#D0D0D0" # Texto en widgets base
COLOR_BREEZE_DARK_BUTTON = "#3A3F44" # Fondo para botones
COLOR_BREEZE_DARK_BUTTON_TEXT = "#D0D0D0" # Texto en botones
COLOR_BREEZE_DARK_HIGHLIGHT = COLOR_BREEZE_PRIMARY # Color de resaltado
COLOR_BREEZE_DARK_HIGHLIGHT_TEXT = "#FFFFFF" # Texto en resaltado
COLOR_BREEZE_DARK_BORDER = "#5A5F65" # Color de borde
COLOR_BREEZE_DARK_DISABLED_BG = "#4A4F54"
COLOR_BREEZE_DARK_DISABLED_TEXT = "#808080"

STYLE_BREEZE = {
    "font": QFont("Noto Sans", 11),
    "title_font": QFont("Noto Sans", 13, QFont.Bold),
    "light_border": COLOR_BREEZE_LIGHT_BORDER,
    "dark_border": COLOR_BREEZE_DARK_BORDER,
    "button_style": f"""
        QPushButton {{
            background-color: {COLOR_BREEZE_LIGHT_BUTTON};
            color: {COLOR_BREEZE_LIGHT_BUTTON_TEXT};
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
            border-radius: 4px;
            padding: 8px 18px;
            font-size: 13px;
            font-weight: bold;
            outline: none;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BREEZE_PRIMARY};
            color: {COLOR_BREEZE_LIGHT_HIGHLIGHT_TEXT};
            border: 1px solid {COLOR_BREEZE_PRIMARY};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_BREEZE_PRESSED};
            border: 1px solid {COLOR_BREEZE_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BREEZE_LIGHT_DISABLED_BG};
            color: {COLOR_BREEZE_LIGHT_DISABLED_TEXT};
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
        }}
    """,
    "dark_button_style": f"""
        QPushButton {{
            background-color: {COLOR_BREEZE_DARK_BUTTON};
            color: {COLOR_BREEZE_DARK_BUTTON_TEXT};
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
            border-radius: 4px;
            padding: 8px 18px;
            font-size: 14px;
            font-weight: bold;
            outline: none;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BREEZE_PRIMARY};
            color: {COLOR_BREEZE_DARK_HIGHLIGHT_TEXT};
            border: 1px solid {COLOR_BREEZE_PRIMARY};
        }}
        QPushButton:pressed {{
            background-color: {COLOR_BREEZE_PRESSED};
            border: 1px solid {COLOR_BREEZE_PRESSED};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BREEZE_DARK_DISABLED_BG};
            color: {COLOR_BREEZE_DARK_DISABLED_TEXT};
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
        }}
    """,
    "light_palette": {
        "window": QColor(COLOR_BREEZE_LIGHT_WINDOW),
        "window_text": QColor(COLOR_BREEZE_LIGHT_WINDOW_TEXT),
        "base": QColor(COLOR_BREEZE_LIGHT_BASE),
        "text": QColor(COLOR_BREEZE_LIGHT_TEXT),
        "button": QColor(COLOR_BREEZE_LIGHT_BUTTON),
        "button_text": QColor(COLOR_BREEZE_LIGHT_BUTTON_TEXT),
        "highlight": QColor(COLOR_BREEZE_PRIMARY),
        "highlight_text": QColor(COLOR_BREEZE_LIGHT_HIGHLIGHT_TEXT)
    },
    "dark_palette": {
        "window": QColor(COLOR_BREEZE_DARK_WINDOW),
        "window_text": QColor(COLOR_BREEZE_DARK_WINDOW_TEXT),
        "base": QColor(COLOR_BREEZE_DARK_BASE),
        "text": QColor(COLOR_BREEZE_DARK_TEXT),
        "button": QColor(COLOR_BREEZE_DARK_BUTTON),
        "button_text": QColor(COLOR_BREEZE_DARK_BUTTON_TEXT),
        "highlight": QColor(COLOR_BREEZE_PRIMARY),
        "highlight_text": QColor(COLOR_BREEZE_DARK_HIGHLIGHT_TEXT)
    },
    "table_style": f"""
        QTableWidget {{
            background-color: {COLOR_BREEZE_LIGHT_BASE};
            alternate-background-color: {QColor(COLOR_BREEZE_LIGHT_BASE).lighter(105).name()};
            gridline-color: {COLOR_BREEZE_LIGHT_BORDER};
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
            selection-background-color: {COLOR_BREEZE_PRIMARY};
            selection-color: white;
        }}
        QTableWidget::item {{
            padding: 4px;
        }}
        QHeaderView::section {{
            background-color: {QColor(COLOR_BREEZE_LIGHT_WINDOW).lighter(105).name()};
            padding: 6px;
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
            font-weight: bold;
            color: {COLOR_BREEZE_LIGHT_WINDOW_TEXT};
        }}
        QTableCornerButton::section {{
            background-color: {QColor(COLOR_BREEZE_LIGHT_WINDOW).lighter(105).name()};
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
        }}
    """,
    "dark_table_style": f"""
        QTableWidget {{
            background-color: {COLOR_BREEZE_DARK_BASE};
            alternate-background-color: {QColor(COLOR_BREEZE_DARK_BASE).lighter(105).name()};
            gridline-color: {COLOR_BREEZE_DARK_BORDER};
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
            color: {COLOR_BREEZE_DARK_TEXT};
            selection-background-color: {COLOR_BREEZE_PRIMARY};
            selection-color: white;
        }}
        QTableWidget::item {{
            padding: 4px;
        }}
        QHeaderView::section {{
            background-color: {QColor(COLOR_BREEZE_DARK_WINDOW).lighter(105).name()};
            padding: 6px;
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
            font-weight: bold;
            color: {COLOR_BREEZE_DARK_WINDOW_TEXT};
        }}
        QTableCornerButton::section {{
            background-color: {QColor(COLOR_BREEZE_DARK_WINDOW).lighter(105).name()};
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
        }}
    """,
    "groupbox_style": f"""
        QGroupBox {{
            border: 1px solid {COLOR_BREEZE_LIGHT_BORDER};
            border-radius: 4px;
            margin-top: 20px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
            font-weight: bold;
            color: {COLOR_BREEZE_LIGHT_WINDOW_TEXT};
        }}
    """,
    "dark_groupbox_style": f"""
        QGroupBox {{
            border: 1px solid {COLOR_BREEZE_DARK_BORDER};
            border-radius: 4px;
            margin-top: 20px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
            font-weight: bold;
            color: {COLOR_BREEZE_DARK_WINDOW_TEXT};
        }}
    """,
    "list_tree_style_template": """
        QAbstractItemView {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            font-size: {font_size}px;
        }}
        QAbstractItemView::item {{
            padding: 3px;
        }}
        QAbstractItemView::item:selected {{
            background-color: {highlight_color};
            color: {highlight_text_color};
        }}
        QHeaderView::section {{
            background-color: {header_bg_color};
            padding: 6px;
            border: 1px solid {border_color};
            font-weight: bold;
            color: {header_text_color};
        }}
    """,
    # MODIFICACIÓN 3: Estilo para QLineEdit y QComboBox con borde azul agua al enfocar
    "lineedit_combobox_style_template": """
        QLineEdit, QComboBox {{
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 3px;
            padding: 3px;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {accent_color}; /* Borde azul agua al enfocar */
        }}
        QComboBox::drop-down {{
            border: 0px;
        }}
        QComboBox::down-arrow {{
            image: url(no_image_needed);
        }}
    """,
    "checkbox_radiobutton_style_template": """
        QCheckBox {{ color: {text_color}; }}
        QRadioButton {{ color: {text_color}; }}
    """
}

