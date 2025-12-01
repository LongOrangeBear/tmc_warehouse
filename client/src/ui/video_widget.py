"""Виджет для отображения видео с камеры."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap


class VideoWidget(QWidget):
    """Виджет для отображения видеопотока."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.setMinimumSize(640, 480)
        
        self.current_image = None
        self.layout.addWidget(self.image_label)

    @Slot(QImage)
    def update_frame(self, image: QImage):
        """Обновить кадр."""
        self.current_image = image.copy()
        # Масштабируем изображение под размер виджета, сохраняя пропорции
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def clear(self):
        """Очистить изображение."""
        self.image_label.clear()
        self.image_label.setText("Нет сигнала")
        self.current_image = None

    def get_current_frame(self) -> QImage:
        """Получить текущий кадр."""
        return self.current_image
