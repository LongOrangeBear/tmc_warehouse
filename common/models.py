from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ControlType(str, Enum):
    """Типы входного контроля для товара."""
    WEIGHT_CHECK = "weight_check"
    VISUAL_CHECK = "visual_check"
    DIMENSION_CHECK = "dimension_check"
    QUANTITY_CHECK = "quantity_check"


class ControlStatus(str, Enum):
    """Статус выполнения контроля по позиции."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ReceptionStatus(str, Enum):
    """Статус приёмки ТМЦ."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SYNCED = "synced"


class SyncStatus(str, Enum):
    """Статус операции синхронизации / отправки данных."""
    OK = "ok"
    ERROR = "error"


class APIError(BaseModel):
    """Единый формат ошибки API."""
    detail: str = Field(..., description="Описание ошибки для человека")
    code: Optional[str] = Field(
        default=None,
        description="Машинно-читаемый код ошибки (опционально).",
    )


class HealthResponse(BaseModel):
    """Ответ на /health."""
    status: str = Field(..., description='"ok", если сервер работает')
    time: datetime = Field(..., description="Текущее время на сервере")


class ValidationResult(BaseModel):
    """Результат проверки одной позиции."""
    passed: bool = Field(..., description="True, если контроль пройден")
    message: str = Field(..., description="Краткое текстовое описание результата")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительные детали: измеренные значения, допуски и т.д.",
    )


class ProductBase(BaseModel):
    """Базовые поля товара (справочник)."""
    article: str = Field(..., max_length=50, description="Артикул (уникальный)")
    name: str = Field(..., max_length=255, description="Наименование товара")
    unit: str = Field("шт", max_length=20, description="Единица измерения")
    requires_control: bool = Field(
        False, description="Нужно ли выполнять входной контроль для товара",
    )
    control_type: Optional[ControlType] = Field(
        default=None,
        description="Тип контроля, если он требуется",
    )
    control_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Параметры контроля для данного типа (например, допуски)",
    )


class ProductCreate(ProductBase):
    """Модель для создания нового товара через API."""
    pass


class ProductRead(ProductBase):
    """Модель для чтения товара из API/БД."""
    id: int = Field(..., description="ID товара в БД")
    created_at: datetime = Field(..., description="Дата и время создания записи")


class ReceptionItemBase(BaseModel):
    """Базовая модель позиции приёмки."""
    article: str = Field(..., max_length=50, description="Артикул (как в ТТН)")
    name: str = Field(..., max_length=255, description="Наименование позиции")
    quantity: float = Field(..., description="Количество по ТТН")
    unit: str = Field("шт", max_length=20, description="Единица измерения")

    control_required: bool = Field(
        False,
        description="Нужно ли проводить входной контроль по этой позиции",
    )
    control_status: Optional[ControlStatus] = Field(
        default=None,
        description="Текущий статус контроля по данной позиции",
    )
    control_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Структурированный результат контроля",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Примечания оператора по данной позиции",
    )

    suspicious_fields: List[str] = Field(
        default_factory=list,
        description=(
            "Список полей ('article', 'name', 'quantity', 'unit'), "
            "которые были распознаны OCR с низкой уверенностью."
        ),
    )


class ReceptionItemCreate(ReceptionItemBase):
    """Модель позиции при создании приёмки."""
    pass


class ReceptionItemRead(ReceptionItemBase):
    """Модель позиции при чтении / получения из API."""
    id: int = Field(..., description="ID позиции в БД")
    reception_id: int = Field(..., description="ID приёмки")
    product_id: Optional[int] = Field(
        default=None,
        description="Ссылка на товар из справочника, если найден по артикулу",
    )


class ReceptionItemControlUpdate(BaseModel):
    """
    Модель обновления результата контроля по позиции.
    Используется в эндпоинте /receptions/{id}/control-results.
    """
    id: int = Field(..., description="ID позиции (reception_items.id)")
    control_status: ControlStatus = Field(..., description="Результат контроля")
    control_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Структурированный результат проверки",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Комментарий оператора для этой позиции",
    )


class ReceptionBase(BaseModel):
    """Базовые поля приёмки ТМЦ."""
    ttn_number: str = Field(..., max_length=100, description="Номер ТТН / накладной")
    ttn_date: date = Field(..., description="Дата ТТН")
    supplier: str = Field(..., max_length=255, description="Поставщик / грузоотправитель")


class ReceptionCreate(ReceptionBase):
    """
    Модель для создания приёмки.
    Клиент отправляет отредактированные данные ТТН и позиции после OCR.
    """
    items: List[ReceptionItemCreate] = Field(
        ..., description="Список позиций, извлечённых из ТТН и проверенных оператором",
    )
    ocr_engine: Optional[str] = Field(
        default=None,
        description="Название/версия OCR-движка (для отладки, опционально)",
    )


class ReceptionShort(BaseModel):
    """Сжатое представление приёмки для списка/истории."""
    id: int
    ttn_number: str
    ttn_date: date
    supplier: str
    status: ReceptionStatus
    created_at: datetime


class ReceptionRead(ReceptionBase):
    """Полная модель приёмки для чтения."""
    id: int = Field(..., description="ID приёмки")
    status: ReceptionStatus = Field(..., description="Текущий статус приёмки")
    created_at: datetime = Field(..., description="Дата/время создания записи")
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Дата/время завершения контроля (если есть)",
    )
    synced_at: Optional[datetime] = Field(
        default=None,
        description="Дата/время полной синхронизации (опционально)",
    )
    document_path: Optional[str] = Field(
        default=None,
        description="Относительный путь к исходному документу ТТН на сервере",
    )
    video_path: Optional[str] = Field(
        default=None,
        description="Относительный путь к видеофайлу контроля на сервере",
    )
    items: List[ReceptionItemRead] = Field(
        default_factory=list,
        description="Список позиций, связанных с приёмкой",
    )


class SyncLogRead(BaseModel):
    """Модель для чтения записей логов синхронизации (опционально)."""
    id: int
    reception_id: int
    status: SyncStatus
    response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime


class SyncResult(BaseModel):
    """Результат операции sync со стороны клиента/сервера."""
    status: SyncStatus
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class OCRItem(BaseModel):
    """Результат OCR по одной строке/позиции."""
    raw_text: str
    article: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    field_confidence: Dict[str, float] = Field(
        default_factory=dict,
        description="Уверенность по полям: 'article', 'name', 'quantity', 'unit'",
    )


class OCRResult(BaseModel):
    """
    Общий результат OCR по документу ТТН.
    В API можно хранить как JSON-строку в поле receptions.ocr_result.
    """
    ttn_number: Optional[str] = None
    ttn_date: Optional[date] = None
    supplier: Optional[str] = None
    items: List[OCRItem] = Field(default_factory=list)
