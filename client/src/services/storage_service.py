"""Сервис локального хранения файлов."""
import shutil
from pathlib import Path
from datetime import date

from client.src.config import get_config


class StorageService:
    """Сервис для работы с локальными файлами."""

    def __init__(self):
        config = get_config()
        self.receipts_root = Path(config["paths"]["receipts_root"])
        
        # Ensure absolute path rooted at current working directory if relative
        if not self.receipts_root.is_absolute():
            self.receipts_root = Path.cwd() / self.receipts_root
        
        self.receipts_root.mkdir(parents=True, exist_ok=True)

    def get_reception_folder(self, reception_id: int, ttn_date: date) -> Path:
        """Получить папку приёмки."""
        folder_name = f"{ttn_date.isoformat()}_{reception_id}"
        folder_path = self.receipts_root / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def save_document(self, source_path: Path, reception_id: int, ttn_date: date) -> Path:
        """Сохранить документ в папку приёмки."""
        folder = self.get_reception_folder(reception_id, ttn_date)
        ext = source_path.suffix or ".pdf"
        target_path = folder / f"document{ext}"
        
        shutil.copy2(source_path, target_path)
        return target_path

    def move_video(self, source_path: Path, reception_id: int, ttn_date: date) -> Path:
        """Переместить видео в папку приёмки."""
        folder = self.get_reception_folder(reception_id, ttn_date)
        ext = source_path.suffix or ".avi"
        target_path = folder / f"video{ext}"
        
        shutil.move(str(source_path), str(target_path))
        return target_path

    def save_photo(self, image_data: bytes, reception_id: int, ttn_date: date, item_id: int) -> Path:
        """Сохранить фото товара."""
        folder = self.get_reception_folder(reception_id, ttn_date)
        # Create subfolder for photos if needed, or just prefix
        filename = f"item_{item_id}_photo_{int(date.today().strftime('%s'))}.jpg" # Using timestamp to avoid collisions
        target_path = folder / filename
        
        with open(target_path, "wb") as f:
            f.write(image_data)
        
        return target_path
