from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

STEAM_DECK_STYLE = {
    "font": QFont("Noto Sans", 10),
    "title_font": QFont("Noto Sans", 12, QFont.Bold),
    "button_style": """
        QPushButton {
            background-color: #3daee9;
            color: #FFFFFF;
            border: 1px solid #3daee9;
            border-radius: 6px;
            padding: 6px 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #5dbff2;
        }
        QPushButton:pressed {
            background-color: #2980b9;
        }
        QPushButton:disabled {
            background-color: #d0d0d0;
            color: #9e9e9e;
            border: 1px solid #cccccc;
        }
    """,
    "dark_button_style": """
        QPushButton {
            background-color: #f0f0f0;
            color: #2e3436;
            border: 1px solid #bfc4c9;
            border-radius: 6px;
            padding: 6px 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #e0e1e2;
        }
        QPushButton:pressed {
            background-color: #d0d1d2;
        }
        QPushButton:disabled {
            background-color: #555b61;
            color: #b0b0b0;
            border: 1px solid #6a6f75;
        }
    """,
    "light_palette": {
        "window": QColor(247, 248, 249),
        "window_text": QColor(33, 37, 41),
        "base": QColor(255, 255, 255),
        "text": QColor(33, 37, 41),
        "button": QColor(247, 248, 249),
        "button_text": QColor(33, 37, 41),
        "highlight": QColor(61, 174, 233),
        "highlight_text": Qt.white
    },
    "dark_palette": {
        "window": QColor(49, 54, 59),
        "window_text": Qt.white,
        "base": QColor(35, 38, 41),
        "text": Qt.white,
        "button": QColor(64, 70, 77),
        "button_text": Qt.white,
        "highlight": QColor(61, 174, 233),
        "highlight_text": Qt.white
    },
    "table_style": """
        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f9f9fa;
            gridline-color: #d0d0d0;
            border: 1px solid #c4c9cc;
        }
        QTableWidget::item {
            padding: 6px;
        }
        QTableWidget::item:selected {
            background-color: #3daee9;
            color: white;
        }
        QHeaderView::section {
            background-color: #f1f3f4;
            padding: 8px;
            border: 1px solid #c4c9cc;
            font-weight: bold;
        }
    """,
    "dark_table_style": """
        QTableWidget {
            background-color: #31363b;
            alternate-background-color: #2b3035;
            gridline-color: #555b61;
            border: 1px solid #5c636a;
        }
        QTableWidget::item {
            padding: 6px;
            color: white;
        }
        QTableWidget::item:selected {
            background-color: #3daee9;
            color: white;
        }
        QHeaderView::section {
            background-color: #40464d;
            padding: 8px;
            border: 1px solid #5c636a;
            font-weight: bold;
            color: white;
        }
    """,
    "groupbox_style": """
        QGroupBox {
            border: 1px solid #bfc4c9;
            border-radius: 6px;
            margin-top: 20px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            font-weight: bold;
            color: #2e3436;
        }
    """,
    "dark_groupbox_style": """
        QGroupBox {
            border: 1px solid #5c636a;
            border-radius: 6px;
            margin-top: 20px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            font-weight: bold;
            color: white;
        }
    """
}