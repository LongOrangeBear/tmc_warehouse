"""Диалог просмотра базы данных товаров."""
from typing import List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QPushButton, QLabel, QHBoxLayout, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from common.models import ProductRead
from client.src.services.sync_service import SyncService

class DatabaseDialog(QDialog):
    def __init__(self, sync_service: SyncService, parent=None):
        super().__init__(parent)
        self.sync_service = sync_service
        self.setWindowTitle("База данных товаров")
        self.resize(1000, 600)
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введите артикул или наименование...")
        self.search_edit.textChanged.connect(self._filter_data)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Артикул", "Наименование", "Ед.изм.", 
            "Контроль", "Тип контроля", "Параметры"
        ])
        
        # Настройка заголовков
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Артикул
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Наименование
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Ед.изм.
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Контроль
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Тип
        header.setSectionResizeMode(5, QHeaderView.Stretch)          # Параметры
        
        layout.addWidget(self.table)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
    def _load_data(self):
        self.products = self.sync_service.get_all_products()
        self._update_table(self.products)
        
    def _filter_data(self, text: str):
        text = text.lower()
        filtered = [
            p for p in self.products 
            if text in p.article.lower() or text in p.name.lower()
        ]
        self._update_table(filtered)
        
    def _update_table(self, products: List[ProductRead]):
        self.table.setRowCount(len(products))
        self.table.setSortingEnabled(False)
        
        control_type_names = {
            "visual_check": "Визуальный",
            "VISUAL_CHECK": "Визуальный",
            "weight_check": "Весовой",
            "WEIGHT_CHECK": "Весовой",
            "quantity_check": "Количественный",
            "QUANTITY_CHECK": "Количественный",
            "dimension_check": "Размерный",
            "DIMENSION_CHECK": "Размерный"
        }
        
        for row, p in enumerate(products):
            # Артикул
            self.table.setItem(row, 0, QTableWidgetItem(p.article))
            
            # Наименование
            self.table.setItem(row, 1, QTableWidgetItem(p.name))
            
            # Ед.изм.
            self.table.setItem(row, 2, QTableWidgetItem(p.unit))
            
            # Контроль
            req_control = QTableWidgetItem("Да" if p.requires_control else "Нет")
            if p.requires_control:
                req_control.setForeground(QColor("orange"))
            self.table.setItem(row, 3, req_control)
            
            # Тип контроля
            ctype = p.control_type
            if isinstance(ctype, object) and hasattr(ctype, 'value'):
                ctype = ctype.value
            ctype_ru = control_type_names.get(ctype, ctype or "-")
            self.table.setItem(row, 4, QTableWidgetItem(ctype_ru))
            
            # Параметры
            params_str = ""
            if p.control_params:
                # Показываем только ключевые параметры, без инструкций
                params = {k: v for k, v in p.control_params.items() if k != 'instructions'}
                params_str = str(params)
            self.table.setItem(row, 5, QTableWidgetItem(params_str))
            
        self.table.setSortingEnabled(True)
