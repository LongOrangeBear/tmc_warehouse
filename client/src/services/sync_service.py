"""HTTP клиент для взаимодействия с сервером."""
import logging
from pathlib import Path
from typing import List, Optional

import requests

from client.src.config import get_config
from common.models import (
    HealthResponse, ProductRead,
    ReceptionCreate, ReceptionRead, ReceptionShort,
    ReceptionItemControlUpdate, ReceptionStatus
)

logger = logging.getLogger(__name__)


class SyncService:
    """Сервис синхронизации с сервером."""

    def __init__(self):
        config = get_config()
        self.base_url = config["server"]["base_url"]
        self.timeout = config["server"]["timeout"]

    def check_health(self) -> bool:
        """Проверить доступность сервера."""
        logger.debug(f"Health check: {self.base_url}/health")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            result = response.status_code == 200
            logger.info(f"Server health: {'ONLINE' if result else 'OFFLINE'}")
            return result
        except requests.RequestException as e:
            logger.warning(f"Server health check failed: {e}")
            return False

    def get_products(self, limit: int = 100) -> List[ProductRead]:
        """Получить список товаров."""
        try:
            response = requests.get(
                f"{self.base_url}/products",
                params={"limit": limit},
                timeout=self.timeout
            )
            response.raise_for_status()
            return [ProductRead(**p) for p in response.json()]
        except requests.RequestException as e:
            logger.error(f"Failed to get products: {e}")
            return []

    def get_all_products(self) -> List[ProductRead]:
        """Получить все товары (алиас для get_products)."""
        return self.get_products(limit=1000)

    def get_product_by_article(self, article: str) -> Optional[ProductRead]:
        """Получить товар по артикулу."""
        try:
            response = requests.get(
                f"{self.base_url}/products/{article}",
                timeout=self.timeout
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return ProductRead(**response.json())
        except requests.RequestException as e:
            logger.error(f"Failed to get product {article}: {e}")
            return None

    def create_reception(self, data: ReceptionCreate) -> Optional[ReceptionRead]:
        """Создать приёмку."""
        logger.info(f"Creating reception: TTN={data.ttn_number}, items={len(data.items)}")
        try:
            response = requests.post(
                f"{self.base_url}/receptions",
                json=data.model_dump(mode="json"),
                timeout=self.timeout
            )
            response.raise_for_status()
            result = ReceptionRead(**response.json())
            logger.info(f"Reception created: ID={result.id}, status={result.status}")
            return result
        except requests.RequestException as e:
            logger.error(f"Failed to create reception: {e}")
            return None

    def get_receptions(
        self,
        status: Optional[ReceptionStatus] = None,
        limit: int = 100
    ) -> List[ReceptionShort]:
        """Получить список приёмок."""
        try:
            params = {"limit": limit}
            if status:
                params["status"] = status.value
            response = requests.get(
                f"{self.base_url}/receptions",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return [ReceptionShort(**r) for r in response.json()]
        except requests.RequestException as e:
            logger.error(f"Failed to get receptions: {e}")
            return []

    def get_reception(self, reception_id: int) -> Optional[ReceptionRead]:
        """Получить приёмку по ID."""
        try:
            response = requests.get(
                f"{self.base_url}/receptions/{reception_id}",
                timeout=self.timeout
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return ReceptionRead(**response.json())
        except requests.RequestException as e:
            logger.error(f"Failed to get reception {reception_id}: {e}")
            return None

    def upload_document(self, reception_id: int, file_path: Path) -> bool:
        """Загрузить документ."""
        logger.info(f"Uploading document for reception {reception_id}: {file_path.name} ({file_path.stat().st_size} bytes)")
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    f"{self.base_url}/receptions/{reception_id}/document",
                    files={"file": (file_path.name, f)},
                    timeout=self.timeout * 2  # Больше времени для загрузки
                )
            response.raise_for_status()
            logger.info(f"Document uploaded successfully for reception {reception_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to upload document: {e}")
            return False

    def upload_video(self, reception_id: int, file_path: Path) -> bool:
        """Загрузить видео."""
        logger.info(f"Uploading video for reception {reception_id}: {file_path.name} ({file_path.stat().st_size} bytes)")
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    f"{self.base_url}/receptions/{reception_id}/video",
                    files={"file": (file_path.name, f)},
                    timeout=self.timeout * 5  # Ещё больше для видео
                )
            response.raise_for_status()
            logger.info(f"Video uploaded successfully for reception {reception_id}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to upload video: {e}")
            return False

    def upload_photo(self, reception_id: int, item_id: int, file_path: Path) -> bool:
        """Загрузить фото товара."""
        logger.info(f"Uploading photo for item {item_id}: {file_path.name}")
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    f"{self.base_url}/receptions/{reception_id}/items/{item_id}/photo",
                    files={"file": (file_path.name, f)},
                    timeout=self.timeout
                )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to upload photo: {e}")
            return False

    def send_control_results(
        self,
        reception_id: int,
        items: List[ReceptionItemControlUpdate]
    ) -> Optional[ReceptionRead]:
        """Отправить результаты контроля."""
        logger.info(f"Sending control results for reception {reception_id}: {len(items)} items")
        try:
            response = requests.post(
                f"{self.base_url}/receptions/{reception_id}/control-results",
                json={"items": [item.model_dump(mode="json") for item in items]},
                timeout=self.timeout
            )
            response.raise_for_status()
            result = ReceptionRead(**response.json())
            logger.info(f"Control results sent successfully, new status: {result.status}")
            return result
        except requests.RequestException as e:
            logger.error(f"Failed to send control results: {e}")
            return None

    def download_video(self, reception_id: int, save_path: Path) -> bool:
        """Скачать видео приёмки."""
        logger.info(f"Downloading video for reception {reception_id}")
        try:
            response = requests.get(
                f"{self.base_url}/receptions/{reception_id}/video",
                timeout=self.timeout * 10,  # Большой timeout для видео
                stream=True
            )
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Video downloaded successfully: {save_path}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to download video: {e}")
            return False

    def download_document(self, reception_id: int, save_path: Path) -> bool:
        """Скачать документ ТТН."""
        logger.info(f"Downloading document for reception {reception_id}")
        try:
            response = requests.get(
                f"{self.base_url}/receptions/{reception_id}/document",
                timeout=self.timeout * 5,
                stream=True
            )
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Document downloaded successfully: {save_path}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to download document: {e}")
            return False

    def download_item_photos_zip(self, reception_id: int, item_id: int, save_path: Path) -> bool:
        """Скачать все фотографии товара в ZIP архиве."""
        logger.info(f"Downloading photos for item {item_id}")
        try:
            response = requests.get(
                f"{self.base_url}/receptions/{reception_id}/items/{item_id}/photos",
                timeout=self.timeout * 5,
                stream=True
            )
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Photos ZIP downloaded successfully: {save_path}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to download photos: {e}")
            return False

    def download_single_photo(self, reception_id: int, item_id: int, photo_index: int, save_path: Path) -> bool:
        """Скачать конкретную фотографию товара."""
        logger.info(f"Downloading photo {photo_index} for item {item_id}")
        try:
            response = requests.get(
                f"{self.base_url}/receptions/{reception_id}/items/{item_id}/photos/{photo_index}",
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Photo downloaded successfully: {save_path}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to download photo: {e}")
            return False
