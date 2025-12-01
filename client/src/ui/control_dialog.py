"""Диалог проведения входного контроля."""
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QStackedWidget, 
    QGroupBox, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QTimer

from client.src.services import (
    CameraService, ValidatorService, SyncService, StorageService
)
from client.src.ui.video_widget import VideoWidget
from common.models import (
    ReceptionRead, ReceptionItemRead, ControlType, 
    ReceptionItemControlUpdate, ControlStatus
)


class ControlDialog(QDialog):
    """Диалог выполнения контроля."""

    def __init__(self, reception: ReceptionRead, parent=None):
        super().__init__(parent)
        self.reception = reception
        self.setWindowTitle(f"Входной контроль - Приёмка #{reception.id}")
        self.resize(1000, 700)
        
        self.camera_service = CameraService()
        self.validator_service = ValidatorService()
        self.sync_service = SyncService()
        self.storage_service = StorageService()
        
        self.current_item: Optional[ReceptionItemRead] = None
        self.results: List[ReceptionItemControlUpdate] = []
        
        self._setup_ui()
        self._load_items()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Левая панель: Список позиций
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Позиции для контроля:"))
        self.items_list = QListWidget()
        self.items_list.currentRowChanged.connect(self._on_item_selected)
        left_layout.addWidget(self.items_list)
        
        layout.addLayout(left_layout, 1)
        
        # Правая панель: Рабочая область
        right_layout = QVBoxLayout()
        
        # Видео
        self.video_widget = VideoWidget()
        self.video_widget.setMinimumHeight(300)
        right_layout.addWidget(self.video_widget)
        
        # Инструкции и ввод
        self.info_group = QGroupBox("Информация о товаре")
        info_layout = QVBoxLayout(self.info_group)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        right_layout.addWidget(self.info_group)
        
        self.instruction_group = QGroupBox("Инструкция контролёра")
        inst_layout = QVBoxLayout(self.instruction_group)
        self.instruction_label = QLabel()
        self.instruction_label.setWordWrap(True)
        inst_layout.addWidget(self.instruction_label)
        right_layout.addWidget(self.instruction_group)
        
        # Поле для заметок
        right_layout.addWidget(QLabel("Заметки:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        right_layout.addWidget(self.notes_edit)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        
        self.photo_btn = QPushButton("📷 Сделать фото")
        self.photo_btn.clicked.connect(self._take_photo)
        
        self.record_btn = QPushButton("🔴 Начать запись")
        self.record_btn.clicked.connect(self._toggle_recording)
        
        self.pass_btn = QPushButton("✅ Контроль пройден")
        self.pass_btn.clicked.connect(lambda: self._submit_result(True))
        self.pass_btn.setStyleSheet("background-color: #107c10;") # Green
        
        self.fail_btn = QPushButton("❌ Отклонить")
        self.fail_btn.clicked.connect(lambda: self._submit_result(False))
        self.fail_btn.setStyleSheet("background-color: #d13438;") # Red
        
        btn_layout.addWidget(self.photo_btn)
        btn_layout.addWidget(self.record_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.pass_btn)
        btn_layout.addWidget(self.fail_btn)
        
        right_layout.addLayout(btn_layout)
        
        layout.addLayout(right_layout, 2)
        
        # Подключение сигналов камеры
        self.camera_service.frame_ready.connect(self.video_widget.update_frame)
        self.camera_service.recording_started.connect(self._on_recording_started)
        self.camera_service.recording_stopped.connect(self._on_recording_stopped)
        self.camera_service.error.connect(self._on_camera_error)

    def _load_items(self):
        self.items_list.clear()
        self.pending_items = [
            item for item in self.reception.items 
            if item.control_required and item.control_status == ControlStatus.PENDING
        ]
        
        for item in self.pending_items:
            self.items_list.addItem(f"{item.article} - {item.name}")
            
        if self.pending_items:
            self.items_list.setCurrentRow(0)
            self.camera_service.start_preview()
        else:
            QMessageBox.information(self, "Готово", "Все позиции проверены")
            self.accept()

    def _on_item_selected(self, row: int):
        if row < 0 or row >= len(self.pending_items):
            return
            
        self.current_item = self.pending_items[row]
        
        # === ИНФОРМАЦИЯ О ТОВАРЕ ===
        info_parts = []
        info_parts.append(f"<b>Артикул:</b> {self.current_item.article}")
        info_parts.append(f"<b>Наименование:</b> {self.current_item.name}")
        info_parts.append(f"<b>Количество:</b> {self.current_item.quantity} {self.current_item.unit}")
        
        # Статус сверки с БД
        if self.current_item.product_id:
            info_parts.append("")
            info_parts.append("<b style='color: green;'>✅ Товар найден в базе данных</b>")
            if self.current_item.control_required:
                info_parts.append("<b style='color: orange;'>⚠️ Требуется входной контроль</b>")
        else:
            info_parts.append("")
            info_parts.append("<b style='color: red;'>❌ Товар НЕ найден в базе данных</b>")
            info_parts.append("<i>Выполните стандартную проверку</i>")
        
        self.info_label.setText("<br>".join(info_parts))
        
        # === АЛГОРИТМ ПРОВЕРКИ ===
        instructions = []
        
        if self.current_item.control_type:
            instructions.append("<b>📋 АЛГОРИТМ ПРОВЕРКИ:</b>")
            instructions.append("")
            instructions.append(f"<b>Тип контроля:</b> {self.current_item.control_type.value}")
            instructions.append("")
            
            params = self.current_item.control_params or {}
            if params:
                instructions.append("<b>Параметры из базы данных:</b>")
                for k, v in params.items():
                    instructions.append(f"  • {k}: <b>{v}</b>")
                    
                # Добавим конкретные инструкции в зависимости от типа
                instructions.append("")
                instructions.append("<b>Порядок действий:</b>")
                if self.current_item.control_type.value == "VISUAL_CHECK":
                    instructions.append("1. Осмотрите товар на предмет повреждений")
                    instructions.append("2. Проверьте соответствие параметрам выше")
                    instructions.append("3. При обнаружении дефектов - сделайте фото")
                elif self.current_item.control_type.value == "WEIGHT_CHECK":
                    instructions.append("1. Взвесьте товар")
                    instructions.append("2. Убедитесь, что вес в допустимых пределах")
                    instructions.append("3. Зафиксируйте результат в заметках")
                elif self.current_item.control_type.value == "QUANTITY_CHECK":
                    instructions.append("1. Пересчитайте количество единиц")
                    instructions.append("2. Сверьте с указанным в документе")
                    instructions.append("3. При расхождении - укажите фактическое количество")
        else:
            instructions.append("<b>📋 СТАНДАРТНАЯ ПРОВЕРКА:</b>")
            instructions.append("")
            instructions.append("1. Проверьте внешний вид упаковки")
            instructions.append("2. Убедитесь в отсутствии повреждений")
            instructions.append("3. Сверьте количество с документом")
            
        self.instruction_label.setText("<br>".join(instructions))
        
        self.notes_edit.clear()
        self.pass_btn.setEnabled(True)
        self.fail_btn.setEnabled(True)

    def _take_photo(self):
        """Сделать фото."""
        if not self.current_item:
            return
            
        jpeg_data = self.camera_service.take_snapshot()
        if jpeg_data:
            try:
                path = self.storage_service.save_photo(
                    jpeg_data, 
                    self.reception.id, 
                    self.reception.ttn_date, 
                    self.current_item.id
                )
                
                # Показать сообщение или обновить UI
                # В этой версии просто добавим в заметки путь
                current_notes = self.notes_edit.toPlainText()
                new_note = f"Фото: {path.name}"
                if current_notes:
                    self.notes_edit.setText(f"{current_notes}\n{new_note}")
                else:
                    self.notes_edit.setText(new_note)
                    
                # Отправить на сервер (если нужно сразу)
                # self.sync_service.upload_photo(...)
                
                QMessageBox.information(self, "Фото", f"Фото сохранено: {path.name}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить фото: {e}")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить кадр с камеры")

    def _toggle_recording(self):
        if self.camera_service.is_recording():
            self.camera_service.stop_recording()
        else:
            # Временная папка, потом переместим
            temp_dir = Path("temp_video")
            try:
                self.camera_service.start_recording(temp_dir)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось начать запись: {e}")

    def _on_recording_started(self):
        self.record_btn.setText("⏹ Остановить запись")
        self.record_btn.setStyleSheet("background-color: #d13438;")

    def _on_recording_stopped(self, path: str):
        self.record_btn.setText("🔴 Начать запись")
        self.record_btn.setStyleSheet("")
        
        # Сохраняем видео
        if self.current_item:
            try:
                saved_path = self.storage_service.move_video(
                    Path(path), 
                    self.reception.id, 
                    self.reception.ttn_date
                )
                # Отправляем на сервер
                self.sync_service.upload_video(self.reception.id, saved_path)
                QMessageBox.information(self, "Видео", "Видео сохранено и загружено")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Ошибка сохранения видео: {e}")

    def _on_camera_error(self, msg: str):
        QMessageBox.warning(self, "Ошибка камеры", msg)

    def _submit_result(self, passed: bool):
        if not self.current_item:
            return
            
        result = ReceptionItemControlUpdate(
            id=self.current_item.id,
            control_status=ControlStatus.PASSED if passed else ControlStatus.FAILED,
            control_result={"passed": passed},
            notes=self.notes_edit.toPlainText()
        )
        
        self.results.append(result)
        
        # Отправляем сразу или накапливаем? Отправим сразу для простоты
        try:
            self.sync_service.send_control_results(self.reception.id, [result])
        except Exception as e:
            QMessageBox.warning(self, "Ошибка сети", f"Не удалось отправить результат: {e}")
            return

        # Переход к следующему
        row = self.items_list.currentRow()
        # Удаляем из списка (визуально)
        self.items_list.takeItem(row)
        del self.pending_items[row]
        
        if self.pending_items:
            # Выбираем следующий (тот же индекс, так как сместилось)
            new_row = min(row, len(self.pending_items) - 1)
            self.items_list.setCurrentRow(new_row)
        else:
            QMessageBox.information(self, "Завершено", "Контроль завершен")
            self.accept()

    def closeEvent(self, event):
        self.camera_service.stop_preview()
        super().closeEvent(event)
