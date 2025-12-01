"""Эндпоинты для загрузки файлов."""
import shutil
import logging
import mimetypes
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from common.models import APIError
from server.src.config import get_config
from server.src.db.repository import ReceptionRepository

router = APIRouter(prefix="/receptions", tags=["Files"])
logger = logging.getLogger(__name__)

# Константы безопасности
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_DOCUMENT_TYPES = {
    'application/pdf',
    'image/png', 
    'image/jpeg',
    'image/jpg'
}
ALLOWED_VIDEO_TYPES = {
    'video/x-msvideo',  # .avi
    'video/mp4',
    'video/mpeg',
    'video/quicktime'   # .mov
}


def _validate_file_size(file: UploadFile) -> None:
    """Проверить размер файла."""
    # Перейти в конец файла чтобы узнать размер
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)  # Вернуться в начало
    
    logger.info(f"File size check: {file.filename} = {size} bytes")
    
    if size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {size} bytes > {MAX_FILE_SIZE}")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.1f} MB"
        )
    
    if size == 0:
        logger.warning(f"Empty file: {file.filename}")
        raise HTTPException(status_code=400, detail="File is empty")


def _validate_file_type(file: UploadFile, allowed_types: set) -> None:
    """Проверить MIME тип файла."""
    # Получить MIME тип из имени файла
    mime_type, _ = mimetypes.guess_type(file.filename)
    
    # Фоллбэк на content_type от клиента (менее надежно)
    if not mime_type:
        mime_type = file.content_type
    
    logger.info(f"File type check: {file.filename} -> {mime_type}")
    
    if mime_type not in allowed_types:
        logger.warning(f"Invalid file type: {mime_type} not in {allowed_types}")
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {mime_type}. Allowed: {', '.join(allowed_types)}"
        )


def _save_file(reception_id: int, file: UploadFile, filename: str) -> str:
    """Сохранить файл и вернуть относительный путь."""
    logger.info(f"Saving file for reception {reception_id}: {filename}")
    
    config = get_config()
    receipts_root = Path(config["paths"]["receipts_root"])
    
    # Получить приёмку
    reception = ReceptionRepository.get_by_id(reception_id)
    if not reception:
        logger.error(f"Reception {reception_id} not found")
        raise HTTPException(status_code=404, detail="Reception not found")
    
    date_str = reception.ttn_date.strftime("%Y-%m-%d")
    folder_name = f"{date_str}_{reception_id}"
    
    # Абсолютный путь
    if not receipts_root.is_absolute():
        project_root = Path(__file__).parent.parent.parent.parent
        receipts_root = project_root / receipts_root
        
    save_dir = receipts_root / folder_name
    save_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = save_dir / filename
    
    logger.info(f"Writing file to: {file_path}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    logger.info(f"File saved successfully: {file_path}")
        
    # Возвращаем относительный путь для БД
    return f"{config['paths']['receipts_root']}/{folder_name}/{filename}"


@router.post("/{reception_id}/document", responses={404: {"model": APIError}, 413: {"model": APIError}, 415: {"model": APIError}})
def upload_document(reception_id: int, file: UploadFile = File(...)):
    """Загрузить документ ТТН."""
    logger.info(f"Document upload request for reception {reception_id}: {file.filename}")
    
    # Валидация
    _validate_file_size(file)
    _validate_file_type(file, ALLOWED_DOCUMENT_TYPES)
    
    # Определяем расширение
    ext = Path(file.filename).suffix
    if not ext:
        ext = ".pdf"
        
    # Сохраняем как document.ext
    rel_path = _save_file(reception_id, file, f"document{ext}")
    
    # Обновляем БД
    if not ReceptionRepository.update_document_path(reception_id, rel_path):
        logger.error(f"Failed to update document path for reception {reception_id}")
        raise HTTPException(status_code=404, detail="Reception not found")
        
    logger.info(f"Document uploaded successfully for reception {reception_id}")
    return {"id": reception_id, "document_path": rel_path}


@router.post("/{reception_id}/video", responses={404: {"model": APIError}, 413: {"model": APIError}, 415: {"model": APIError}})
def upload_video(reception_id: int, file: UploadFile = File(...)):
    """Загрузить видео контроля."""
    logger.info(f"Video upload request for reception {reception_id}: {file.filename}")
    
    # Валидация
    _validate_file_size(file)
    _validate_file_type(file, ALLOWED_VIDEO_TYPES)
    
    ext = Path(file.filename).suffix
    if not ext:
        ext = ".avi"
        
    rel_path = _save_file(reception_id, file, f"video{ext}")
    
    if not ReceptionRepository.update_video_path(reception_id, rel_path):
        logger.error(f"Failed to update video path for reception {reception_id}")
        raise HTTPException(status_code=404, detail="Reception not found")
        
    logger.info(f"Video uploaded successfully for reception {reception_id}")
    return {"id": reception_id, "video_path": rel_path}
