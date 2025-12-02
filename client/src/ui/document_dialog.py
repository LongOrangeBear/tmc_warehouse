"""Диалог загрузки документа и создания приёмки."""
import logging
from pathlib import Path
from datetime import date
from typing import Optional
import tempfile
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QLineEdit, QMessageBox,
    QDateEdit, QScrollArea, QSplitter, QWidget, QGroupBox, QTextEdit, QTableWidgetItem,
    QProgressDialog, QSizePolicy, QTabWidget
)
from PySide6.QtCore import Qt, QDate, QTimer, QCoreApplication
from PySide6.QtGui import QPixmap, QColor

from client.src.services import OCRService, SyncService, CameraService
from client.src.ui.results_widget import ResultsWidget
from client.src.ui.video_widget import VideoWidget
from client.src.ui.database_dialog import DatabaseDialog
from common.models import OCRResult, ReceptionCreate, ReceptionItemCreate, ProductRead
logger = logging.getLogger(__name__)


class DocumentDialog(QDialog):
    """Диалог для обработки документа ТТН."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Приёмка ТМЦ - Загрузка документа")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        self.ocr_service = OCRService()
        self.sync_service = SyncService()
        self.current_file: Optional[Path] = None
        self.current_video_path: Optional[str] = None
        self.ocr_result: Optional[OCRResult] = None
        self.verified_items = {}  # {uuid: {'status': 'verified'|'rejected', 'comment': str, 'photos': []}}
        self.products_cache = {}  # Кеш товаров из БД {article: ProductRead}
        self.camera_service = CameraService()
        self.camera_active = False
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Верхняя панель: Выбор файла (упрощенная)
        top_panel = QHBoxLayout()
        
        self.file_path_label = QLabel("Файл не выбран")
        self.file_path_label.setStyleSheet("color: gray; font-weight: bold;")
        
        self.select_btn = QPushButton("Выбрать файл")
        self.select_btn.clicked.connect(self._select_file)
        
        self.reset_btn = QPushButton("🔄 Сброс")
        self.reset_btn.clicked.connect(self._reset_all)
        self.reset_btn.setEnabled(False)
        self.reset_btn.setStyleSheet("background-color: #ff9800; color: white;")
        
        self.db_btn = QPushButton("🗄️ База данных")
        self.db_btn.clicked.connect(self._show_database)
        
        top_panel.addWidget(self.file_path_label, 1)
        top_panel.addWidget(self.select_btn)
        top_panel.addWidget(self.reset_btn)
        top_panel.addWidget(self.db_btn)
        
        layout.addLayout(top_panel)
        
        # === ГЛАВНЫЙ ГОРИЗОНТАЛЬНЫЙ СПЛИТТЕР (Лево 2/3 | Право 1/3) ===
        main_horizontal_splitter = QSplitter(Qt.Horizontal)
        
        # === ЛЕВАЯ КОЛОНКА: Вертикальный сплиттер (Верх 50% | Низ 50%) ===
        left_vertical_splitter = QSplitter(Qt.Vertical)
        
        # --- ВЕРХ ЛЕВОЙ КОЛОНКИ: Вкладки (Видео / Документ) ---
        self.content_tabs = QTabWidget()
        
        # Вкладка 1: Видео
        video_tab = QWidget()
        video_layout = QVBoxLayout(video_tab)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = VideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.video_widget.setMinimumHeight(300)
        video_layout.addWidget(self.video_widget, 0, Qt.AlignCenter)
        
        # Индикатор записи (удален, теперь внутри VideoWidget)
        # self.recording_indicator = QLabel("") ...
        
        self.content_tabs.addTab(video_tab, "📹 Видео")
        
        # Вкладка 2: Документ (превью)
        document_tab = QWidget()
        document_layout = QVBoxLayout(document_tab)
        document_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_scroll = QScrollArea()
        preview_scroll.setWidgetResizable(True)
        self.preview_label = QLabel("Документ не загружен")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("color: gray;")
        preview_scroll.setWidget(self.preview_label)
        document_layout.addWidget(preview_scroll)
        
        self.content_tabs.addTab(document_tab, "📄 Документ")
        
        left_vertical_splitter.addWidget(self.content_tabs)
        
        # --- НИЖНЯЯ ЛЕВАЯ КОЛОНКА: Таблица позиций ---
        table_container = QGroupBox("Позиции")
        table_layout = QVBoxLayout(table_container)
        
        self.results_widget = ResultsWidget()
        self.results_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.results_widget.itemSelectionChanged.connect(self._on_item_selected)
        table_layout.addWidget(self.results_widget)
        
        left_vertical_splitter.addWidget(table_container)
        
        # Настройка пропорций левого вертикального сплиттера (50/50)
        left_vertical_splitter.setStretchFactor(0, 1)
        left_vertical_splitter.setStretchFactor(1, 1)
        
        main_horizontal_splitter.addWidget(left_vertical_splitter)
        
        # === ПРАВАЯ КОЛОНКА: Данные документа + Проверка товара ===
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- ДАННЫЕ ДОКУМЕНТА (фиксированная высота) ---
        fields_group = QGroupBox("Данные документа")
        fields_layout = QVBoxLayout(fields_group)
        
        # Строка 1: Номер ТТН
        ttn_row = QHBoxLayout()
        ttn_row.addWidget(QLabel("Номер ТТН:"))
        self.ttn_edit = QLineEdit()
        self.ttn_edit.setPlaceholderText("Номер ТТН")
        ttn_row.addWidget(self.ttn_edit, 1)
        fields_layout.addLayout(ttn_row)
        
        # Строка 2: Дата ТТН
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("Дата ТТН:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        date_row.addWidget(self.date_edit, 1)
        fields_layout.addLayout(date_row)
        
        # Строка 3: Поставщик
        supplier_row = QHBoxLayout()
        supplier_row.addWidget(QLabel("Поставщик:"))
        self.supplier_edit = QLineEdit()
        self.supplier_edit.setPlaceholderText("Поставщик")
        supplier_row.addWidget(self.supplier_edit, 1)
        fields_layout.addLayout(supplier_row)
        
        right_layout.addWidget(fields_group)
        
        # --- ПРОВЕРКА ТОВАРА (резиновая) ---
        self.verification_panel = QGroupBox("Проверка товара")
        self.verification_panel.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; border: 2px solid #ccc; border-radius: 5px; }")
        verification_layout = QVBoxLayout(self.verification_panel)
        
        # Создаем ScrollArea для контента проверки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Информация о товаре
        self.product_info_label = QLabel("Выберите товар в таблице")
        self.product_info_label.setWordWrap(True)
        self.product_info_label.setStyleSheet("padding: 10px; background: #f5f5f5; border-radius: 5px;")
        scroll_layout.addWidget(self.product_info_label)
        
        # 2. Инструкции
        scroll_layout.addWidget(QLabel("<b>Что проверить:</b>"))
        self.instructions_label = QLabel("")
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setStyleSheet("padding: 10px; background: #fffacd; border-radius: 5px;")
        scroll_layout.addWidget(self.instructions_label)
        
        # 3. Фото товара (Кликабельное)
        scroll_layout.addWidget(QLabel("<b>Фото товара:</b>"))
        self.photo_preview_label = QLabel()
        self.photo_preview_label.setAlignment(Qt.AlignCenter)
        self.photo_preview_label.setFixedSize(200, 200) # Немного увеличим
        self.photo_preview_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 5px;
                background: #f9f9f9;
            }
            QLabel:hover {
                border-color: #2196F3;
                background: #e3f2fd;
            }
        """)
        self.photo_preview_label.setText("📷\nНажмите, чтобы\nсделать фото")
        self.photo_preview_label.setWordWrap(True)
        self.photo_preview_label.setCursor(Qt.PointingHandCursor)
        # Обработка клика теперь будет в _on_photo_clicked
        self.photo_preview_label.mousePressEvent = self._on_photo_clicked 
        self.current_photo_path = None
        
        # Центрируем фото
        photo_container = QHBoxLayout()
        photo_container.addStretch()
        photo_container.addWidget(self.photo_preview_label)
        photo_container.addStretch()
        scroll_layout.addLayout(photo_container)
        
        # 4. Комментарий (под фото)
        scroll_layout.addWidget(QLabel("<b>Комментарий:</b>"))
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        self.comment_edit.setPlaceholderText("Опишите причину, если товар не принят...")
        scroll_layout.addWidget(self.comment_edit)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        verification_layout.addWidget(scroll_area)
        
        # Кнопки проверки (принять/отклонить) - ВНИЗУ, вне скролла
        buttons_layout = QHBoxLayout()
        
        self.mark_verified_btn = QPushButton("✓ Принять")
        self.mark_verified_btn.clicked.connect(lambda: self._mark_verified(True))
        self.mark_verified_btn.setEnabled(False)
        self.mark_verified_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        
        self.mark_rejected_btn = QPushButton("✗ Не принимать")
        self.mark_rejected_btn.clicked.connect(lambda: self._mark_verified(False))
        self.mark_rejected_btn.setEnabled(False)
        self.mark_rejected_btn.setStyleSheet("background-color: #d13438; color: white; font-weight: bold; padding: 10px;")
        
        buttons_layout.addWidget(self.mark_verified_btn)
        buttons_layout.addWidget(self.mark_rejected_btn)
        
        verification_layout.addLayout(buttons_layout)
        
        right_layout.addWidget(self.verification_panel)
        
        main_horizontal_splitter.addWidget(right_container)
        
        # Настройка пропорций главного горизонтального сплиттера (2/3 лево, 1/3 право)
        main_horizontal_splitter.setStretchFactor(0, 2)
        main_horizontal_splitter.setStretchFactor(1, 1)
        
        layout.addWidget(main_horizontal_splitter)
        
        # Нижняя панель: Кнопки действий
        bottom_panel = QHBoxLayout()
        
        # Счетчик непроверенных товаров
        self.counter_label = QLabel("")
        self.counter_label.setStyleSheet("color: orange; font-weight: bold;")
        
        self.create_btn = QPushButton("✉️ Отправить на сервер")
        self.create_btn.clicked.connect(self._create_reception)
        self.create_btn.setEnabled(False)
        self.create_btn.setStyleSheet("font-weight: bold; padding: 10px;")
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setProperty("class", "secondary")
        
        bottom_panel.addStretch()
        bottom_panel.addWidget(self.counter_label)
        bottom_panel.addWidget(self.create_btn)
        bottom_panel.addWidget(cancel_btn)
        
        layout.addLayout(bottom_panel)
        
        # Подключение сигналов камеры
        self.camera_service.frame_ready.connect(self.video_widget.update_frame)
        self.camera_service.recording_started.connect(self._on_recording_started)
        self.camera_service.recording_stopped.connect(self._on_recording_stopped)
        self.camera_service.recording_size_updated.connect(self.video_widget.update_video_size)
        self.camera_service.recording_limit_exceeded.connect(self._on_recording_limit_exceeded)
        
        # Таймер для мигания индикатора записи
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._blink_recording_indicator)
        self.blink_state = False



    def _select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать документ", "", "Images/PDF (*.png *.jpg *.jpeg *.pdf)"
        )
        if file_path:
            self.current_file = Path(file_path)
            self.file_path_label.setText(self.current_file.name)
            self.file_path_label.setStyleSheet("color: black; font-weight: bold;")
            self.reset_btn.setEnabled(True)
            
            # Загрузить превью во вкладку "Документ"
            if self.current_file.suffix.lower() == ".pdf":
                # Конвертировать первую страницу PDF в изображение
                try:
                    from pdf2image import convert_from_path
                    images = convert_from_path(str(self.current_file), first_page=1, last_page=1, dpi=150)
                    if images:
                        # Конвертировать PIL Image в QPixmap
                        import io
                        buffer = io.BytesIO()
                        images[0].save(buffer, format='PNG')
                        buffer.seek(0)
                        pixmap = QPixmap()
                        pixmap.loadFromData(buffer.getvalue())
                        if not pixmap.isNull():
                            self.preview_label.setPixmap(pixmap.scaled(
                                800, 1200, Qt.KeepAspectRatio, Qt.SmoothTransformation
                            ))
                        else:
                            self.preview_label.setText("PDF Документ\n(Не удалось загрузить превью)")
                    else:
                        self.preview_label.setText("PDF Документ\n(Запуск распознавания...)")
                except Exception as e:
                    logger.warning(f"Failed to render PDF preview: {e}")
                    self.preview_label.setText("PDF Документ\n(Запуск распознавания...)")
            else:
                pixmap = QPixmap(str(self.current_file))
                self.preview_label.setPixmap(pixmap.scaled(
                    800, 1200, Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
            
            # Автоматически запускаем распознавание
            self._run_ocr()


    def _run_ocr(self):
        if not self.current_file:
            return
        
        logger.info(f"Starting OCR processing: {self.current_file}")
        self.setCursor(Qt.WaitCursor)
        
        try:
            # Запуск OCR
            result = self.ocr_service.process_document(self.current_file)
            logger.info(f"OCR completed: TTN={result.ttn_number}, items={len(result.items)}")
            
            # Очистить кеш проверенных товаров при новом OCR
            self.verified_items.clear()
            self._update_create_button_state()
            
            # ОТКЛЮЧИТЬ кнопку загрузки после успешного OCR
            self.select_btn.setEnabled(False)
            
            # ЗАПУСТИТЬ КАМЕРУ и ЗАПИСЬ после успешного OCR
            self._start_camera(auto_record=True)
            
            # Заполнение полей
            if result.ttn_number:
                self.ttn_edit.setText(result.ttn_number)
            if result.ttn_date:
                self.date_edit.setDate(result.ttn_date)
            if result.supplier:
                self.supplier_edit.setText(result.supplier)
                
            # Конвертация и заполнение таблицы
            items = self.ocr_service.ocr_items_to_reception_items(result.items)
            self.results_widget.set_items(items)
            
            QMessageBox.information(self, "OCR", "Распознавание завершено. Начата видеозапись.\nПроверьте все товары.")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка OCR: {e}")
        finally:
            self.setCursor(Qt.ArrowCursor)

    def _create_reception(self):
        # Валидация
        ttn = self.ttn_edit.text().strip()
        if not ttn:
            QMessageBox.warning(self, "Ошибка", "Введите номер ТТН")
            return
            
        items = self.results_widget.get_items()
        if not items:
            QMessageBox.warning(self, "Ошибка", "Список товаров пуст")
            return
            
        # Сбор данных для создания
        data = ReceptionCreate(
            ttn_number=ttn,
            ttn_date=self.date_edit.date().toPython(),
            supplier=self.supplier_edit.text().strip(),
            items=items
        )
        
        # Отправка на сервер (создание черновика)
        logger.info(f"Creating reception: TTN={ttn}, items={len(items)}")
        
        # Настройка прогресс-диалога
        progress = QProgressDialog("Подготовка к отправке...", None, 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.setValue(0)
        progress.show()
        QCoreApplication.processEvents()

        try:
            # 1. Создание приёмки (15%)
            progress.setLabelText("Шаг 1/7: Создание записи приёмки...")
            progress.setValue(5)
            QCoreApplication.processEvents()
            
            reception = self.sync_service.create_reception(data)
            if not reception:
                progress.close()
                logger.error("Failed to create reception (returned None)")
                QMessageBox.critical(self, "Ошибка", "Не удалось создать приёмку")
                return
            
            progress.setValue(15)
            QCoreApplication.processEvents()
            logger.info(f"Reception created successfully: ID={reception.id}")
            
            # 2. Загрузка файла документа (30%)
            if self.current_file:
                progress.setLabelText(f"Шаг 2/7: Загрузка документа ({self.current_file.name})...")
                progress.setValue(20)
                QCoreApplication.processEvents()
                
                logger.info(f"Uploading document for reception {reception.id}")
                self.sync_service.upload_document(reception.id, self.current_file)
                
                progress.setValue(30)
                QCoreApplication.processEvents()
            else:
                progress.setValue(30)
            
            # 3. Загрузка видео (45%)
            if self.current_video_path and os.path.exists(self.current_video_path):
                video_size_mb = os.path.getsize(self.current_video_path) / (1024 * 1024)
                progress.setLabelText(f"Шаг 3/7: Загрузка видео ({video_size_mb:.1f} МБ)...")
                progress.setValue(35)
                QCoreApplication.processEvents()
                
                logger.info(f"Uploading video for reception {reception.id}")
                self.sync_service.upload_video(reception.id, Path(self.current_video_path))
                
                progress.setValue(45)
                QCoreApplication.processEvents()
            else:
                progress.setValue(45)
            
            # 4. Загрузка фотографий (45-65%)
            photos_count = 0
            if reception.items:
                progress.setLabelText("Шаг 4/7: Загрузка фотографий товаров...")
                progress.setValue(50)
                QCoreApplication.processEvents()
                
                # Получаем items из БД (они с ID)
                db_items = list(reception.items)
                db_items.sort(key=lambda x: x.id)
                
                # Получаем исходные items с UUID для маппинга
                items_with_uuids = self.results_widget.get_items_with_uuids()
                
                if len(db_items) != len(items_with_uuids):
                    logger.warning(f"Count mismatch: db_items={len(db_items)}, sent_items={len(items_with_uuids)}")
                
                total_items = len(db_items)
                
                for i, db_item in enumerate(db_items):
                    if i >= len(items_with_uuids):
                        break
                    
                    item_uuid, _ = items_with_uuids[i]
                    verified_data = self.verified_items.get(item_uuid, {})
                    
                    # Загрузка фото
                    photos = verified_data.get('photos', [])
                    if photos:
                        for photo_path in photos:
                            try:
                                if os.path.exists(photo_path):
                                    photos_count += 1
                                    progress.setLabelText(f"Шаг 4/7: Загрузка фото {photos_count}...")
                                    logger.info(f"Uploading photo for item {db_item.id}: {photo_path}")
                                    self.sync_service.upload_photo(reception.id, db_item.id, Path(photo_path))
                            except Exception as e:
                                logger.error(f"Error uploading photo: {e}")
                    
                    # Обновляем прогресс (от 50 до 65)
                    current_progress = 50 + int((i + 1) / total_items * 15)
                    progress.setValue(current_progress)
                    QCoreApplication.processEvents()
                
                progress.setValue(65)
                QCoreApplication.processEvents()
            else:
                progress.setValue(65)
            
            # 5. Отправка результатов контроля (65-80%)
            if reception.items:
                progress.setLabelText("Шаг 5/7: Отправка результатов контроля...")
                progress.setValue(70)
                QCoreApplication.processEvents()
                
                control_updates = []
                db_items = list(reception.items)
                db_items.sort(key=lambda x: x.id)
                items_with_uuids = self.results_widget.get_items_with_uuids()
                
                for i, db_item in enumerate(db_items):
                    if i >= len(items_with_uuids):
                        break
                    
                    item_uuid, _ = items_with_uuids[i]
                    verified_data = self.verified_items.get(item_uuid, {})
                    status = verified_data.get('status', 'pending')
                    
                    from common.models import ControlStatus, ReceptionItemControlUpdate
                    
                    api_status = ControlStatus.PENDING
                    if status == 'verified':
                        api_status = ControlStatus.PASSED
                    elif status == 'rejected':
                        api_status = ControlStatus.FAILED
                    
                    update = ReceptionItemControlUpdate(
                        id=db_item.id,
                        control_status=api_status,
                        notes=verified_data.get('comment'),
                        control_result={}
                    )
                    control_updates.append(update)
                
                if control_updates:
                    logger.info(f"Sending control results for {len(control_updates)} items")
                    self.sync_service.send_control_results(reception.id, control_updates)
                    
                    progress.setValue(80)
                    QCoreApplication.processEvents()
            else:
                progress.setValue(80)
            
            # 6. Финализация (80-90%)
            progress.setLabelText("Шаг 6/7: Финализация данных...")
            progress.setValue(85)
            QCoreApplication.processEvents()
            
            # Короткая пауза для завершения обработки на сервере
            import time
            time.sleep(0.5)
            
            progress.setValue(90)
            QCoreApplication.processEvents()
            
            # 7. Итоговый статус (90-100%)
            progress.setLabelText("Шаг 7/7: Формирование отчёта...")
            progress.setValue(95)
            QCoreApplication.processEvents()
            
            # Формируем итоговое сообщение
            summary_parts = []
            summary_parts.append(f"✓ Данные отправлены (приёмка #{reception.id})")
            if photos_count > 0:
                summary_parts.append(f"✓ Фотографии отправлены ({photos_count} шт.)")
            else:
                summary_parts.append("○ Фотографии: нет")
            if self.current_video_path and os.path.exists(self.current_video_path):
                summary_parts.append("✓ Видео отправлено")
            else:
                summary_parts.append("○ Видео: нет")
            summary_parts.append("✓ Добавлено в список приёмок")
            
            summary_text = "\n".join(summary_parts)
            
            progress.setValue(100)
            progress.setLabelText(f"Готово!\n\n{summary_text}")
            
            # Добавить кнопку "Продолжить"
            from PySide6.QtWidgets import QPushButton
            ok_button = QPushButton("Продолжить")
            progress.setCancelButton(ok_button)
            progress.setCancelButtonText("Продолжить")
            
            QCoreApplication.processEvents()
            
            # Ждём нажатия кнопки
            progress.exec()
            
            # Остановить камеру после успешной отправки
            self._stop_camera()
            
            self.accept()
            
        except Exception as e:
            progress.close()
            logger.exception(f"Exception during reception creation: {e}")
            
            # Показать детальное сообщение об ошибке
            error_msg = f"Ошибка при создании приёмки:\n\n{str(e)}"
            QMessageBox.critical(self, "Ошибка", error_msg)
    
    def _on_item_selected(self):
        """Обработка выбора товара в таблице."""
        selected_rows = self.results_widget.selectionModel().selectedRows()
        
        # Показывать кнопку проверки ТОЛЬКО при выбранном товаре
        if not selected_rows:
            self.product_info_label.setText("Выберите товар в таблице")
            self.instructions_label.setText("")
            self.mark_verified_btn.setEnabled(False)
            self.mark_rejected_btn.setEnabled(False)
            
            # Сброс превью
            self.current_photo_path = None
            self.photo_preview_label.setText("📷\nНет фото")
            self.photo_preview_label.setToolTip("")
            self.photo_preview_label.setCursor(Qt.ArrowCursor)
            return
        
        # Кнопки всегда видны, но их доступность управляется ниже
        self.mark_verified_btn.setEnabled(True)
        self.mark_rejected_btn.setEnabled(True)
        self.photo_preview_label.setCursor(Qt.PointingHandCursor)
        self.photo_preview_label.setToolTip("Нажмите, чтобы сделать фото")
            
        row = selected_rows[0].row()
        items = self.results_widget.get_items()
        if row >= len(items):
            return
            
        item = items[row]
        item_uuid = self.results_widget.get_item_uuid(row)
        
        # Проверяем, уже проверен ли товар
        is_verified = item_uuid in self.verified_items
        
        # Загружаем информацию о товаре из БД
        product_info = []
        product_info.append(f"<b>Артикул:</b> {item.article if item.article else '(не распознан)'}")
        product_info.append(f"<b>Наименование:</b> {item.name}")
        product_info.append(f"<b>Количество:</b> {item.quantity} {item.unit}")
        product_info.append("")
        
        # Получить информацию о товаре из БД (с кешированием только для непустых артикулов)
        product = None
        
        # 1. Поиск по артикулу (с кешированием)
        if item.article and item.article.strip():
            if item.article not in self.products_cache:
                try:
                    self.products_cache[item.article] = self.sync_service.get_product_by_article(item.article)
                except Exception as e:
                    logger.error(f"Error fetching product from DB: {e}")
                    self.products_cache[item.article] = None
            product = self.products_cache.get(item.article)
            
        # 2. Fallback: поиск по наименованию (без кеширования по пустому ключу)
        if not product and item.name and item.name.strip():
            try:
                all_products = self.sync_service.get_all_products()
                for p in all_products:
                    if p.name.lower() in item.name.lower() or item.name.lower() in p.name.lower():
                        product = p
                        # Если у товара есть артикул, закешируем его для будущего использования
                        if item.article and item.article.strip():
                            self.products_cache[item.article] = p
                        break
            except Exception as e:
                logger.error(f"Error searching product by name: {e}")
        
        # Показать статус БД
        if product:
            product_info.append("<b style='color: green;'>✅ Товар найден в базе данных</b>")
            if product.requires_control:
                product_info.append("<b style='color: orange;'>⚠️ Требуется входной контроль</b>")
        else:
            product_info.append("<b style='color: red;'>❌ Товар не найден в базе данных</b>")
        
        if is_verified:
            product_info.append("")
            product_info.append("<b style='color: green;'>✓ ПРОВЕРЕНО</b>")
        
        self.product_info_label.setText("<br>".join(product_info))
        
        # Инструкции
        instructions = []
        if product and product.requires_control:
            # Словарь для русских названий типов проверки
            control_type_names = {
                "visual_check": "Визуальный осмотр",
                "VISUAL_CHECK": "Визуальный осмотр",
                "weight_check": "Контроль веса",
                "WEIGHT_CHECK": "Контроль веса",
                "quantity_check": "Подсчет количества",
                "QUANTITY_CHECK": "Подсчет количества",
                "dimension_check": "Измерение размеров",
                "DIMENSION_CHECK": "Измерение размеров"
            }
            
            # Показать тип контроля на русском
            if product.control_type:
                # Работаем со строкой напрямую (не enum)
                control_type_str = product.control_type if isinstance(product.control_type, str) else product.control_type.value
                control_name = control_type_names.get(control_type_str, control_type_str)
                instructions.append(f"<b>Тип контроля:</b> {control_name}")
            
            # Показать параметры проверки
            if product.control_params:
                instructions.append("<b>Необходимые проверки:</b>")
                
                # Если есть готовые инструкции - показать их первыми
                if "instructions" in product.control_params:
                    step_instructions = product.control_params["instructions"]
                    instructions.append("<b>Порядок действий:</b>")
                    # Разбить по переносам строк и добавить
                    for line in step_instructions.split("\n"):
                        if line.strip():
                            instructions.append(line)
                
                # Показать остальные параметры
                # Словарь переводов параметров
                param_translations = {
                    "check_expiration": "Проверить срок годности",
                    "check_integrity": "Проверить целостность",
                    "check_packaging": "Проверить упаковку",
                    "measure_weight": "Взвесить",
                    "count_items": "Посчитать штуки",
                    "target_weight": "Целевой вес",
                    "tolerance": "Допуск",
                    "expected_count": "Ожидаемое кол-во",
                    "length": "Длина",
                    "width": "Ширина",
                    "height": "Высота"
                }

                for param, value in product.control_params.items():
                    if param == "instructions":
                        continue  # Уже показали выше
                    
                    param_ru = param_translations.get(param, param)
                    
                    # Форматирование в зависимости от типа значения
                    if isinstance(value, bool):
                        if value:
                            instructions.append(f"• {param_ru}")
                    elif isinstance(value, (int, float)):
                        instructions.append(f"• {param_ru}: {value}")
                    elif isinstance(value, str):
                        instructions.append(f"• <b>{param_ru}:</b> {value}")
            

        else:
            instructions.append("<b>Стандартная проверка:</b>")
            instructions.append("1. Проверьте внешний вид упаковки")
            instructions.append("2. Убедитесь в отсутствии повреждений")
            instructions.append("3. Сверьте количество с документом")
        
        self.instructions_label.setText("<br>".join(instructions))
        
        # Загрузить данные проверки, если есть
        if is_verified:
            data = self.verified_items[item_uuid]
            self.comment_edit.setText(data.get('comment', ''))
            
            # Загрузить фото
            photos = data.get('photos', [])
            if photos:
                self.current_photo_path = photos[0]
                pixmap = QPixmap(self.current_photo_path)
                self.photo_preview_label.setPixmap(pixmap.scaled(
                    150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation
                ))
                self.photo_preview_label.setToolTip("Нажмите для увеличения")
            else:
                self.current_photo_path = None
                self.photo_preview_label.setText("📷\nНет фото")
                self.photo_preview_label.setToolTip("Нажмите, чтобы сделать фото")
        else:
            self.comment_edit.clear()
            self.current_photo_path = None
            self.photo_preview_label.setText("📷\nНет фото")
            self.photo_preview_label.setToolTip("Нажмите, чтобы сделать фото")
    
    def _mark_verified(self, accepted: bool):
        """Отметить текущий товар как проверенный (принято/отклонено)."""
        selected_rows = self.results_widget.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # Если отклоняем - комментарий обязателен
        comment = self.comment_edit.toPlainText().strip()
        if not accepted and not comment:
            QMessageBox.warning(
                self, 
                "Требуется комментарий", 
                "Для отклонения товара необходимо указать причину в комментарии."
            )
            return
            
        row = selected_rows[0].row()
        item_uuid = self.results_widget.get_item_uuid(row)
        if not item_uuid:
            return
        
        # Сохраняем статус и комментарий, сохраняя фото если есть
        if item_uuid not in self.verified_items:
            self.verified_items[item_uuid] = {}
            
        self.verified_items[item_uuid].update({
            'status': 'verified' if accepted else 'rejected', # Используем 'verified' для согласованности с _create_reception
            'comment': comment
        })
        
        # Обновить визуально строку в таблице - добавить статус в колонку "Проверено"
        status_text = "✓ Принято" if accepted else "✗ Отклонено"
        status_color = QColor("green") if accepted else QColor("red")
        
        verified_item = QTableWidgetItem(status_text)
        verified_item.setForeground(status_color)
        verified_item.setFlags(verified_item.flags() ^ Qt.ItemIsEditable)
        self.results_widget.setItem(row, 6, verified_item)  # Колонка "Проверено"
        
        # Обновить информацию в панели
        self._on_item_selected()
        
        # Проверить, все ли проверены
        self._update_create_button_state()
        
        # Проверяем, все ли товары проверены
        items_with_uuids = self.results_widget.get_items_with_uuids()
        all_verified = True
        
        # Автоматически выбрать следующий непроверенный
        for next_row, (next_uuid, _) in enumerate(items_with_uuids):
            if next_uuid not in self.verified_items or self.verified_items[next_uuid].get('status') not in ('verified', 'rejected'):
                self.results_widget.selectRow(next_row)
                all_verified = False
                return
        
        # Если все проверены - остановить запись
        if all_verified and len(items_with_uuids) > 0:
            if self.camera_service.is_recording():
                self.camera_service.stop_recording()
                self.video_widget.show_status("✓ ЗАПИСЬ ЗАВЕРШЕНА", "#4CAF50")
                self.blink_timer.stop()
            
            QMessageBox.information(self, "Готово", "Все товары проверены! Можно отправить на сервер.")
    
    def _take_photo(self):
        """Сделать фото с камеры."""
        selected_rows = self.results_widget.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        
        # Получить кадр
        image = self.video_widget.get_current_frame()
        if image is None:
            QMessageBox.warning(self, "Ошибка", "Нет изображения с камеры")
            return
            
        # Сохранить во временный файл
        try:
            temp_dir = tempfile.gettempdir()
            # Используем фиксированное имя для перезаписи (одно фото на товар)
            filename = f"tmc_photo_{date.today()}_{row}_0.jpg"
            path = os.path.join(temp_dir, filename)
            image.save(path, "JPG")
            
            # Добавить в verified_items (перезаписываем список фото)
            item_uuid = self.results_widget.get_item_uuid(row)
            if not item_uuid:
                return

            if item_uuid not in self.verified_items:
                self.verified_items[item_uuid] = {'status': 'pending', 'photos': []}
            
            # Всегда перезаписываем список фото, оставляя только одно последнее
            self.verified_items[item_uuid]['photos'] = [path]
            
            # Обновить превью
            self.current_photo_path = path
            pixmap = QPixmap(path)
            scaled = pixmap.scaled(
                self.photo_preview_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.photo_preview_label.setPixmap(scaled)
            self.photo_preview_label.setToolTip("Нажмите для увеличения")
            
            QMessageBox.information(self, "Фото", "Фото сохранено!")
            
        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить фото: {e}")

    def _on_photo_clicked(self, event):
        """Обработка клика по фото: сделать фото или увеличить."""
        # Если товар не выбран, ничего не делаем
        if not self.results_widget.selectionModel().selectedRows():
            return
            
        if self.current_photo_path and os.path.exists(self.current_photo_path):
            self._enlarge_photo(event)
        else:
            self._take_photo()

    def _enlarge_photo(self, event):
        """Увеличить фото по клику."""
        if not self.current_photo_path or not os.path.exists(self.current_photo_path):
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Просмотр фото")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel()
        pixmap = QPixmap(self.current_photo_path)
        
        # Масштабируем под размер экрана, если нужно
        screen_size = dialog.screen().availableGeometry().size()
        if pixmap.width() > screen_size.width() * 0.8 or pixmap.height() > screen_size.height() * 0.8:
            pixmap = pixmap.scaled(
                screen_size.width() * 0.8, 
                screen_size.height() * 0.8, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)
        
        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        
        # Кнопка для удаления/пересъемки фото
        actions_layout = QHBoxLayout()
        
        retake_btn = QPushButton("📷 Переснять")
        retake_btn.clicked.connect(lambda: [dialog.close(), self._take_photo()])
        actions_layout.addWidget(retake_btn)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        actions_layout.addWidget(close_btn)
        
        layout.addLayout(actions_layout)
        
        dialog.exec()

    def _update_create_button_state(self):
        """Обновить состояние кнопки создания приёмки."""
        items_with_uuids = self.results_widget.get_items_with_uuids()
        
        # Считаем только те, которые есть в таблице
        verified_count = 0
        for uuid, _ in items_with_uuids:
            if uuid in self.verified_items:
                # Проверяем, что статус verified или rejected (не pending)
                status = self.verified_items[uuid].get('status')
                if status in ('verified', 'rejected'):
                    verified_count += 1
                    
        remaining = len(items_with_uuids) - verified_count
        all_verified = remaining == 0 and len(items_with_uuids) > 0
        
        # Обновить счетчик
        if len(items_with_uuids) > 0:
            if remaining > 0:
                self.counter_label.setText(f"⚠️ Осталось проверить: {remaining} товар(ов)")
                self.counter_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.counter_label.setText("✓ Все товары проверены")
                self.counter_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.counter_label.setText("")
        
        self.create_btn.setEnabled(all_verified)
        
        if all_verified:
            self.create_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        else:
            self.create_btn.setStyleSheet("background-color: #cccccc; font-weight: bold; padding: 10px;")
    
    def _start_camera(self, auto_record=False):
        """Запустить камеру."""
        if not self.camera_active:
            self.camera_service.start_preview()
            self.camera_active = True
            logger.info("Camera started")
            
            # Переключиться на вкладку "Видео"
            self.content_tabs.setCurrentIndex(0)
            
            if auto_record:
                # Небольшая задержка перед стартом записи, чтобы камера успела инициализироваться
                QTimer.singleShot(500, self._start_recording_internal)

    def _start_recording_internal(self):
        """Внутренний метод для старта записи."""
        if self.camera_active and not self.camera_service.is_recording():
             temp_dir = Path("temp_video")
             self.camera_service.start_recording(temp_dir)
    
    def _stop_camera(self):
        """Остановить камеру."""
        if self.camera_active:
            if self.camera_service.is_recording():
                self.camera_service.stop_recording()
            self.camera_service.stop_preview()
            self.camera_active = False
            self.blink_timer.stop()
            self.video_widget.hide_status()
            logger.info("Camera stopped")
    
    def _on_recording_started(self):
        """Обработка начала записи."""
        logger.info("Recording started")
        self.video_widget.start_recording_info()
        self.video_widget.show_status("🔴 ИДЕТ ЗАПИСЬ", "red")
        
        self.blink_timer.start(1000)
        self.blink_state = True
    
    def _on_recording_stopped(self, path: str):
        """Обработка остановки записи."""
        self.current_video_path = path  # Сохраняем путь
        logger.info(f"Recording stopped: {path}")
        
        # Скрыть информацию о записи
        self.video_widget.stop_recording_info()
        self.video_widget.show_status("⏹ ЗАПИСЬ ОСТАНОВЛЕНА", "gray")
        self.blink_timer.stop()
    
    def _on_recording_limit_exceeded(self, message: str):
        """Обработка превышения лимита записи."""
        logger.info(f"Recording limit exceeded: {message}")
        self.video_widget.show_limit_exceeded(message)
        self.blink_timer.stop()
        self.video_widget.show_status("🔴 ЗАПИСЬ ОСТАНОВЛЕНА (ЛИМИТ)", "#ff8800")
    
    def _blink_recording_indicator(self):
        """Мигание индикатора записи."""
        self.blink_state = not self.blink_state
        if self.blink_state:
            self.video_widget.show_status("🔴 ИДЕТ ЗАПИСЬ", "red")
        else:
            self.video_widget.show_status("🔴 ИДЕТ ЗАПИСЬ", "#800000") # Dark red
    
    def closeEvent(self, event):
        """Остановить камеру при закрытии."""
        self._stop_camera()
        super().closeEvent(event)
    
    def _reset_all(self):
        """Сброс всего состояния диалога."""
        logger.info("Resetting dialog state")
        
        # 1. Остановить камеру
        self._stop_camera()
        
        # 2. Очистить данные
        self.current_file = None
        self.current_video_path = None
        self.ocr_result = None
        self.verified_items.clear()
        self.products_cache.clear()
        
        # 3. Сбросить UI элементы
        self.file_path_label.setText("Файл не выбран")
        self.file_path_label.setStyleSheet("color: gray;")
        self.preview_label.setText("Превью")
        self.preview_label.setPixmap(QPixmap())
        
        self.ttn_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.supplier_edit.clear()
        
        self.results_widget.set_items([])
        self.counter_label.setText("")
        
        self.product_info_label.setText("Выберите товар в таблице")
        self.instructions_label.setText("")
        self.comment_edit.clear()
        
        # 4. Сбросить состояние кнопок
        self.select_btn.setEnabled(True)
        self.reset_btn.setEnabled(False)
        self.create_btn.setEnabled(False)
        
        self.mark_verified_btn.hide()
        self.mark_rejected_btn.hide()
        self.comment_edit.hide()
        
        logger.info("Reset completed")

    def _show_database(self):
        """Открыть диалог просмотра базы данных."""
        dialog = DatabaseDialog(self.sync_service, self)
        dialog.exec()
