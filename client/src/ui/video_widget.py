"""Виджет для отображения видео с камеры."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Slot, QTimer, QDateTime
from PySide6.QtGui import QImage, QPixmap, QPainter, QFont, QColor


class VideoWidget(QWidget):
    """Виджет для отображения видеопотока с фиксированным аспектом."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.setMinimumSize(320, 240)
        
        self.current_image = None
        self.recording_start_time = None
        self.video_size_bytes = 0
        self.video_aspect_ratio = 16 / 9
        self.is_fullscreen = False
        self.limit_exceeded = False
        self.limit_message = ""
        
        # Overlay label для информации (слева сверху)
        self.info_label = QLabel(self)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 8px 12px;
                font-family: monospace;
                font-size: 12px;
                border-radius: 4px;
            }
        """)
        self.info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.info_label.hide()
        
        # Overlay label для статуса (справа сверху)
        self.status_label = QLabel(self)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 0, 0, 200);
                color: white;
                padding: 8px 12px;
                font-family: sans-serif;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.hide()
        
        # Overlay для сообщения о превышении лимита
        self.limit_label = QLabel(self)
        self.limit_label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 0, 0, 200);
                color: white;
                padding: 20px;
                font-family: sans-serif;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid white;
            }
        """)
        self.limit_label.setAlignment(Qt.AlignCenter)
        self.limit_label.setWordWrap(True)
        self.limit_label.hide()
        
        # Таймер для обновления времени записи
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_info)
        
        self.layout.addWidget(self.image_label)

    @Slot(QImage)
    def update_frame(self, image: QImage):
        """Обновить кадр с сохранением аспекта."""
        self.current_image = image.copy()
        
        if image.width() > 0 and image.height() > 0:
            self.video_aspect_ratio = image.width() / image.height()
        
        self._update_display()
    
    def _update_display(self):
        """Обновить отображение с учетом аспекта."""
        if not self.current_image:
            return
            
        pixmap = QPixmap.fromImage(self.current_image)
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def clear(self):
        """Очистить изображение."""
        self.image_label.clear()
        self.image_label.setText("Нет сигнала")
        self.current_image = None

    def get_current_frame(self) -> QImage:
        """Получить текущий кадр."""
        return self.current_image
    
    def sizeHint(self):
        """Предложить размер с сохранением aspect ratio 16:9."""
        from PySide6.QtCore import QSize
        # Базовый размер при aspect 16:9
        return QSize(960, 540)  # 16:9 aspect ratio
    
    def hasHeightForWidth(self):
        """Виджет поддерживает фиксированный aspect ratio."""
        return True
    
    def heightForWidth(self, width):
        """Вычислить высоту на основе ширины для сохранения aspect ratio 16:9."""
        # Для aspect 16:9: height = width * 9 / 16
        return int(width * 9 / 16)

    
    def start_recording_info(self):
        """Начать отображение информации о записи."""
        from datetime import datetime
        self.recording_start_time = datetime.now()
        self.video_size_bytes = 0
        self.limit_exceeded = False
        self.limit_message = ""
        self.info_label.show()
        self.limit_label.hide()
        self.update_timer.start(1000)
        self._update_info()
        self._position_overlays()
    
    def stop_recording_info(self):
        """Остановить отображение информации о записи."""
        self.update_timer.stop()
        self.info_label.hide()
        self.limit_label.hide()
        self.recording_start_time = None
        self.video_size_bytes = 0
        self.limit_exceeded = False
        self.limit_message = ""
    
    def update_video_size(self, size_bytes: int):
        """Обновить размер видео."""
        self.video_size_bytes = size_bytes
        if self.recording_start_time:
            self._update_info()
    
    def _update_info(self):
        """Обновить текст информации."""
        if not self.recording_start_time:
            return
        
        from datetime import datetime
        elapsed = datetime.now() - self.recording_start_time
        
        hours = elapsed.seconds // 3600
        minutes = (elapsed.seconds % 3600) // 60
        seconds = elapsed.seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        if self.video_size_bytes < 1024 * 1024:
            size_str = f"{self.video_size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{self.video_size_bytes / (1024 * 1024):.1f} MB"
        
        start_datetime_str = self.recording_start_time.strftime("%d.%m.%Y %H:%M:%S")
        
        info_text = f"📅 {start_datetime_str}\n⏱ {time_str}\n💾 {size_str}"
        self.info_label.setText(info_text)
        self._position_overlays()

    def show_status(self, text: str, color: str = "red"):
        """Показать статус (например, запись)."""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 8px 12px;
                font-family: sans-serif;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
            }}
        """)
        self.status_label.show()
        self._position_overlays()

    def hide_status(self):
        """Скрыть статус."""
        self.status_label.hide()
    
    def _position_overlays(self):
        """Позиционировать оверлеи."""
        # Info label - слева сверху
        if self.info_label.isVisible():
            self.info_label.adjustSize()
            self.info_label.move(10, 10)
            
        # Status label - справа сверху
        if self.status_label.isVisible():
            self.status_label.adjustSize()
            x = self.width() - self.status_label.width() - 10
            y = 10
            self.status_label.move(x, y)
        
        # Позиционировать limit_label по центру
        if self.limit_label.isVisible():
            self.limit_label.setMaximumWidth(self.width() - 40)
            self.limit_label.adjustSize()
            x = (self.width() - self.limit_label.width()) // 2
            y = (self.height() - self.limit_label.height()) // 2
            self.limit_label.move(x, y)
    
    def toggle_fullscreen(self):
        """Переключить полноэкранный режим родительского окна."""
        parent_window = self.window()
        if parent_window and parent_window != self:
            if parent_window.isFullScreen():
                parent_window.showNormal()
                self.is_fullscreen = False
            else:
                parent_window.showFullScreen()
                self.is_fullscreen = True
    
    def mouseDoubleClickEvent(self, event):
        """Двойной клик для fullscreen."""
        self.toggle_fullscreen()
    
    def show_limit_exceeded(self, message: str):
        """Показать сообщение о превышении лимита."""
        self.limit_exceeded = True
        self.limit_message = message
        self.limit_label.setText(message)
        self.limit_label.show()
        self._position_overlays()
    
    def is_limit_exceeded(self) -> bool:
        """Проверить превышен ли лимит."""
        return self.limit_exceeded
    
    def resizeEvent(self, event):
        """Обработка изменения размера."""
        super().resizeEvent(event)
        self._position_overlays()
        if self.current_image:
            self._update_display()
