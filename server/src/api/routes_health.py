"""Health check endpoint."""
from datetime import datetime, timezone
from fastapi import APIRouter
from common.models import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Проверка работоспособности сервера."""
    return HealthResponse(status="ok", time=datetime.now(timezone.utc))
