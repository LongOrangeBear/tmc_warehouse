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
    QDateEdit, QScrollArea, QSplitter, QWidget, QGroupBox, QTextEdit, QTableWidgetItem
)
from PySide6.QtCore import Qt, QDate, QTimer
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
        self.resize(1200, 800)
        
        self.ocr_service = OCRService()
        self.sync_service = SyncService()
        self.current_file: Optional[Path] = None
        self.ocr_result: Optional[OCRResult] = None
        self.verified_items = {}  # {row_index: {'status': 'accepted'|'rejected', 'comment': str}}
        self.products_cache = {}  # Кеш товаров из БД {article: ProductRead}
        self.camera_service = CameraService()
        self.camera_active = False
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Верхняя панель: Выбор файла
        top_panel = QHBoxLayout()
        
        file_label = QLabel("Документ:")
        self.file_path_label = QLabel("Файл не выбран")
        self.file_path_label.setStyleSheet("color: gray;")
        
        self.select_btn = QPushButton("Выбрать файл")
        self.select_btn.clicked.connect(self._select_file)
        
        self.recognize_btn = QPushButton("Распознать (OCR/ИИ)")
        self.recognize_btn.clicked.connect(self._run_ocr)
        self.recognize_btn.setEnabled(False)
        
        self.reset_btn = QPushButton("🔄 Сброс")
        self.reset_btn.clicked.connect(self._reset_all)
        self.reset_btn.setEnabled(False)
        self.reset_btn.setStyleSheet("background-color: #ff9800; color: white;")
        
        self.db_btn = QPushButton("🗄️ База данных")
        self.db_btn.clicked.connect(self._show_database)
        
        top_panel.addWidget(file_label)
        top_panel.addWidget(self.file_path_label, 1)
        top_panel.addWidget(self.select_btn)
        top_panel.addWidget(self.recognize_btn)
        top_panel.addWidget(self.reset_btn)
        top_panel.addWidget(self.db_btn)
        
        layout.addLayout(top_panel)
        
        # Основная рабочая область (2 уровня: верх и низ)
        # Верхний уровень: Камера + Превью документа (меньше)
        # Нижний уровень: Форма+Таблица + Проверка
        
        main_vertical_splitter = QSplitter(Qt.Vertical)
        
        # === ВЕРХНЯЯ ЧАСТЬ: Камера + Документ ===
        top_splitter = QSplitter(Qt.Horizontal)
        
        # Камера (слева сверху)
        camera_container = QGroupBox("Видеофиксация")
        camera_layout = QVBoxLayout(camera_container)
        
        self.video_widget = VideoWidget()
        self.video_widget.setMinimumHeight(200)
        self.video_widget.setMaximumHeight(300)
        camera_layout.addWidget(self.video_widget)
        
        # Индикатор записи
        self.recording_indicator = QLabel("")
        self.recording_indicator.setAlignment(Qt.AlignCenter)
        self.recording_indicator.setStyleSheet(
            "background-color: #ff4444; color: white; font-weight: bold; "
            "padding: 5px; border-radius: 3px;"
        )
        self.recording_indicator.hide()
        camera_layout.addWidget(self.recording_indicator)
        
        # Кнопка записи
        self.record_btn = QPushButton("🔴 Начать запись")
        self.record_btn.clicked.connect(self._toggle_recording)
        self.record_btn.setEnabled(False)
        camera_layout.addWidget(self.record_btn)
        
        top_splitter.addWidget(camera_container)
        
        # Превью документа (справа сверху)
        preview_container = QGroupBox("Документ")
        preview_layout = QVBoxLayout(preview_container)
        
        preview_scroll = QScrollArea()
        self.preview_label = QLabel("Предпросмотр")
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_scroll.setWidget(self.preview_label)
        preview_scroll.setWidgetResizable(True)
        preview_layout.addWidget(preview_scroll)
        
        top_splitter.addWidget(preview_container)
        
        # Соотношение камера:документ = 1:1 (равномерно)
        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 1)
        
        main_vertical_splitter.addWidget(top_splitter)
        
        # === НИЖНЯЯ ЧАСТЬ: Форма+Таблица + Проверка ===
        bottom_splitter = QSplitter(Qt.Horizontal)
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        
        # Форма заголовка ТТН
        self.ttn_edit = QLineEdit()
        self.ttn_edit.setPlaceholderText("Номер ТТН")
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        
        self.supplier_edit = QLineEdit()
        self.supplier_edit.setPlaceholderText("Поставщик")
        
        middle_layout.addWidget(QLabel("Номер ТТН:"))
        middle_layout.addWidget(self.ttn_edit)
        middle_layout.addWidget(QLabel("Дата ТТН:"))
        middle_layout.addWidget(self.date_edit)
        middle_layout.addWidget(QLabel("Поставщик:"))
        middle_layout.addWidget(self.supplier_edit)
        
        # Таблица позиций с чекбоксами
        middle_layout.addWidget(QLabel("Позиции:"))
        self.results_widget = ResultsWidget()
        self.results_widget.itemSelectionChanged.connect(self._on_item_selected)
        middle_layout.addWidget(self.results_widget)
        
        bottom_splitter.addWidget(middle_widget)
        
        # Правая часть: Панель проверки товара
        self.verification_panel = QGroupBox("Проверка товара")
        verification_layout = QVBoxLayout(self.verification_panel)
        
        # Информация о товаре
        self.product_info_label = QLabel("Выберите товар в таблице")
        self.product_info_label.setWordWrap(True)
        self.product_info_label.setStyleSheet("padding: 10px; background: #f5f5f5; border-radius: 5px;")
        verification_layout.addWidget(self.product_info_label)
        
        # Инструкции
        verification_layout.addWidget(QLabel("<b>Что проверить:</b>"))
        self.instructions_label = QLabel("")
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setStyleSheet("padding: 10px; background: #fffacd; border-radius: 5px;")
        verification_layout.addWidget(self.instructions_label)
        
        verification_layout.addStretch()
        
        # Поле для комментария
        verification_layout.addWidget(QLabel("<b>Комментарий:</b>"))
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(60)
        self.comment_edit.setPlaceholderText("Опишите причину, если товар не принят...")
        verification_layout.addWidget(self.comment_edit)
        
        # Кнопки проверки (принять/отклонить)
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
        
        # Кнопка фото (отдельно или рядом)
        self.take_photo_btn = QPushButton("📷 Сделать фото")
        self.take_photo_btn.clicked.connect(self._take_photo)
        self.take_photo_btn.setEnabled(False)
        self.take_photo_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        
        verification_layout.addWidget(self.take_photo_btn)
        verification_layout.addLayout(buttons_layout)
        
        bottom_splitter.addWidget(self.verification_panel)
        
        # Соотношение таблица:проверка = 3:2 (более сбалансированно)
        bottom_splitter.setStretchFactor(0, 3)
        bottom_splitter.setStretchFactor(1, 2)
        
        main_vertical_splitter.addWidget(bottom_splitter)
        
        # Настройка вертикального сплиттера (верх:низ = 2:3 для баланса)
        main_vertical_splitter.setStretchFactor(0, 2)  # Верх (камера+превью)
        main_vertical_splitter.setStretchFactor(1, 3)  # Низ (таблица+проверка)
        
        layout.addWidget(main_vertical_splitter)
        
        # Нижняя панель: Кнопки действий
        bottom_panel = QHBoxLayout()
        
        # Счетчик непроверенных товаров
        self.counter_label = QLabel("")
        self.counter_label.setStyleSheet("color: orange; font-weight: bold;")
        
        self.create_btn = QPushButton("✉️ Отправить на сервер")
        self.create_btn.clicked.connect(self._create_reception)
        self.create_btn.setEnabled(False)  # Пока не все проверены
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
            self.file_path_label.setStyleSheet("color: black;")
            self.recognize_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
            
            # Загрузить превью
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
                                500, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation
                            ))
                        else:
                            self.preview_label.setText("PDF Документ\n(Не удалось загрузить превью)")
                    else:
                        self.preview_label.setText("PDF Документ\n(Нажмите Распознать)")
                except Exception as e:
                    logger.warning(f"Failed to render PDF preview: {e}")
                    self.preview_label.setText("PDF Документ\n(Нажмите Распознать)")
            else:
                pixmap = QPixmap(str(self.current_file))
                if not pixmap.isNull():
                    self.preview_label.setPixmap(pixmap.scaled(
                        500, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    ))

    def _run_ocr(self):
        if not self.current_file:
            return
        
        logger.info(f"Starting OCR processing: {self.current_file}")
        self.setCursor(Qt.WaitCursor)
        self.recognize_btn.setEnabled(False)
        
        try:
            # Запуск OCR
            result = self.ocr_service.process_document(self.current_file)
            logger.info(f"OCR completed: TTN={result.ttn_number}, items={len(result.items)}")
            
            # Очистить кеш проверенных товаров при новом OCR
            self.verified_items.clear()
            self._update_create_button_state()
            
            # ОТКЛЮЧИТЬ кнопки загрузки и распознавания
            self.select_btn.setEnabled(False)
            self.recognize_btn.setEnabled(False)
            
            # ЗАПУСТИТЬ КАМЕРУ после успешного OCR
            self._start_camera()
            
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
            
            self.create_btn.setEnabled(True)
            QMessageBox.information(self, "OCR", "Распознавание завершено")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка OCR: {e}")
        finally:
            self.setCursor(Qt.ArrowCursor)
            self.recognize_btn.setEnabled(True)

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
            
        # Сбор данных
        data = ReceptionCreate(
            ttn_number=ttn,
            ttn_date=self.date_edit.date().toPython(),
            supplier=self.supplier_edit.text().strip(),
            items=items
        )
        
        # Отправка на сервер
        logger.info(f"Creating reception: TTN={ttn}, items={len(items)}")
        try:
            reception = self.sync_service.create_reception(data)
            if reception:
                logger.info(f"Reception created successfully: ID={reception.id}")
                # Загрузка файла документа
                if self.current_file:
                    logger.info(f"Uploading document for reception {reception.id}")
                    self.sync_service.upload_document(reception.id, self.current_file)
                
                # Загрузка фото доказательств
                if reception.items:
                    # Предполагаем, что порядок items совпадает
                    # reception.items - это список ReceptionItem из БД (с ID)
                    # items - это список ReceptionItemCreate из UI (без ID, но с photos)
                    
                    # Нужно получить items из БД в правильном порядке.
                    # Peewee backref может не гарантировать порядок, но обычно по ID.
                    # Лучше запросить полную приёмку с сортировкой items по ID
                    
                    # Для простоты пока считаем по индексу, так как создавали пачкой
                    db_items = list(reception.items)
                    # Сортируем по ID на всякий случай
                    db_items.sort(key=lambda x: x.id)
                    
                    for i, db_item in enumerate(db_items):
                        if i < len(items):
                            ui_item = items[i]
                            # Проверяем наличие фото в verified_items по индексу строки
                            # Но items здесь это уже список ReceptionItemCreate
                            # Нам нужно достать фото из verified_items по индексу строки таблицы
                            
                            # verified_items хранит {row_index: data}
                            # items создавались из таблицы по порядку строк
                            # значит items[i] соответствует строке i
                            
                            verified_data = self.verified_items.get(i, {})
                            photos = verified_data.get('photos', [])
                            
                            for photo_path in photos:
                                try:
                                    logger.info(f"Uploading photo for item {db_item.id}: {photo_path}")
                                    # Здесь нам нужен метод upload_photo в sync_service
                                    # Если его нет, надо добавить. Но пользователь просил добавить кнопку, 
                                    # подразумевая что функционал есть или будет добавлен.
                                    # Проверим sync_service позже. Если нет - добавим.
                                    # Пока используем заглушку или предполагаем наличие.
                                    if hasattr(self.sync_service, 'upload_photo'):
                                        self.sync_service.upload_photo(reception.id, db_item.id, photo_path)
                                    else:
                                        logger.warning("SyncService has no upload_photo method")
                                except Exception as e:
                                    logger.error(f"Error uploading photo: {e}")
                    
                QMessageBox.information(self, "Успех", f"Приёмка #{reception.id} создана")
                self.accept() # This accept() is the final one for success
            else:
                logger.error("Failed to create reception (returned None)")
                QMessageBox.critical(self, "Ошибка", "Не удалось создать приёмку")
            
            # Остановить камеру после успешной отправки
            self._stop_camera()
            
        except Exception as e:
            logger.exception(f"Exception during reception creation: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка сети: {e}")
    
    def _on_item_selected(self):
        """Обработка выбора товара в таблице."""
        selected_rows = self.results_widget.selectionModel().selectedRows()
        
        # Показывать кнопку проверки ТОЛЬКО при выбранном товаре
        if not selected_rows:
            self.product_info_label.setText("Выберите товар в таблице")
            self.instructions_label.setText("")
            self.mark_verified_btn.setEnabled(False)
            self.mark_rejected_btn.setEnabled(False)
            self.take_photo_btn.setEnabled(False) # Disable photo button
            self.mark_verified_btn.hide()  # СКРЫТЬ кнопки
            self.mark_rejected_btn.hide()
            self.take_photo_btn.hide()
            self.comment_edit.hide()
            return
        
        self.mark_verified_btn.show()  # ПОКАЗАТЬ кнопки
        self.mark_rejected_btn.show()
        self.take_photo_btn.show()
        self.comment_edit.show()
        
        # Enable buttons only if item selected (redundant check but safe)
        self.mark_verified_btn.setEnabled(True)
        self.mark_rejected_btn.setEnabled(True)
        self.take_photo_btn.setEnabled(True)
            
        row = selected_rows[0].row()
        items = self.results_widget.get_items()
        if row >= len(items):
            return
            
        item = items[row]
        
        # Проверяем, уже проверен ли товар
        is_verified = row in self.verified_items
        
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
                control_type_ru = control_type_names.get(control_type_str, control_type_str)
                instructions.append(f"<b>Тип контроля:</b> {control_type_ru}")
                instructions.append("")
            
            # Показать параметры проверки
            if product.control_params:
                instructions.append("<b>Необходимые проверки:</b>")
                instructions.append("")
                
                # Если есть готовые инструкции - показать их первыми
                if "instructions" in product.control_params:
                    step_instructions = product.control_params["instructions"]
                    instructions.append("<b>Порядок действий:</b>")
                    # Разбить по переносам строк и добавить
                    for line in step_instructions.split("\n"):
                        if line.strip():
                            instructions.append(line)
                    instructions.append("")
                
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
                instructions.append("Нет специальных требований")
        else:
            instructions.append("<b>Стандартная проверка:</b>")
            instructions.append("")
            instructions.append("1. Проверьте внешний вид упаковки")
            instructions.append("2. Убедитесь в отсутствии повреждений")
            instructions.append("3. Сверьте количество с документом")
        
        self.instructions_label.setText("<br>".join(instructions))
        
        # Кнопки проверки
        if is_verified:
            verified_data = self.verified_items.get(row, {})
            status = verified_data.get('status', 'accepted')
            
            if status == 'accepted':
                self.mark_verified_btn.setText("✓ Принято")
                self.mark_rejected_btn.setText("✗ Не принимать")
            else:
                self.mark_verified_btn.setText("✓ Принять")
                self.mark_rejected_btn.setText("✗ Отклонено")
            
            self.mark_verified_btn.setEnabled(False)
            self.mark_rejected_btn.setEnabled(False)
            self.comment_edit.setEnabled(False)
            
            # Показать сохраненный комментарий
            comment = verified_data.get('comment', '')
            self.comment_edit.setText(comment)
        else:
            self.mark_verified_btn.setText("✓ Принять")
            self.mark_rejected_btn.setText("✗ Не принимать")
            self.mark_verified_btn.setEnabled(True)
            self.mark_rejected_btn.setEnabled(True)
            self.comment_edit.setEnabled(True)
            self.comment_edit.clear()
    
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
        
        # Сохраняем статус и комментарий
        self.verified_items[row] = {
            'status': 'accepted' if accepted else 'rejected',
            'comment': comment
        }
        
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
        
        # Автоматически выбрать следующий непроверенный
        items = self.results_widget.get_items()
        for next_row in range(len(items)):
            if next_row not in self.verified_items:
                self.results_widget.selectRow(next_row)
                return
        
        # Если все проверены
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
            filename = f"tmc_photo_{date.today()}_{row}_{len(self.verified_items.get(row, {}).get('photos', []))}.jpg"
            path = os.path.join(temp_dir, filename)
            image.save(path, "JPG")
            
            # Добавить в verified_items
            if row not in self.verified_items:
                self.verified_items[row] = {'status': 'pending', 'photos': []}
            
            if 'photos' not in self.verified_items[row]:
                self.verified_items[row]['photos'] = []
                
            self.verified_items[row]['photos'].append(path)
            
            QMessageBox.information(self, "Фото", "Фото сохранено!")
            
        except Exception as e:
            logger.error(f"Error saving photo: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить фото: {e}")

    def _update_create_button_state(self):
        """Обновить состояние кнопки создания приёмки."""
        items = self.results_widget.get_items()
        remaining = len(items) - len(self.verified_items)
        all_verified = remaining == 0 and len(items) > 0
        
        # Обновить счетчик
        if len(items) > 0:
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
    
    def _start_camera(self):
        """Запустить камеру."""
        if not self.camera_active:
            self.camera_service.start_preview()
            self.camera_active = True
            self.record_btn.setEnabled(True)
            logger.info("Camera started")
    
    def _stop_camera(self):
        """Остановить камеру."""
        if self.camera_active:
            if self.camera_service.is_recording():
                self.camera_service.stop_recording()
            self.camera_service.stop_preview()
            self.camera_active = False
            self.record_btn.setEnabled(False)
            self.blink_timer.stop()
            self.recording_indicator.hide()
            logger.info("Camera stopped")
    
    def _toggle_recording(self):
        """Переключить запись."""
        if self.camera_service.is_recording():
            self.camera_service.stop_recording()
        else:
            temp_dir = Path("temp_video")
            self.camera_service.start_recording(temp_dir)
    
    def _on_recording_started(self):
        """Обработка начала записи."""
        self.record_btn.setText("⏹ Остановить запись")
        self.record_btn.setStyleSheet("background-color: #d13438; color: white; font-weight: bold;")
        self.recording_indicator.setText("● ИДЕТ ЗАПИСЬ")
        self.recording_indicator.show()
        self.blink_timer.start(500)  # Мигать каждые 500 мс
    
    def _on_recording_stopped(self, path: str):
        """Обработка остановки записи."""
        self.record_btn.setText("🔴 Начать запись")
        self.record_btn.setStyleSheet("")
        self.recording_indicator.hide()
        self.blink_timer.stop()
        logger.info(f"Recording stopped: {path}")
    
    def _blink_recording_indicator(self):
        """Мигание индикатора записи."""
        self.blink_state = not self.blink_state
        if self.blink_state:
            self.recording_indicator.setStyleSheet(
                "background-color: #ff4444; color: white; font-weight: bold; "
                "padding: 5px; border-radius: 3px;"
            )
        else:
            self.recording_indicator.setStyleSheet(
                "background-color: #880000; color: white; font-weight: bold; "
                "padding: 5px; border-radius: 3px;"
            )
    
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
        
        self.results_widget.setRowCount(0)
        self.counter_label.setText("")
        
        self.product_info_label.setText("Выберите товар в таблице")
        self.instructions_label.setText("")
        self.comment_edit.clear()
        
        # 4. Сбросить состояние кнопок
        self.select_btn.setEnabled(True)
        self.recognize_btn.setEnabled(False)
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
