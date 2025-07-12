from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import QWidget, QPushButton, QTableWidget, QGroupBox, QListWidget, QTreeWidget, QLineEdit, QComboBox, QCheckBox, QRadioButton, QApplication

# Colores centralizados para fácil modificación, inspirados en Plasma 6.0 Breeze
COLOR_BREEZE_PRIMARY = "#3daee9"  # Azul Breeze estándar
COLOR_BREEZE_ACCENT = "#5dbff2"   # Azul más claro para efectos de hover y foco
COLOR_BREEZE_PRESSED = "#2980b9"  # Azul más oscuro para estado presionado

# Colores del Tema Claro
COLOR_BREEZE_LIGHT_WINDOW = "#F7F8F9"
COLOR_BREEZE_LIGHT_WINDOW_TEXT = "#212529"
COLOR_BREEZE_LIGHT_BASE = "#FFFFFF"
COLOR_BREEZE_LIGHT_TEXT = "#212529"
COLOR_BREEZE_LIGHT_BUTTON = "#F0F0F0"
COLOR_BREEZE_LIGHT_BUTTON_TEXT = "#212529"
COLOR_BREEZE_LIGHT_HIGHLIGHT = COLOR_BREEZE_PRIMARY
COLOR_BREEZE_LIGHT_HIGHLIGHT_TEXT = "#FFFFFF"
COLOR_BREEZE_LIGHT_BORDER = "#BFC4C9"
COLOR_BREEZE_LIGHT_DISABLED_BG = "#E0E0E0"
COLOR_BREEZE_LIGHT_DISABLED_TEXT = "#A0A0A0"

# Colores del Tema Oscuro
COLOR_BREEZE_DARK_WINDOW = "#2A2E32"
COLOR_BREEZE_DARK_WINDOW_TEXT = "#D0D0D0"
COLOR_BREEZE_DARK_BASE = "#31363B"
COLOR_BREEZE_DARK_TEXT = "#D0D0D0"
COLOR_BREEZE_DARK_BUTTON = "#3A3F44"
COLOR_BREEZE_DARK_BUTTON_TEXT = "#D0D0D0"
COLOR_BREEZE_DARK_HIGHLIGHT = COLOR_BREEZE_PRIMARY
COLOR_BREEZE_DARK_HIGHLIGHT_TEXT = "#FFFFFF"
COLOR_BREEZE_DARK_BORDER = "#5A5F65"
COLOR_BREEZE_DARK_DISABLED_BG = "#4A4F54"
COLOR_BREEZE_DARK_DISABLED_TEXT = "#808080"

STYLE_BREEZE = {
    "font": QFont("Noto Sans", 11),
    "title_font": QFont("Noto Sans", 13, QFont.Bold),
    "light_border": COLOR_BREEZE_LIGHT_BORDER,
    "dark_border": COLOR_BREEZE_DARK_BORDER,
    # Estilo de botón para Breeze (más plano, sutil hover/pressed)
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

def apply_breeze_style_to_widget(widget, config_manager):
    """Aplica el estilo Breeze a un widget y sus hijos de forma recursiva."""
    theme = config_manager.get_theme()
    style_settings = STYLE_BREEZE

    palette = widget.palette()
    current_palette_colors = style_settings["dark_palette"] if theme == "dark" else style_settings["light_palette"]

    palette.setColor(QPalette.Window, current_palette_colors["window"])
    palette.setColor(QPalette.WindowText, current_palette_colors["window_text"])
    palette.setColor(QPalette.Base, current_palette_colors["base"])
    palette.setColor(QPalette.Text, current_palette_colors["text"])
    palette.setColor(QPalette.Button, current_palette_colors["button"])
    palette.setColor(QPalette.ButtonText, current_palette_colors["button_text"])
    palette.setColor(QPalette.Highlight, current_palette_colors["highlight"])
    palette.setColor(QPalette.HighlightedText, current_palette_colors["highlight_text"])
    palette.setColor(QPalette.ToolTipBase, current_palette_colors["base"])
    palette.setColor(QPalette.ToolTipText, current_palette_colors["text"])

    widget.setPalette(palette)
    widget.setFont(style_settings["font"])

    # Aplicar estilos CSS específicos a los hijos
    for child_widget in widget.findChildren(QWidget):
        if isinstance(child_widget, QApplication) or (isinstance(child_widget, QWidget) and not isinstance(child_widget, (QPushButton, QTableWidget, QGroupBox, QListWidget, QTreeWidget, QLineEdit, QComboBox, QCheckBox, QRadioButton))):
            continue

        child_widget.setFont(style_settings["font"])

        if isinstance(child_widget, QPushButton):
            child_widget.setStyleSheet(style_settings["dark_button_style"] if theme == "dark" else style_settings["button_style"])
        elif isinstance(child_widget, QTableWidget):
            child_widget.setStyleSheet(style_settings["dark_table_style"] if theme == "dark" else style_settings["table_style"])
        elif isinstance(child_widget, QGroupBox):
            child_widget.setStyleSheet(style_settings["dark_groupbox_style"] if theme == "dark" else style_settings["groupbox_style"])
            child_widget.setFont(style_settings["title_font"])
        elif isinstance(child_widget, (QListWidget, QTreeWidget)):
            list_tree_bg = style_settings["dark_palette"]["base"] if theme == "dark" else style_settings["light_palette"]["base"]
            list_tree_text = style_settings["dark_palette"]["text"] if theme == "dark" else style_settings["light_palette"]["text"]
            list_tree_border = style_settings["dark_border"] if theme == "dark" else style_settings["light_border"]
            list_tree_highlight = style_settings["dark_palette"]["highlight"] if theme == "dark" else style_settings["light_palette"]["highlight"]
            list_tree_highlight_text = style_settings["dark_palette"]["highlight_text"] if theme == "dark" else style_settings["light_palette"]["highlight_text"]
            header_bg = style_settings["dark_palette"]["button"] if theme == "dark" else style_settings["light_palette"]["button"]
            header_text = style_settings["dark_palette"]["button_text"] if theme == "dark" else style_settings["light_palette"]["button_text"]

            child_widget.setStyleSheet(style_settings["list_tree_style_template"].format(
                bg_color=list_tree_bg.name(),
                text_color=list_tree_text.name(),
                border_color=list_tree_border,
                font_size=style_settings["font"].pointSize(),
                highlight_color=list_tree_highlight.name(),
                highlight_text_color=list_tree_highlight_text.name(),
                header_bg_color=header_bg.name(),
                header_text_color=header_text.name()
            ))

        elif isinstance(child_widget, (QLineEdit, QComboBox)):
            bg_color = style_settings["dark_palette"]["base"].name() if theme == "dark" else style_settings["light_palette"]["base"].name()
            text_color = style_settings["dark_palette"]["text"].name() if theme == "dark" else style_settings["light_palette"]["text"].name()
            border_color = style_settings["dark_border"] if theme == "dark" else style_settings["light_border"]
            accent_color = COLOR_BREEZE_ACCENT

            child_widget.setStyleSheet(STYLE_BREEZE["lineedit_combobox_style_template"].format(
                bg_color=bg_color,
                text_color=text_color,
                border_color=border_color,
                accent_color=accent_color
            ))

        elif isinstance(child_widget, (QCheckBox, QRadioButton)):
            text_color = style_settings["dark_palette"]["text"].name() if theme == "dark" else style_settings["light_palette"]["text"].name()
            child_widget.setStyleSheet(STYLE_BREEZE["checkbox_radiobutton_style_template"].format(
                text_color=text_color
            ))

    widget.repaint()
