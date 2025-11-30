# tests/conftest.py
"""
Pytest конфигурация и fixtures для тестов TMC Warehouse.
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Добавить корень проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ═══════════════════════════════════════════════════════════════════
# Fixtures для конфигурации
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Путь к корню проекта."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_config() -> dict:
    """Тестовая конфигурация."""
    return {
        "app": {
            "name": "TMC Warehouse Test",
            "version": "0.0.0-test"
        },
        "paths": {
            "database": ":memory:",  # SQLite в памяти
            "receipts_root": tempfile.mkdtemp(),
            "logs": tempfile.mkdtemp()
        },
        "tesseract": {
            "path": _find_tesseract(),
            "languages": ["rus", "eng"],
            "psm": 6
        },
        "poppler": {
            "path": _find_poppler()
        },
        "camera": {
            "default_index": 0,
            "resolution": [640, 480],
            "fps": 15,
            "codec": "MJPG",
            "container": "avi"
        },
        "server": {
            "host": "127.0.0.1",
            "port": 8765,  # Другой порт для тестов
            "base_url": "http://127.0.0.1:8765/api/v1",
            "timeout": 5
        },
        "sync": {
            "retry_count": 1,
            "retry_delay": 1
        },
        "validation": {
            "control_types": {
                "weight_check": {
                    "description": "Проверка веса",
                    "params": ["target_weight", "tolerance"]
                },
                "visual_check": {
                    "description": "Визуальный осмотр",
                    "params": ["checklist"]
                }
            }
        }
    }


def _find_tesseract() -> str:
    """Найти путь к Tesseract."""
    import platform
    
    if platform.system() == "Windows":
        default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if Path(default).exists():
            return default
    else:
        # Linux/Mac
        import shutil
        path = shutil.which("tesseract")
        if path:
            return path
    
    return "tesseract"  # Надеемся что в PATH


def _find_poppler() -> str:
    """Найти путь к Poppler."""
    import platform
    
    if platform.system() == "Windows":
        default = r"C:\poppler\bin"
        if Path(default).exists():
            return default
    
    return None  # На Linux не нужен путь


# ═══════════════════════════════════════════════════════════════════
# Fixtures для базы данных (Server)
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def temp_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Временная база данных для теста."""
    db_path = tmp_path / "test_warehouse.db"
    yield db_path
    # Очистка после теста
    if db_path.exists():
        db_path.unlink()


# ═══════════════════════════════════════════════════════════════════
# Fixtures для FastAPI (Server)
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def test_client():
    """
    HTTP клиент для тестирования FastAPI.
    
    Использование:
        def test_health(test_client):
            response = test_client.get("/api/v1/health")
            assert response.status_code == 200
    """
    try:
        from fastapi.testclient import TestClient
        from server.src.main_server import app
        
        with TestClient(app) as client:
            yield client
    except ImportError:
        pytest.skip("FastAPI or server not available")


# ═══════════════════════════════════════════════════════════════════
# Fixtures для тестовых данных
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_product_data() -> dict:
    """Пример данных товара."""
    return {
        "article": "TEST-001",
        "name": "Тестовый товар",
        "unit": "шт",
        "requires_control": True,
        "control_type": "weight_check",
        "control_params": {
            "target_weight": 10.0,
            "tolerance": 0.5
        }
    }


@pytest.fixture
def sample_reception_data() -> dict:
    """Пример данных приёмки."""
    return {
        "ttn_number": "TEST-TTN-001",
        "ttn_date": "2025-01-15",
        "supplier": "ООО Тестовый поставщик",
        "items": [
            {
                "article": "TEST-001",
                "name": "Тестовый товар",
                "quantity": 100,
                "unit": "шт",
                "control_required": False,
                "suspicious_fields": []
            }
        ]
    }


@pytest.fixture
def sample_ttn_text() -> str:
    """Пример текста ТТН для OCR тестов."""
    return """
    ТОВАРНАЯ НАКЛАДНАЯ № ТТН-2025-001 от 15.01.2025
    
    Поставщик: ООО "МеталлТорг"
    
    № | Артикул    | Наименование         | Ед. | Кол-во
    1 | BOLT-M10   | Болт М10х50          | шт  | 100
    2 | NUT-M10    | Гайка М10            | шт  | 100
    3 | WASHER-M10 | Шайба М10            | шт  | 200
    
    Итого: 3 позиции
    """


# ═══════════════════════════════════════════════════════════════════
# Skip markers
# ═══════════════════════════════════════════════════════════════════

def pytest_configure(config):
    """Регистрация кастомных маркеров."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "camera: marks tests that require camera"
    )
    config.addinivalue_line(
        "markers", "gui: marks tests that require GUI"
    )
    config.addinivalue_line(
        "markers", "integration: marks integration tests"
    )


# ═══════════════════════════════════════════════════════════════════
# Auto-skip для отсутствующих зависимостей
# ═══════════════════════════════════════════════════════════════════

def pytest_collection_modifyitems(config, items):
    """Автоматически пропускать тесты при отсутствии зависимостей."""
    import platform
    
    skip_camera = pytest.mark.skip(reason="Camera tests disabled in CI")
    skip_gui_linux = pytest.mark.skip(reason="GUI tests require display")
    
    for item in items:
        # Пропустить тесты камеры в CI
        if "camera" in item.keywords:
            if os.environ.get("CI"):
                item.add_marker(skip_camera)
        
        # Пропустить GUI тесты на Linux без дисплея
        if "gui" in item.keywords:
            if platform.system() == "Linux" and not os.environ.get("DISPLAY"):
                item.add_marker(skip_gui_linux)
