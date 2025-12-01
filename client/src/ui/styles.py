"""QSS стили для приложения."""

STYLES = """
/* Общие стили */
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    color: #333;
}

QMainWindow {
    background-color: #f5f5f5;
}

/* Кнопки */
QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #ccc;
    color: #666;
}

/* Вторичные кнопки */
QPushButton.secondary {
    background-color: #e1e1e1;
    color: #333;
}

QPushButton.secondary:hover {
    background-color: #d0d0d0;
}

/* Таблицы */
QTableWidget {
    background-color: white;
    border: 1px solid #ccc;
    gridline-color: #eee;
}

QHeaderView::section {
    background-color: #f0f0f0;
    padding: 4px;
    border: 1px solid #ddd;
    font-weight: bold;
}

/* Поля ввода */
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    padding: 6px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: white;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #0078d4;
}

/* Группы */
QGroupBox {
    font-weight: bold;
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 3px;
    left: 10px;
}

/* Статус бар */
QStatusBar {
    background-color: #0078d4;
    color: white;
}

/* Подсветка подозрительных полей */
QLineEdit.suspicious {
    background-color: #fff4ce;
    border-color: #fde7a9;
}
"""
