"""Диалог детального просмотра приёмки."""
import logging
import json
import tempfile
from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QGroupBox, QSplitter, QScrollArea, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from client.src.services import SyncService
from common.models import ReceptionRead

logger = logging.getLogger(__name__)


class ReceptionDetailDialog(QDialog):
    """Диалог для детального просмотра приёмки."""
    
    def __init__(self, reception_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Просмотр приёмки #{reception_id}")
        self.resize(1400, 900)
        
        self.reception_id = reception_id
        self.sync_service = SyncService()
        self.reception: Optional[ReceptionRead] = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Создать UI."""
        layout = QVBoxLayout(self)
        
        # === Заголовок: Информация о приёмке ===
        info_group = QGroupBox("Информация о приёмке")
        info_layout = QVBoxLayout(info_group)
        
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("padding: 10px; background: #f5f5f5; border-radius: 5px;")
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_group)
        
        # === Основная зона: Товары + Детали ===
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая часть: Таблица товаров
        items_group = QGroupBox("Товары")
        items_layout = QVBoxLayout(items_group)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Артикул", "Наименование", "Кол-во", "Ед.изм.", "Цена", "Статус"
        ])
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items_table.itemSelectionChanged.connect(self._on_item_selected)
        
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        items_layout.addWidget(self.items_table)
        splitter.addWidget(items_group)
        
        # Правая часть: Детали товара (комментарии + фото)
        details_group = QGroupBox("Детали товара")
        details_layout = QVBoxLayout(details_group)
        
        # Комментарии
        details_layout.addWidget(QLabel("<b>Комментарии:</b>"))
        self.comments_text = QTextEdit()
        self.comments_text.setReadOnly(True)
        self.comments_text.setMaximumHeight(150)
        self.comments_text.setPlaceholderText("Выберите товар в таблице...")
        details_layout.addWidget(self.comments_text)
        
        # Фотографии
        details_layout.addWidget(QLabel("<b>Фотографии:</b>"))
        
        # Скроллируемая область для фото
        photos_scroll = QScrollArea()
        photos_scroll.setWidgetResizable(True)
        photos_scroll.setMinimumHeight(200)
        
        self.photos_widget = QLabel("Нет фотографий")
        self.photos_widget.setAlignment(Qt.AlignCenter)
        self.photos_widget.setStyleSheet("border: 1px solid #ccc; background: #f9f9f9; padding: 10px;")
        photos_scroll.setWidget(self.photos_widget)
        
        details_layout.addWidget(photos_scroll)
        
        # Кнопки для работы с фото
        photo_buttons = QHBoxLayout()
        self.download_photos_btn = QPushButton("💾 Скачать все фото")
        self.download_photos_btn.clicked.connect(self._download_photos)
        self.download_photos_btn.setEnabled(False)
        photo_buttons.addWidget(self.download_photos_btn)
        photo_buttons.addStretch()
        
        details_layout.addLayout(photo_buttons)
        details_layout.addStretch()
        
        splitter.addWidget(details_group)
        
        # Соотношение таблица:детали = 2:1
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter, stretch=1)
        
        # === Нижняя панель: Видео + Документы ===
        media_layout = QHBoxLayout()
        
        # Видео
        self.video_btn = QPushButton("🎥 Скачать видео приёмки")
        self.video_btn.clicked.connect(self._download_video)
        self.video_btn.setEnabled(False)
        media_layout.addWidget(self.video_btn)
        
        # Документ (PDF/изображение ТТН)
        self.document_btn = QPushButton("📄 Скачать документ ТТН")
        self.document_btn.clicked.connect(self._download_document)
        self.document_btn.setEnabled(False)
        media_layout.addWidget(self.document_btn)
        
        media_layout.addStretch()
        
        # Закрыть
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        close_btn.setProperty("class", "secondary")
        media_layout.addWidget(close_btn)
        
        layout.addLayout(media_layout)
    
    def _load_data(self):
        """Загрузить данные приёмки с сервера."""
        try:
            self.reception = self.sync_service.get_reception(self.reception_id)
            
            if not self.reception:
                QMessageBox.critical(self, "Ошибка", f"Приёмка #{self.reception_id} не найдена")
                self.reject()
                return
            
            # Заполнить информацию о приёмке
            info_html = f"""
            <table>
                <tr><td><b>ID:</b></td><td>{self.reception.id}</td></tr>
                <tr><td><b>ТТН:</b></td><td>{self.reception.ttn_number}</td></tr>
                <tr><td><b>Дата ТТН:</b></td><td>{self.reception.ttn_date.strftime('%d.%m.%Y')}</td></tr>
                <tr><td><b>Поставщик:</b></td><td>{self.reception.supplier}</td></tr>
                <tr><td><b>Статус:</b></td><td style='color: {"green" if self.reception.status.value == "completed" else "orange"};'>{self.reception.status.value}</td></tr>
                <tr><td><b>Создано:</b></td><td>{self.reception.created_at.strftime('%d.%m.%Y %H:%M')}</td></tr>
            </table>
            """
            self.info_label.setText(info_html)
            
            # Заполнить таблицу товаров
            self.items_table.setRowCount(len(self.reception.items))
            for row, item in enumerate(self.reception.items):
                self.items_table.setItem(row, 0, QTableWidgetItem(item.article or "-"))
                self.items_table.setItem(row, 1, QTableWidgetItem(item.name))
                self.items_table.setItem(row, 2, QTableWidgetItem(str(item.quantity)))
                self.items_table.setItem(row, 3, QTableWidgetItem(item.unit))
                
                # В ReceptionItemRead нет поля price, показываем "-"
                self.items_table.setItem(row, 4, QTableWidgetItem("-"))
                
                # Статус контроля на основе control_status
                from common.models import ControlStatus
                if item.control_status == ControlStatus.PASSED:
                    status_text = "✓ Принято"
                    status_color = Qt.darkGreen
                elif item.control_status == ControlStatus.FAILED:
                    status_text = "✗ Отклонено"
                    status_color = Qt.darkRed
                elif item.control_status == ControlStatus.PENDING:
                    status_text = "⏳ Ожидание"
                    status_color = Qt.darkGray
                else:
                    status_text = "-"
                    status_color = Qt.darkGray
                    
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(status_color)
                self.items_table.setItem(row, 5, status_item)
            
            # Проверить наличие видео и документа
            # Предполагаем, что если есть video_path/document_path в модели
            if hasattr(self.reception, 'video_path') and self.reception.video_path:
                self.video_btn.setEnabled(True)
            
            if hasattr(self.reception, 'document_path') and self.reception.document_path:
                self.document_btn.setEnabled(True)
                
        except Exception as e:
            logger.error(f"Failed to load reception {self.reception_id}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить приёмку: {e}")
            self.reject()
    
    def _on_item_selected(self):
        """Обработка выбора товара в таблице."""
        selected_rows = self.items_table.selectionModel().selectedRows()
        
        if not selected_rows or not self.reception:
            self.comments_text.clear()
            self.comments_text.setPlaceholderText("Выберите товар в таблице...")
            self.photos_widget.setText("Нет фотографий")
            self.download_photos_btn.setEnabled(False)
            return
        
        row = selected_rows[0].row()
        item = self.reception.items[row]
        
        # Показать комментарии (notes в модели)
        if item.notes:
            self.comments_text.setPlainText(item.notes)
        else:
            self.comments_text.setPlaceholderText("Комментариев нет")
            self.comments_text.clear()
        
        # Показать фотографии
        if item.photos:
            # photos - это JSON список путей
            import json
            try:
                if isinstance(item.photos, str):
                    photo_paths = json.loads(item.photos)
                else:
                    photo_paths = item.photos
                
                if photo_paths and len(photo_paths) > 0:
                    self._display_photos(photo_paths, item.id)
                    self.download_photos_btn.setEnabled(True)
                else:
                    self.photos_widget.setText("Нет фотографий")
                    self.download_photos_btn.setEnabled(False)
            except Exception as e:
                logger.error(f"Error parsing photos: {e}")
                self.photos_widget.setText(f"Ошибка загрузки фото: {e}")
                self.download_photos_btn.setEnabled(False)
        else:
            self.photos_widget.setText("Нет фотографий")
            self.download_photos_btn.setEnabled(False)
    
    def _display_photos(self, photo_paths: list, item_id: int):
        """Отобразить фотографии товара."""
        count = len(photo_paths)
        
        # Создать временную директорию для фото
        temp_dir = Path(tempfile.gettempdir()) / f"tmc_photos_{item_id}"
        temp_dir.mkdir(exist_ok=True)
        
        # Скачать фотографии
        downloaded_count = 0
        for i, photo_rel_path in enumerate(photo_paths):
            try:
                save_path = temp_dir / f"photo_{i}.jpg"
                if self.sync_service.download_single_photo(
                    self.reception_id, 
                    item_id, 
                    i, 
                    save_path
                ):
                    downloaded_count += 1
            except Exception as e:
                logger.error(f"Failed to download photo {i}: {e}")
        
        if downloaded_count > 0:
            # Показать превью фотографий (упрощенная версия)
            from PySide6.QtWidgets import QHBoxLayout
            from PySide6.QtCore import Qt
            
            layout = QHBoxLayout()
            
            for i in range(downloaded_count):
                photo_path = temp_dir / f"photo_{i}.jpg"
                if photo_path.exists():
                    pixmap = QPixmap(str(photo_path))
                    if not pixmap.isNull():
                        label = QLabel()
                        scaled = pixmap.scaled(
                            150, 150, 
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation
                        )
                        label.setPixmap(scaled)
                        label.setToolTip(f"Фото {i+1}/{count}")
                        label.setStyleSheet("border: 2px solid #ddd; padding: 2px;")
                        layout.addWidget(label)
            
            layout.addStretch()
            
            # Очистить старый виджет и установить layout
            old_widget = self.photos_widget
            self.photos_widget = QLabel()
            self.photos_widget.setLayout(layout)
            old_widget.parent().layout().replaceWidget(old_widget, self.photos_widget)
        else:
            self.photos_widget.setText(f"❌ Не удалось загрузить фотографии ({count} доступно)")
    
    def _download_photos(self):
        """Скачать все фотографии выбранного товара."""
        selected_rows = self.items_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        item = self.reception.items[row]
        
        # Спросить куда сохранить
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить фотографии",
            f"item_{item.id}_photos.zip",
            "ZIP Archives (*.zip)"
        )
        
        if not save_path:
            return
        
        # Скачать ZIP архив
        try:
            if self.sync_service.download_item_photos_zip(
                self.reception_id,
                item.id,
                Path(save_path)
            ):
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Фотографии сохранены:\n{save_path}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Не удалось скачать фотографии. Проверьте логи."
                )
        except Exception as e:
            logger.error(f"Failed to download photos: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка скачивания: {e}")
    
    def _download_video(self):
        """Скачать видео приёмки."""
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить видео",
            f"reception_{self.reception_id}_video.avi",
            "Video Files (*.avi *.mp4)"
        )
        
        if not save_path:
            return
        
        try:
            if self.sync_service.download_video(
                self.reception_id,
                Path(save_path)
            ):
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Видео сохранено:\n{save_path}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Не удалось скачать видео. Возможно, оно не было загружено."
                )
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка скачивания: {e}")
    
    def _download_document(self):
        """Скачать документ ТТН."""
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить документ",
            f"reception_{self.reception_id}_document.pdf",
            "PDF Files (*.pdf);;Images (*.png *.jpg)"
        )
        
        if not save_path:
            return
        
        try:
            if self.sync_service.download_document(
                self.reception_id,
                Path(save_path)
            ):
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Документ сохранен:\n{save_path}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Не удалось скачать документ. Возможно, он не был загружен."
                )
        except Exception as e:
            logger.error(f"Failed to download document: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка скачивания: {e}")
