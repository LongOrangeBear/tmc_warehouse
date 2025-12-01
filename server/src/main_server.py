"""Точка входа сервера FastAPI."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from server.src.config import get_config
from server.src.db.migrations import init_db, seed_products
from server.src.api import routes_health, routes_products, routes_receptions, routes_files

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup и shutdown события."""
    logger.info("Starting server...")
    init_db()
    seed_products()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down server...")


# Создание приложения
config = get_config()
app = FastAPI(
    title=config["app"]["name"],
    version=config["app"]["version"],
    lifespan=lifespan
)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request, call_next):
    """Логировать все HTTP запросы."""
    client_host = request.client.host if request.client else "test"
    logger.debug(f"Request: {request.method} {request.url.path} from {client_host}")
    try:
        response = await call_next(request)
        logger.debug(f"Response: {request.method} {request.url.path} -> {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} - {e}")
        raise

# CORS (для локальной разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(routes_health.router, prefix="/api/v1")
app.include_router(routes_products.router, prefix="/api/v1")
app.include_router(routes_receptions.router, prefix="/api/v1")
app.include_router(routes_files.router, prefix="/api/v1")

# Статика для доступа к файлам
receipts_root_str = config["paths"]["receipts_root"]
project_root = Path(__file__).parent.parent.parent
if not Path(receipts_root_str).is_absolute():
    receipts_root = project_root / receipts_root_str
else:
    receipts_root = Path(receipts_root_str)

receipts_root.mkdir(parents=True, exist_ok=True)
app.mount("/data", StaticFiles(directory=str(receipts_root)), name="data")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
        log_level="info"
    )
