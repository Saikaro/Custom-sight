from .constants import (
    BG, CARD, CARD2, ACCENT, ACCH, ACCL, TEXT, SUB, BORDER, BORDER2, RED, GREEN,
)


def get_stylesheet():
    return f"""
    * {{ font-family: 'Segoe UI', sans-serif; }}
    QWidget {{ font-size: 13px; color: {TEXT}; background: transparent; }}

    QGroupBox {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 10px;
        margin-top: 22px;
        padding: 12px 10px 10px 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 13px; top: 3px;
        color: {SUB};
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1.5px;
    }}

    QListWidget {{
        background: {BG};
        border: 1px solid {BORDER};
        border-radius: 8px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 7px 10px;
        border-radius: 5px;
        color: {SUB};
        margin: 1px 0;
    }}
    QListWidget::item:selected {{
        color: {ACCL};
        background: rgba(124,58,237,0.15);
        border: 1px solid rgba(124,58,237,0.3);
    }}
    QListWidget::item:hover:!selected {{
        background: {BORDER};
        color: {TEXT};
    }}

    QPushButton {{
        background: {CARD2};
        border: 1px solid {BORDER2};
        border-radius: 6px;
        padding: 5px 8px;
        color: {TEXT};
        font-size: 12px;
    }}
    QPushButton:hover {{ background: #222; border-color: #3a3a3a; }}
    QPushButton:pressed {{ background: {BG}; }}
    QPushButton:disabled {{ color: {SUB}; border-color: {BORDER}; background: {CARD}; }}

    QPushButton#AccentButton {{
        background: {ACCENT};
        border: none;
        color: white;
        font-weight: bold;
        font-size: 13px;
        border-radius: 7px;
        padding: 8px 16px;
    }}
    QPushButton#AccentButton:hover {{ background: {ACCH}; }}
    QPushButton#AccentButton:pressed {{ background: #6d28d9; }}
    QPushButton#AccentButton:disabled {{ background: rgba(124,58,237,0.30); color: rgba(255,255,255,0.30); }}

    QPushButton#DangerButton {{
        border: 1px solid rgba(239,68,68,0.4);
        color: {RED};
        background: transparent;
    }}
    QPushButton#DangerButton:hover {{
        background: rgba(239,68,68,0.1);
        border-color: {RED};
    }}
    QPushButton#DangerButton:disabled {{ color: rgba(239,68,68,0.28); border-color: rgba(239,68,68,0.14); }}

    QSlider::groove:horizontal {{
        height: 3px;
        background: {BORDER2};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {TEXT};
        border: 2px solid {BG};
        width: 14px;
        height: 14px;
        margin: -6px 0;
        border-radius: 7px;
    }}
    QSlider::handle:horizontal:hover {{ background: {ACCL}; border-color: {ACCENT}; }}
    QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}

    QComboBox {{
        background: {BG};
        border: 1px solid {BORDER2};
        border-radius: 6px;
        padding: 5px 10px;
        color: {TEXT};
    }}
    QComboBox:focus {{ border-color: {ACCENT}; }}
    QComboBox:disabled {{ color: {SUB}; border-color: {BORDER}; }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox QAbstractItemView {{
        background: {CARD};
        border: 1px solid {BORDER2};
        selection-background-color: rgba(124,58,237,0.2);
        selection-color: {ACCL};
        padding: 4px;
        outline: none;
    }}

    QLabel {{ color: {TEXT}; }}
    QLabel#Sub {{ color: {SUB}; font-size: 11px; }}
    QLabel#Status {{ color: {ACCL}; font-weight: bold; font-size: 12px; }}

    QLineEdit#spinbox {{
        background: {CARD2};
        color: {TEXT};
        border: 1px solid {BORDER2};
        border-radius: 5px;
        padding: 2px 6px;
        font-size: 12px;
        selection-background-color: transparent;
        selection-color: {TEXT};
    }}
    QLineEdit#spinbox:focus {{
        border: 1px solid {ACCENT};
        background: {CARD};
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER2};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {SUB}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

    QMessageBox {{ background: {CARD}; }}
    QMessageBox QLabel {{ color: {TEXT}; }}
    QMessageBox QPushButton {{ min-width: 70px; }}

    QInputDialog {{ background: {CARD}; }}
    QInputDialog QLabel {{ color: {TEXT}; }}
    QInputDialog QLineEdit {{
        background: {BG};
        border: 1px solid {BORDER2};
        border-radius: 5px;
        padding: 5px 8px;
        color: {TEXT};
    }}
    QInputDialog QLineEdit:focus {{ border-color: {ACCENT}; }}
    """
