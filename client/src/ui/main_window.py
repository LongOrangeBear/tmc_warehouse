"""Главное окно клиента."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStatusBar, QMessageBox
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon

from client.src.services import SyncService, CameraService
from client.src.ui.styles import STYLES
from client.src.ui.document_dialog import DocumentDialog
from client.src.ui.history_dialog import HistoryDialog
from client.src.ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Главное окно приложения TMC Warehouse."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TMC Warehouse - Приёмка ТМЦ")
        self.resize(600, 400)
        
        # Сервисы
        self.sync_service = SyncService()
        self.camera_service = CameraService()
        
        # Статусы
        self.server_online = False
        self.camera_available = False
        
        self._setup_ui()
        self._setup_status_bar()
        self._start_health_check()
        self._check_camera()

    def _setup_ui(self):
        """Настроить интерфейс."""
        # Применить стили
        self.setStyleSheet(STYLES)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # Заголовок
        title = QLabel("Система приёмки ТМЦ")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Кнопки
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(15)
        
        # Кнопка "Принять ТМЦ"
        self.receive_btn = QPushButton("📦 Принять ТМЦ")
        self.receive_btn.setMinimumHeight(60)
        self.receive_btn.setStyleSheet("font-size: 16px;")
        self.receive_btn.clicked.connect(self._open_reception_dialog)
        btn_layout.addWidget(self.receive_btn)
        
        # Кнопка "История"
        history_btn = QPushButton("📋 История приёмок")
        history_btn.setMinimumHeight(60)
        history_btn.setStyleSheet("font-size: 16px;")
        history_btn.clicked.connect(self._open_history_dialog)
        btn_layout.addWidget(history_btn)
        
        # Кнопка "Настройки"
        settings_btn = QPushButton("⚙️ Настройки")
        settings_btn.setMinimumHeight(60)
        settings_btn.setStyleSheet("font-size: 16px;")
        settings_btn.clicked.connect(self._open_settings_dialog)
        btn_layout.addWidget(settings_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()

    def _setup_status_bar(self):
        """Настроить статус-бар."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Индикаторы
        self.server_label = QLabel("🔴 Сервер: офлайн")
        self.camera_label = QLabel("🔴 Камера: не найдена")
        
        self.status_bar.addPermanentWidget(self.server_label)
        self.status_bar.addPermanentWidget(self.camera_label)

    def _start_health_check(self):
        """Запустить периодическую проверку сервера."""
        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self._check_server_health)
        self.health_timer.start(5000)  # Каждые 5 секунд
        
        # Первая проверка сразу
        self._check_server_health()

    def _check_server_health(self):
        """Проверить доступность сервера."""
        online = self.sync_service.check_health()
        self.server_online = online
        
        if online:
            self.server_label.setText("🟢 Сервер: онлайн")
            self.server_label.setStyleSheet("color: green;")
            self.receive_btn.setEnabled(True)
        else:
            self.server_label.setText("🔴 Сервер: офлайн")
            self.server_label.setStyleSheet("color: red;")
            self.receive_btn.setEnabled(False)

    def _check_camera(self):
        """Проверить доступность камеры."""
        cameras = CameraService.list_available_cameras()
        self.camera_available = len(cameras) > 0
        
        if self.camera_available:
            self.camera_label.setText(f"🟢 Камера: доступна ({len(cameras)})")
            self.camera_label.setStyleSheet("color: green;")
        else:
            self.camera_label.setText("🟡 Камера: не найдена")
            self.camera_label.setStyleSheet("color: orange;")

    def _open_reception_dialog(self):
        """Открыть диалог приёмки."""
        dialog = DocumentDialog(self)
        if dialog.exec():
            # После успешного создания приёмки можно что-то сделать
            QMessageBox.information(self, "Готово", "Приёмка успешно создана")

    def _open_history_dialog(self):
        """Открыть диалог истории."""
        dialog = HistoryDialog(self)
        dialog.exec()

    def _open_settings_dialog(self):
        """Открыть диалог настроек."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Если настройки изменились, возможно нужно что-то обновить
            # Например, перепроверить камеру
            self._check_camera()

    def closeEvent(self, event):
        """Обработка закрытия окна."""
        self.health_timer.stop()
        super().closeEvent(event)
