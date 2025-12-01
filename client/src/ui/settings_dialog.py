"""Диалог настроек."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QCheckBox, QPushButton, QGroupBox,
    QMessageBox
)
from client.src.config import get_config, save_config
from client.src.services.camera_service import CameraService

class SettingsDialog(QDialog):
    """Диалог настроек приложения."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.resize(400, 300)
        
        self.config = get_config()
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Камера
        cam_group = QGroupBox("Камера")
        cam_layout = QVBoxLayout(cam_group)
        
        cam_layout.addWidget(QLabel("Выберите камеру:"))
        self.camera_combo = QComboBox()
        cam_layout.addWidget(self.camera_combo)
        
        self.mock_check = QCheckBox("Использовать Mock-камеру (если нет реальной)")
        cam_layout.addWidget(self.mock_check)
        
        layout.addWidget(cam_group)
        
        # Интерфейс
        ui_group = QGroupBox("Интерфейс")
        ui_layout = QVBoxLayout(ui_group)
        
        ui_layout.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        ui_layout.addWidget(self.theme_combo)
        
        layout.addWidget(ui_group)
        
        layout.addStretch()
        
        # Кнопки
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._save_settings)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def _load_settings(self):
        # Загрузка камер
        available_cameras = CameraService.list_available_cameras()
        self.camera_combo.addItem("По умолчанию (0)", 0)
        for idx in available_cameras:
            self.camera_combo.addItem(f"Камера {idx}", idx)
            
        current_idx = self.config.get("camera", {}).get("default_index", 0)
        # Find index in combo
        combo_idx = self.camera_combo.findData(current_idx)
        if combo_idx >= 0:
            self.camera_combo.setCurrentIndex(combo_idx)
            
        # Mock mode (not explicitly in config yet, but we can add it)
        # For now just UI placeholder or maybe we add it to config
        
        # Theme
        theme = self.config.get("ui", {}).get("theme", "light")
        self.theme_combo.setCurrentIndex(0 if theme == "light" else 1)
        
    def _save_settings(self):
        # Update config
        self.config["camera"]["default_index"] = self.camera_combo.currentData()
        
        if "ui" not in self.config:
            self.config["ui"] = {}
        self.config["ui"]["theme"] = "light" if self.theme_combo.currentIndex() == 0 else "dark"
        
        try:
            save_config(self.config)
            QMessageBox.information(self, "Успех", "Настройки сохранены. Перезапустите приложение.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки: {e}")
