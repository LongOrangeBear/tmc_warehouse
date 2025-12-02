"""Виджет таблицы результатов распознавания."""
from typing import List, Tuple, Optional
import logging
import uuid
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QAction

from common.models import ReceptionItemCreate

logger = logging.getLogger(__name__)


class ResultsWidget(QTableWidget):
    """Таблица для отображения и редактирования позиций."""
    
    items_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[Tuple[str, ReceptionItemCreate]] = []  # (uuid, item)
        self._updating = False
        
        self.setColumnCount(7)  # Добавили колонку "Проверено"
        self.setHorizontalHeaderLabels([
            "Артикул", "Наименование", "Количество", "Ед.изм.", "Статус OCR", "БД", "Проверено"
        ])
        
        # Размеры колонок (фиксированные для стабильности)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 120)  # Артикул
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 80)  # Количество
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(3, 70)  # Ед.изм
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.resizeSection(4, 110)  # OCR статус
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.resizeSection(5, 110)  # БД статус
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        header.resizeSection(6, 120)  # Проверено
        
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        self.itemChanged.connect(self._on_item_changed)
        self._items: List[Tuple[str, ReceptionItemCreate]] = []
        self._updating = False

    def set_items(self, items: List[ReceptionItemCreate]):
        """Установить список позиций."""
        self._updating = True
        # Generate UUIDs for new items
        self._items = [(str(uuid.uuid4()), item) for item in items]
        self.setRowCount(len(items))
        
        # Импортируем SyncService для проверки БД
        from client.src.services import SyncService
        sync_service = SyncService()
        
        for row, (uid, item) in enumerate(self._items):
            # Артикул
            art_item = QTableWidgetItem(item.article)
            if "article" in item.suspicious_fields:
                art_item.setBackground(QColor("#fff4ce"))
                art_item.setToolTip("Низкая уверенность OCR")
            self.setItem(row, 0, art_item)
            
            # Наименование
            name_item = QTableWidgetItem(item.name)
            if "name" in item.suspicious_fields:
                name_item.setBackground(QColor("#fff4ce"))
            self.setItem(row, 1, name_item)
            
            # Количество
            qty_item = QTableWidgetItem(str(item.quantity))
            if "quantity" in item.suspicious_fields:
                qty_item.setBackground(QColor("#fff4ce"))
            self.setItem(row, 2, qty_item)
            
            # Ед.изм.
            unit_item = QTableWidgetItem(item.unit)
            if "unit" in item.suspicious_fields:
                unit_item.setBackground(QColor("#fff4ce"))
            self.setItem(row, 3, unit_item)
            
            # Статус OCR
            ocr_status = "⚠️ Проверьте" if item.suspicious_fields else "✓ OK"
            ocr_item = QTableWidgetItem(ocr_status)
            ocr_item.setFlags(ocr_item.flags() ^ Qt.ItemIsEditable)
            self.setItem(row, 4, ocr_item)
            
            # Статус БД - проверяем наличие товара в базе
            db_status = QTableWidgetItem("...")
            db_status.setFlags(db_status.flags() ^ Qt.ItemIsEditable)
            # БД статус - проверка наличия в базе
            db_status_text = "❓"
            db_status_color = QColor("gray")
            db_tooltip = "Ошибка при проверке БД"
            
            try:
                # Если артикул пустой - попробовать найти по наименованию
                product = None
                if item.article and item.article.strip():
                    product = sync_service.get_product_by_article(item.article)
                
                # Fallback: поиск по наименованию если артикул пустой
                if not product and item.name and item.name.strip():
                    all_products = sync_service.get_all_products()
                    # Поиск по частичному совпадению наименования
                    for p in all_products:
                        if p.name.lower() in item.name.lower() or item.name.lower() in p.name.lower():
                            product = p
                            break
                
                if product:
                    if product.requires_control:
                        db_status_text = "⚠️ Контроль"
                        db_status_color = QColor("orange")
                        db_tooltip = f"Товар требует контроля: {product.control_type or 'не указан'}"
                    else:
                        db_status_text = "✓ В БД"
                        db_status_color = QColor("green")
                        db_tooltip = "Товар найден в базе, контроль не требуется"
                else:
                    db_status_text = "❌ Нет в БД"
                    db_status_color = QColor("red")
                    db_tooltip = "Товар не найден в базе данных"
            except Exception as e:
                logger.error(f"Error checking product in DB: {e}")
                db_status_text = "❓"
                db_status_color = QColor("gray")
                db_tooltip = f"Ошибка проверки БД: {e}"

            db_status.setText(db_status_text)
            db_status.setForeground(db_status_color)
            db_status.setToolTip(db_tooltip)
            self.setItem(row, 5, db_status)
            
        self._updating = False

    def get_items(self) -> List[ReceptionItemCreate]:
        """Получить список позиций из таблицы (без UUID)."""
        # Reconstruct items from table to capture edits
        return [item for _, item in self.get_items_with_uuids()]

    def get_items_with_uuids(self) -> List[Tuple[str, ReceptionItemCreate]]:
        """Получить список позиций с их UUID."""
        items_with_uuids = []
        for row in range(self.rowCount()):
            if row >= len(self._items):
                continue
                
            original_uuid, original_item = self._items[row]
            
            article = self.item(row, 0).text()
            name = self.item(row, 1).text()
            quantity_text = self.item(row, 2).text()
            unit = self.item(row, 3).text()
            
            try:
                quantity = float(quantity_text)
            except ValueError:
                quantity = 0.0
            
            # Create new item with updated fields but keep original suspicious_fields
            # (or update them if user edited, but here we just copy for simplicity)
            # Ideally we should track if user edited suspicious fields.
            # In _on_item_changed we update the object in self._items.
            # So we can just return the object from self._items!
            # But wait, self._items is updated in _on_item_changed.
            # So we can just return self._items?
            # Yes, provided self._items stays in sync with rows.
            # _delete_selected_row keeps it in sync.
            # _add_row keeps it in sync.
            # _on_item_changed updates the object in place.
            
            items_with_uuids.append((original_uuid, original_item))
            
        return items_with_uuids

    def get_item_uuid(self, row: int) -> Optional[str]:
        """Получить UUID товара по индексу строки."""
        if 0 <= row < len(self._items):
            return self._items[row][0]
        return None

    def _on_item_changed(self, item: QTableWidgetItem):
        """Обработка редактирования ячейки."""
        if self._updating:
            return
            
        row = item.row()
        col = item.column()
        
        if row < 0 or row >= len(self._items):
            return
            
        _, obj = self._items[row]
        text = item.text()
        
        if col == 0:
            obj.article = text
            if "article" in obj.suspicious_fields:
                obj.suspicious_fields.remove("article")
                item.setBackground(Qt.white)
        elif col == 1:
            obj.name = text
            if "name" in obj.suspicious_fields:
                obj.suspicious_fields.remove("name")
                item.setBackground(Qt.white)
        elif col == 2:
            try:
                obj.quantity = float(text)
                if "quantity" in obj.suspicious_fields:
                    obj.suspicious_fields.remove("quantity")
                    item.setBackground(Qt.white)
            except ValueError:
                pass # Вернуть старое значение? Пока оставим как есть
        elif col == 3:
            obj.unit = text
            if "unit" in obj.suspicious_fields:
                obj.suspicious_fields.remove("unit")
                item.setBackground(Qt.white)
                
        # Обновить статус
        if not obj.suspicious_fields:
            self.item(row, 4).setText("OK")
            
        self.items_changed.emit()

    def _show_context_menu(self, position):
        """Контекстное меню."""
        menu = QMenu()
        delete_action = QAction("Удалить строку", self)
        delete_action.triggered.connect(self._delete_selected_row)
        menu.addAction(delete_action)
        
        add_action = QAction("Добавить строку", self)
        add_action.triggered.connect(self._add_row)
        menu.addAction(add_action)
        
        menu.exec(self.viewport().mapToGlobal(position))

    def _delete_selected_row(self):
        """Удалить выделенную строку."""
        rows = sorted(set(index.row() for index in self.selectedIndexes()), reverse=True)
        for row in rows:
            self.removeRow(row)
            del self._items[row]
        self.items_changed.emit()

    def _add_row(self):
        """Добавить новую пустую строку."""
        new_item = ReceptionItemCreate(
            article="", name="Новый товар", quantity=1, unit="шт", suspicious_fields=[]
        )
        self._items.append((str(uuid.uuid4()), new_item))
        self.set_items([item for _, item in self._items]) # Перерисовать всё проще
        self.items_changed.emit()
