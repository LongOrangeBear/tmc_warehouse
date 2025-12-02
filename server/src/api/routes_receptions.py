"""Эндпоинты для работы с приёмками."""
from typing import List
from fastapi import APIRouter, HTTPException, Query, Body

from common.models import (
    ReceptionCreate, ReceptionRead, ReceptionShort, 
    ReceptionStatus, APIError, ReceptionItemControlUpdate
)
from server.src.db.repository import ReceptionRepository

router = APIRouter(prefix="/receptions", tags=["Receptions"])


@router.post("", response_model=ReceptionRead, status_code=201)
def create_reception(data: ReceptionCreate) -> ReceptionRead:
    """Создать новую приёмку."""
    return ReceptionRepository.create(data)


@router.get("", response_model=List[ReceptionShort])
def get_receptions(
    status: ReceptionStatus = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> List[ReceptionShort]:
    """Получить список приёмок."""
    return ReceptionRepository.get_all(status=status, limit=limit, offset=offset)


@router.get("/{reception_id}", response_model=ReceptionRead, responses={404: {"model": APIError}})
def get_reception(reception_id: int) -> ReceptionRead:
    """Получить детали приёмки."""
    reception = ReceptionRepository.get_by_id(reception_id)
    if not reception:
        raise HTTPException(status_code=404, detail="Reception not found")
    return reception


@router.post("/{reception_id}/control-results", response_model=ReceptionRead, responses={404: {"model": APIError}})
def update_control_results(
    reception_id: int,
    items: List[ReceptionItemControlUpdate] = Body(..., embed=True)
) -> ReceptionRead:
    """Обновить результаты контроля и завершить приёмку если всё готово."""
    reception = ReceptionRepository.update_control_results(reception_id, items)
    if not reception:
        raise HTTPException(status_code=404, detail="Reception not found")
    return reception


