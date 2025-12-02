"""Диалог истории приёмок."""
from typing import List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QPushButton, QMessageBox, QLabel, QAbstractItemView,
    QFileDialog
)
from PySide6.QtCore import Qt

from client.src.services import SyncService
from client.src.ui.reception_detail_dialog import ReceptionDetailDialog
from common.models import ReceptionShort, ReceptionStatus


class HistoryDialog(QDialog):
    """Диалог просмотра истории приёмок."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("История приёмок")
        self.resize(800, 600)
        
        self.sync_service = SyncService()
        self.receptions: List[ReceptionShort] = []
        
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "ТТН", "Дата", "Поставщик", "Статус"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # Двойной клик для открытия детального просмотра
        self.table.doubleClicked.connect(self._open_detail_dialog)
        
        layout.addWidget(self.table)
        
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._load_data)
        layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📊 Экспорт в Excel (CSV)")
        export_btn.clicked.connect(self._export_data)
        layout.addWidget(export_btn)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        close_btn.setProperty("class", "secondary")
        layout.addWidget(close_btn)

    def _load_data(self):
        self.table.setRowCount(0)
        try:
            self.receptions = self.sync_service.get_receptions(limit=50)
            self.table.setRowCount(len(self.receptions))
            
            for row, r in enumerate(self.receptions):
                self.table.setItem(row, 0, QTableWidgetItem(str(r.id)))
                self.table.setItem(row, 1, QTableWidgetItem(r.ttn_number))
                self.table.setItem(row, 2, QTableWidgetItem(r.ttn_date.strftime("%d.%m.%Y")))
                self.table.setItem(row, 3, QTableWidgetItem(r.supplier))
                
                status_item = QTableWidgetItem(r.status.value)
                if r.status == ReceptionStatus.COMPLETED:
                    status_item.setForeground(Qt.darkGreen)
                elif r.status == ReceptionStatus.PENDING:
                    status_item.setForeground(Qt.darkRed) # Or orange
                self.table.setItem(row, 4, status_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить историю: {e}")

    def _export_data(self):
        """Экспорт данных в CSV."""
        if not self.receptions:
            QMessageBox.warning(self, "Внимание", "Нет данных для экспорта")
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчет", "report.csv", "CSV Files (*.csv)"
        )
        
        if not path:
            return
            
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                # Header
                writer.writerow(["ID", "ТТН", "Дата", "Поставщик", "Статус"])
                # Data
                for r in self.receptions:
                    writer.writerow([
                        r.id,
                        r.ttn_number,
                        r.ttn_date.strftime("%d.%m.%Y"),
                        r.supplier,
                        r.status.value
                    ])
            
            QMessageBox.information(self, "Успех", f"Отчет сохранен: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")
    
    def _open_detail_dialog(self):
        """Открыть детальный просмотр выбранной приёмки."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        reception_id = self.receptions[row].id
        
        # Открыть диалог детального просмотра
        detail_dialog = ReceptionDetailDialog(reception_id, self)
        detail_dialog.exec()
