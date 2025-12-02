"""Эндпоинты для скачивания файлов (документы, видео, фото)."""
import logging
import json
import zipfile
import io
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from common.models import APIError
from server.src.config import get_config
from server.src.db.repository import ReceptionRepository
from server.src.db.models import ReceptionItem

router = APIRouter(prefix="/receptions", tags=["Downloads"])
logger = logging.getLogger(__name__)


def _get_absolute_path(relative_path: str) -> Path:
    """Преобразовать относительный путь в абсолютный."""
    path = Path(relative_path)
    
    if not path.is_absolute():
        # Получить корень проекта
        project_root = Path(__file__).parent.parent.parent.parent
        path = project_root / relative_path
    
    return path


@router.get("/{reception_id}/document", responses={404: {"model": APIError}})
def download_document(reception_id: int):
    """Скачать документ ТТН."""
    logger.info(f"Document download request for reception {reception_id}")
    
    # Получить приёмку
    reception = ReceptionRepository.get_by_id(reception_id)
    if not reception:
        logger.error(f"Reception {reception_id} not found")
        raise HTTPException(status_code=404, detail="Reception not found")
    
    # Проверить наличие документа
    if not reception.document_path:
        logger.warning(f"No document for reception {reception_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Получить абсолютный путь
    doc_path = _get_absolute_path(reception.document_path)
    
    if not doc_path.exists():
        logger.error(f"Document file not found on disk: {doc_path}")
        raise HTTPException(status_code=404, detail="Document file not found on disk")
    
    # Определить MIME type
    ext = doc_path.suffix.lower()
    media_type_map = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg'
    }
    media_type = media_type_map.get(ext, 'application/octet-stream')
    
    logger.info(f"Sending document: {doc_path} ({doc_path.stat().st_size} bytes)")
    
    return FileResponse(
        path=str(doc_path),
        media_type=media_type,
        filename=f"reception_{reception_id}_document{ext}"
    )


@router.get("/{reception_id}/video", responses={404: {"model": APIError}})
def download_video(reception_id: int):
    """Скачать видео приёмки."""
    logger.info(f"Video download request for reception {reception_id}")
    
    reception = ReceptionRepository.get_by_id(reception_id)
    if not reception:
        logger.error(f"Reception {reception_id} not found")
        raise HTTPException(status_code=404, detail="Reception not found")
    
    if not reception.video_path:
        logger.warning(f"No video for reception {reception_id}")
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_path = _get_absolute_path(reception.video_path)
    
    if not video_path.exists():
        logger.error(f"Video file not found on disk: {video_path}")
        raise HTTPException(status_code=404, detail="Video file not found on disk")
    
    ext = video_path.suffix.lower()
    media_type_map = {
        '.avi': 'video/x-msvideo',
        '.mp4': 'video/mp4',
        '.mov': 'video/quicktime'
    }
    media_type = media_type_map.get(ext, 'video/x-msvideo')
    
    logger.info(f"Sending video: {video_path} ({video_path.stat().st_size} bytes)")
    
    return FileResponse(
        path=str(video_path),
        media_type=media_type,
        filename=f"reception_{reception_id}_video{ext}"
    )


@router.get("/{reception_id}/items/{item_id}/photos", responses={404: {"model": APIError}})
def download_item_photos(reception_id: int, item_id: int):
    """Скачать все фотографии товара в виде ZIP архива."""
    logger.info(f"Photos download request for reception {reception_id}, item {item_id}")
    
    # Получить товар из БД
    item = ReceptionItem.get_or_none(ReceptionItem.id == item_id)
    
    if not item or item.reception.id != reception_id:
        logger.error(f"Item {item_id} not found in reception {reception_id}")
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not item.photos:
        logger.warning(f"No photos for item {item_id}")
        raise HTTPException(status_code=404, detail="No photos for this item")
    
    # Парсить JSON список путей
    try:
        if isinstance(item.photos, str):
            photo_paths = json.loads(item.photos)
        else:
            photo_paths = item.photos
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse photos JSON: {e}")
        raise HTTPException(status_code=500, detail="Invalid photos data")
    
    if not photo_paths:
        logger.warning(f"Empty photos list for item {item_id}")
        raise HTTPException(status_code=404, detail="No photos for this item")
    
    # Создать ZIP архив в памяти
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, photo_rel_path in enumerate(photo_paths, 1):
            photo_path = _get_absolute_path(photo_rel_path)
            
            if photo_path.exists():
                # Добавить файл в архив с красивым именем
                arcname = f"photo_{i}{photo_path.suffix}"
                logger.info(f"Adding to ZIP: {photo_path} as {arcname}")
                zip_file.write(photo_path, arcname=arcname)
            else:
                logger.warning(f"Photo file not found: {photo_path}")
    
    # Проверить что хоть что-то добавили
    zip_buffer.seek(0)
    if zip_buffer.tell() == 0:
        logger.error(f"No valid photos found for item {item_id}")
        raise HTTPException(status_code=404, detail="No valid photo files found")
    
    zip_buffer.seek(0)
    
    logger.info(f"Sending ZIP archive for item {item_id} ({len(photo_paths)} photos)")
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=item_{item_id}_photos.zip"
        }
    )


@router.get("/{reception_id}/items/{item_id}/photos/{photo_index}", responses={404: {"model": APIError}})
def download_single_photo(reception_id: int, item_id: int, photo_index: int):
    """Скачать конкретную фотографию товара по индексу (начиная с 0)."""
    logger.info(f"Single photo download: reception={reception_id}, item={item_id}, index={photo_index}")
    
    item = ReceptionItem.get_or_none(ReceptionItem.id == item_id)
    
    if not item or item.reception.id != reception_id:
        logger.error(f"Item {item_id} not found in reception {reception_id}")
        raise HTTPException(status_code=404, detail="Item not found")
    
    if not item.photos:
        logger.warning(f"No photos for item {item_id}")
        raise HTTPException(status_code=404, detail="No photos for this item")
    
    try:
        if isinstance(item.photos, str):
            photo_paths = json.loads(item.photos)
        else:
            photo_paths = item.photos
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse photos JSON: {e}")
        raise HTTPException(status_code=500, detail="Invalid photos data")
    
    if photo_index < 0 or photo_index >= len(photo_paths):
        logger.warning(f"Invalid photo index {photo_index} for item {item_id} (total: {len(photo_paths)})")
        raise HTTPException(status_code=404, detail="Photo index out of range")
    
    photo_rel_path = photo_paths[photo_index]
    photo_path = _get_absolute_path(photo_rel_path)
    
    if not photo_path.exists():
        logger.error(f"Photo file not found: {photo_path}")
        raise HTTPException(status_code=404, detail="Photo file not found on disk")
    
    ext = photo_path.suffix.lower()
    media_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    media_type = media_type_map.get(ext, 'image/jpeg')
    
    logger.info(f"Sending photo: {photo_path} ({photo_path.stat().st_size} bytes)")
    
    return FileResponse(
        path=str(photo_path),
        media_type=media_type,
        filename=f"item_{item_id}_photo_{photo_index + 1}{ext}"
    )
