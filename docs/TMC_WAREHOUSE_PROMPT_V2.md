# 🤖 ПРОМПТ ДЛЯ ИИ-РАЗРАБОТЧИКА
## Система приёма ТМЦ на склад (v2.0)

**Версия:** 2.0 (клиент-серверная архитектура)
**Стек:** Python 3.12, PySide6, FastAPI, Peewee, SQLite, OpenCV, Tesseract

---

## 📋 МЕТА-ИНСТРУКЦИЯ

Ты — экспертный Python-разработчик. Твоя задача — реализовать код системы приёма ТМЦ на склад по готовой архитектуре и спецификациям.

### Твои роли:
1. **Backend Developer** — FastAPI, Peewee ORM, REST API
2. **Desktop Developer** — PySide6 GUI, многопоточность
3. **Computer Vision Engineer** — OCR (Tesseract), работа с камерой (OpenCV)
4. **Integration Engineer** — связь клиент-сервер, синхронизация

### Принципы работы:
- Следуй плану этап за этапом
- Используй **существующие** модели из `common/models.py`
- Следуй спецификации API из `docs/API.md`
- Отмечай выполненные задачи ✅
- Не переходи к следующему этапу пока текущий не завершён
- Пиши чистый, типизированный код по PEP 8

### ВАЖНО — Что уже готово:
- ✅ `common/models.py` — все Pydantic-модели (НЕ ИЗМЕНЯТЬ, только использовать)
- ✅ `config/config.json` — конфигурация
- ✅ `docs/*` — вся документация
- ⚠️ `server/src/main_server.py` — только health endpoint (нужно расширить)
- ⚠️ `client/src/main_client.py` — только скелет GUI (нужно расширить)

---

## 🏗️ АРХИТЕКТУРА СИСТЕМЫ

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              КЛИЕНТ (PySide6)                           │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ MainWindow  │  │DocumentDlg  │  │ ControlDlg  │  │ HistoryDlg  │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │            │
│  ┌──────┴────────────────┴────────────────┴────────────────┴──────┐    │
│  │                         СЕРВИСЫ                                 │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │    │
│  │  │   OCR    │ │  Camera  │ │ Validator│ │   Sync   │           │    │
│  │  │ Service  │ │ Service  │ │ Service  │ │ Service  │           │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └────┬─────┘           │    │
│  └──────────────────────────────────────────────┼─────────────────┘    │
└─────────────────────────────────────────────────┼───────────────────────┘
                                                  │ HTTP/REST
┌─────────────────────────────────────────────────┼───────────────────────┐
│                              СЕРВЕР (FastAPI)   │                       │
├─────────────────────────────────────────────────┼───────────────────────┤
│  ┌──────────────────────────────────────────────┴──────────────────┐   │
│  │                         API РОУТЕРЫ                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │   │
│  │  │  Health  │ │ Products │ │Receptions│ │  Files   │            │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │   │
│  └─────────────────────────────┬───────────────────────────────────┘   │
│                                │                                        │
│  ┌─────────────────────────────┴───────────────────────────────────┐   │
│  │                         REPOSITORY                               │   │
│  │              (CRUD операции с Peewee ORM)                        │   │
│  └─────────────────────────────┬───────────────────────────────────┘   │
│                                │                                        │
│  ┌─────────────────────────────┴───────────────────────────────────┐   │
│  │                    SQLite + File Storage                         │   │
│  │         data/database/warehouse.db    data/receipts/             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 СТРУКТУРА ПРОЕКТА

```
tmc_warehouse/
│
├── common/                          # ✅ ГОТОВО - НЕ ИЗМЕНЯТЬ
│   ├── __init__.py
│   └── models.py                    # Pydantic модели (эталон)
│
├── config/                          # ✅ ГОТОВО
│   └── config.json                  # Конфигурация
│
├── docs/                            # ✅ ГОТОВО - справочник
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── INSTALL.md
│   └── USER_GUIDE.md
│
├── server/                          # ⚠️ НУЖНО РЕАЛИЗОВАТЬ
│   └── src/
│       ├── __init__.py
│       ├── main_server.py           # Точка входа (расширить)
│       ├── config.py                # Загрузка конфига
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py            # Peewee модели
│       │   ├── migrations.py        # Создание таблиц
│       │   └── repository.py        # CRUD операции
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes_health.py     # GET /health
│       │   ├── routes_products.py   # /products
│       │   ├── routes_receptions.py # /receptions
│       │   └── routes_files.py      # Загрузка файлов
│       └── schemas/
│           └── __init__.py          # Re-export из common
│
├── client/                          # ⚠️ НУЖНО РЕАЛИЗОВАТЬ
│   └── src/
│       ├── __init__.py
│       ├── main_client.py           # Точка входа (расширить)
│       ├── config.py                # Загрузка конфига
│       ├── services/
│       │   ├── __init__.py
│       │   ├── ocr_service.py       # OCR распознавание
│       │   ├── camera_service.py    # Работа с камерой
│       │   ├── storage_service.py   # Локальное хранение
│       │   ├── validator_service.py # Валидация контроля
│       │   └── sync_service.py      # HTTP клиент к серверу
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_window.py       # Главное окно
│       │   ├── document_dialog.py   # Загрузка и OCR документа
│       │   ├── results_widget.py    # Таблица позиций
│       │   ├── control_dialog.py    # Входной контроль
│       │   ├── video_widget.py      # Превью камеры
│       │   ├── history_dialog.py    # История приёмок
│       │   └── styles.py            # QSS стили
│       └── utils/
│           ├── __init__.py
│           └── helpers.py           # Вспомогательные функции
│
├── data/                            # Создаётся автоматически
│   ├── database/
│   │   └── warehouse.db
│   ├── receipts/
│   │   └── YYYY-MM-DD_<id>/
│   │       ├── document.pdf
│   │       └── video.avi
│   └── logs/
│
├── requirements.txt                 # ✅ ГОТОВО
├── README.md
├── run_server.bat
└── run_client.bat
```

---

## 📊 ПЛАН РАЗРАБОТКИ ПО ЭТАПАМ

### ОБЗОР ЭТАПОВ

```
ЭТАП 1: Сервер - База данных        ████░░░░░░  3 часа
ЭТАП 2: Сервер - API роутеры        ████░░░░░░  4 часа
ЭТАП 3: Клиент - Сервисы            █████░░░░░  5 часов
ЭТАП 4: Клиент - UI диалоги         █████░░░░░  5 часов
ЭТАП 5: Клиент - MainWindow         ███░░░░░░░  3 часа
ЭТАП 6: Интеграция и тесты          ████░░░░░░  4 часа
                                    ═══════════════════
                                    ИТОГО: ~24 часа
```

---

## 🗄️ ЭТАП 1: СЕРВЕР — БАЗА ДАННЫХ (3 часа)

### Цель
Реализовать слой данных: Peewee модели, миграции, CRUD операции.

### Схема таблиц (SQLite)

```sql
-- Товары (справочник)
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    unit VARCHAR(20) DEFAULT 'шт',
    requires_control BOOLEAN DEFAULT 0,
    control_type VARCHAR(50),
    control_params TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Приёмки ТМЦ
CREATE TABLE receptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ttn_number VARCHAR(100) NOT NULL,
    ttn_date DATE NOT NULL,
    supplier VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    document_path VARCHAR(500),
    video_path VARCHAR(500),
    ocr_result TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    synced_at TIMESTAMP
);

-- Позиции приёмки
CREATE TABLE reception_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reception_id INTEGER NOT NULL,
    product_id INTEGER,
    article VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    quantity REAL,
    unit VARCHAR(20) DEFAULT 'шт',
    control_required BOOLEAN DEFAULT 0,
    control_status VARCHAR(20),
    control_result TEXT,  -- JSON
    notes TEXT,
    suspicious_fields TEXT,  -- JSON array
    FOREIGN KEY (reception_id) REFERENCES receptions(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Индексы
CREATE INDEX idx_products_article ON products(article);
CREATE INDEX idx_receptions_status ON receptions(status);
CREATE INDEX idx_items_reception ON reception_items(reception_id);
```

### Задачи

| # | Задача | Файл | Статус |
|---|--------|------|--------|
| 1.1 | Загрузчик конфига для сервера | server/src/config.py | ⬜ |
| 1.2 | Peewee модели (Product, Reception, ReceptionItem) | server/src/db/models.py | ⬜ |
| 1.3 | Миграции (создание таблиц + seed данные) | server/src/db/migrations.py | ⬜ |
| 1.4 | Repository (CRUD операции) | server/src/db/repository.py | ⬜ |

### Файл: server/src/config.py

```python
"""Загрузка конфигурации сервера."""
import json
from pathlib import Path
from typing import Any, Dict

_config: Dict[str, Any] = {}

def load_config() -> Dict[str, Any]:
    """Загрузить конфиг из config/config.json."""
    global _config
    if _config:
        return _config
    
    # Путь относительно корня проекта
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)
    
    return _config

def get_config() -> Dict[str, Any]:
    """Получить загруженный конфиг."""
    if not _config:
        return load_config()
    return _config
```

### Файл: server/src/db/models.py

```python
"""Peewee ORM модели для SQLite."""
import json
from datetime import datetime, date
from pathlib import Path

from peewee import (
    SqliteDatabase, Model, AutoField, CharField, TextField,
    BooleanField, FloatField, DateField, DateTimeField,
    ForeignKeyField, IntegerField
)

from server.src.config import get_config

# Инициализация БД
def get_database() -> SqliteDatabase:
    config = get_config()
    db_path = Path(config["paths"]["database"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return SqliteDatabase(str(db_path), pragmas={
        'journal_mode': 'wal',
        'cache_size': -1024 * 64,
        'foreign_keys': 1,
    })

database = get_database()


class BaseModel(Model):
    """Базовая модель с привязкой к БД."""
    class Meta:
        database = database


class Product(BaseModel):
    """Товар (справочник)."""
    id = AutoField()
    article = CharField(max_length=50, unique=True)
    name = CharField(max_length=255)
    unit = CharField(max_length=20, default="шт")
    requires_control = BooleanField(default=False)
    control_type = CharField(max_length=50, null=True)
    control_params = TextField(null=True)  # JSON
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "products"

    def get_control_params_dict(self) -> dict:
        if self.control_params:
            return json.loads(self.control_params)
        return {}


class Reception(BaseModel):
    """Приёмка ТМЦ."""
    id = AutoField()
    ttn_number = CharField(max_length=100)
    ttn_date = DateField()
    supplier = CharField(max_length=255)
    status = CharField(max_length=20, default="pending")
    document_path = CharField(max_length=500, null=True)
    video_path = CharField(max_length=500, null=True)
    ocr_result = TextField(null=True)  # JSON
    created_at = DateTimeField(default=datetime.now)
    completed_at = DateTimeField(null=True)
    synced_at = DateTimeField(null=True)

    class Meta:
        table_name = "receptions"


class ReceptionItem(BaseModel):
    """Позиция приёмки."""
    id = AutoField()
    reception = ForeignKeyField(Reception, backref="items", on_delete="CASCADE")
    product = ForeignKeyField(Product, null=True, backref="reception_items")
    article = CharField(max_length=50, null=True)
    name = CharField(max_length=255)
    quantity = FloatField(null=True)
    unit = CharField(max_length=20, default="шт")
    control_required = BooleanField(default=False)
    control_status = CharField(max_length=20, null=True)
    control_result = TextField(null=True)  # JSON
    notes = TextField(null=True)
    suspicious_fields = TextField(null=True)  # JSON array

    class Meta:
        table_name = "reception_items"

    def get_suspicious_fields_list(self) -> list:
        if self.suspicious_fields:
            return json.loads(self.suspicious_fields)
        return []
```

### Файл: server/src/db/migrations.py

```python
"""Инициализация БД и seed данные."""
import json
from server.src.db.models import database, Product, Reception, ReceptionItem


def init_db():
    """Создать таблицы если не существуют."""
    with database:
        database.create_tables([Product, Reception, ReceptionItem], safe=True)


def seed_products():
    """Заполнить справочник тестовыми товарами."""
    products_data = [
        {
            "article": "BOLT-M10",
            "name": "Болт М10х50",
            "unit": "шт",
            "requires_control": True,
            "control_type": "weight_check",
            "control_params": json.dumps({"target_weight": 2.0, "tolerance": 0.2})
        },
        {
            "article": "NUT-M10",
            "name": "Гайка М10",
            "unit": "шт",
            "requires_control": False,
            "control_type": None,
            "control_params": None
        },
        {
            "article": "WASHER-M10",
            "name": "Шайба М10",
            "unit": "шт",
            "requires_control": False,
            "control_type": None,
            "control_params": None
        },
        {
            "article": "CAM-HD-01",
            "name": "Камера HD 1080p",
            "unit": "шт",
            "requires_control": True,
            "control_type": "visual_check",
            "control_params": json.dumps({
                "checklist": ["Проверить корпус", "Проверить объектив", "Проверить кабель"]
            })
        },
        {
            "article": "PIPE-50",
            "name": "Труба 50мм",
            "unit": "м",
            "requires_control": True,
            "control_type": "dimension_check",
            "control_params": json.dumps({
                "length": 6.0, "tolerance": 0.05
            })
        },
    ]

    with database.atomic():
        for p in products_data:
            Product.get_or_create(article=p["article"], defaults=p)


def reset_db():
    """Удалить и пересоздать таблицы (для тестов)."""
    with database:
        database.drop_tables([ReceptionItem, Reception, Product], safe=True)
        init_db()
        seed_products()


if __name__ == "__main__":
    init_db()
    seed_products()
    print("Database initialized with seed data.")
```

### Файл: server/src/db/repository.py

```python
"""CRUD операции с базой данных."""
import json
from datetime import datetime
from typing import List, Optional

from peewee import fn

from server.src.db.models import database, Product, Reception, ReceptionItem
from common.models import (
    ProductCreate, ProductRead,
    ReceptionCreate, ReceptionRead, ReceptionShort, ReceptionItemRead,
    ReceptionStatus, ControlStatus
)


class ProductRepository:
    """Репозиторий для работы с товарами."""

    @staticmethod
    def get_all(limit: int = 100, offset: int = 0) -> List[ProductRead]:
        """Получить список товаров."""
        query = Product.select().limit(limit).offset(offset)
        return [ProductRepository._to_read(p) for p in query]

    @staticmethod
    def get_by_article(article: str) -> Optional[ProductRead]:
        """Найти товар по артикулу."""
        product = Product.get_or_none(Product.article == article)
        if product:
            return ProductRepository._to_read(product)
        return None

    @staticmethod
    def create(data: ProductCreate) -> ProductRead:
        """Создать товар."""
        product = Product.create(
            article=data.article,
            name=data.name,
            unit=data.unit,
            requires_control=data.requires_control,
            control_type=data.control_type.value if data.control_type else None,
            control_params=json.dumps(data.control_params) if data.control_params else None
        )
        return ProductRepository._to_read(product)

    @staticmethod
    def _to_read(p: Product) -> ProductRead:
        from common.models import ControlType
        return ProductRead(
            id=p.id,
            article=p.article,
            name=p.name,
            unit=p.unit,
            requires_control=p.requires_control,
            control_type=ControlType(p.control_type) if p.control_type else None,
            control_params=p.get_control_params_dict() if p.control_params else None,
            created_at=p.created_at
        )


class ReceptionRepository:
    """Репозиторий для работы с приёмками."""

    @staticmethod
    def create(data: ReceptionCreate) -> ReceptionRead:
        """Создать приёмку с позициями."""
        with database.atomic():
            reception = Reception.create(
                ttn_number=data.ttn_number,
                ttn_date=data.ttn_date,
                supplier=data.supplier,
                status=ReceptionStatus.PENDING.value
            )

            for item_data in data.items:
                # Попробовать найти товар по артикулу
                product = Product.get_or_none(Product.article == item_data.article)
                
                # Определить нужен ли контроль
                control_required = item_data.control_required
                if product and product.requires_control:
                    control_required = True

                ReceptionItem.create(
                    reception=reception,
                    product=product,
                    article=item_data.article,
                    name=item_data.name,
                    quantity=item_data.quantity,
                    unit=item_data.unit,
                    control_required=control_required,
                    control_status=ControlStatus.PENDING.value if control_required else None,
                    notes=item_data.notes,
                    suspicious_fields=json.dumps(item_data.suspicious_fields) if item_data.suspicious_fields else None
                )

            return ReceptionRepository.get_by_id(reception.id)

    @staticmethod
    def get_all(
        status: Optional[ReceptionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ReceptionShort]:
        """Получить список приёмок."""
        query = Reception.select().order_by(Reception.created_at.desc())
        if status:
            query = query.where(Reception.status == status.value)
        query = query.limit(limit).offset(offset)

        return [
            ReceptionShort(
                id=r.id,
                ttn_number=r.ttn_number,
                ttn_date=r.ttn_date,
                supplier=r.supplier,
                status=ReceptionStatus(r.status),
                created_at=r.created_at
            )
            for r in query
        ]

    @staticmethod
    def get_by_id(reception_id: int) -> Optional[ReceptionRead]:
        """Получить приёмку по ID с позициями."""
        reception = Reception.get_or_none(Reception.id == reception_id)
        if not reception:
            return None

        items = ReceptionItem.select().where(ReceptionItem.reception == reception)

        return ReceptionRead(
            id=reception.id,
            ttn_number=reception.ttn_number,
            ttn_date=reception.ttn_date,
            supplier=reception.supplier,
            status=ReceptionStatus(reception.status),
            created_at=reception.created_at,
            completed_at=reception.completed_at,
            synced_at=reception.synced_at,
            document_path=reception.document_path,
            video_path=reception.video_path,
            items=[ReceptionRepository._item_to_read(item) for item in items]
        )

    @staticmethod
    def update_document_path(reception_id: int, path: str) -> bool:
        """Обновить путь к документу."""
        updated = Reception.update(document_path=path).where(Reception.id == reception_id).execute()
        return updated > 0

    @staticmethod
    def update_video_path(reception_id: int, path: str) -> bool:
        """Обновить путь к видео."""
        updated = Reception.update(video_path=path).where(Reception.id == reception_id).execute()
        return updated > 0

    @staticmethod
    def update_control_results(reception_id: int, items_updates: list) -> Optional[ReceptionRead]:
        """Обновить результаты контроля по позициям."""
        reception = Reception.get_or_none(Reception.id == reception_id)
        if not reception:
            return None

        with database.atomic():
            for update in items_updates:
                ReceptionItem.update(
                    control_status=update.control_status.value,
                    control_result=json.dumps(update.control_result) if update.control_result else None,
                    notes=update.notes
                ).where(ReceptionItem.id == update.id).execute()

            # Проверить завершены ли все позиции
            pending_count = ReceptionItem.select().where(
                (ReceptionItem.reception == reception) &
                (ReceptionItem.control_required == True) &
                (ReceptionItem.control_status == ControlStatus.PENDING.value)
            ).count()

            if pending_count == 0:
                Reception.update(
                    status=ReceptionStatus.COMPLETED.value,
                    completed_at=datetime.now()
                ).where(Reception.id == reception_id).execute()

        return ReceptionRepository.get_by_id(reception_id)

    @staticmethod
    def _item_to_read(item: ReceptionItem) -> ReceptionItemRead:
        return ReceptionItemRead(
            id=item.id,
            reception_id=item.reception.id,
            product_id=item.product.id if item.product else None,
            article=item.article,
            name=item.name,
            quantity=item.quantity,
            unit=item.unit,
            control_required=item.control_required,
            control_status=ControlStatus(item.control_status) if item.control_status else None,
            control_result=json.loads(item.control_result) if item.control_result else None,
            notes=item.notes,
            suspicious_fields=item.get_suspicious_fields_list()
        )
```

### Тесты этапа 1

```python
# tests/test_server_db.py
import pytest
from server.src.db.migrations import init_db, seed_products, reset_db
from server.src.db.repository import ProductRepository, ReceptionRepository
from common.models import ReceptionCreate, ReceptionItemCreate

@pytest.fixture(autouse=True)
def setup_db():
    reset_db()
    yield

def test_get_products():
    products = ProductRepository.get_all()
    assert len(products) >= 5
    assert products[0].article == "BOLT-M10"

def test_get_product_by_article():
    product = ProductRepository.get_by_article("BOLT-M10")
    assert product is not None
    assert product.requires_control == True
    assert product.control_type.value == "weight_check"

def test_product_not_found():
    product = ProductRepository.get_by_article("NONEXISTENT")
    assert product is None

def test_create_reception():
    data = ReceptionCreate(
        ttn_number="TEST-001",
        ttn_date="2025-01-15",
        supplier="ООО Тест",
        items=[
            ReceptionItemCreate(
                article="BOLT-M10",
                name="Болт М10",
                quantity=100,
                unit="шт"
            )
        ]
    )
    reception = ReceptionRepository.create(data)
    assert reception.id > 0
    assert reception.ttn_number == "TEST-001"
    assert len(reception.items) == 1
    assert reception.items[0].control_required == True  # Из справочника

def test_get_reception_by_id():
    # Сначала создать
    data = ReceptionCreate(
        ttn_number="TEST-002",
        ttn_date="2025-01-15",
        supplier="ООО Тест2",
        items=[]
    )
    created = ReceptionRepository.create(data)
    
    # Потом получить
    reception = ReceptionRepository.get_by_id(created.id)
    assert reception is not None
    assert reception.ttn_number == "TEST-002"
```

### ✅ Чеклист этапа 1

- [ ] config.py загружает конфигурацию
- [ ] Peewee модели созданы (Product, Reception, ReceptionItem)
- [ ] Миграции создают таблицы
- [ ] Seed данные загружаются
- [ ] ProductRepository: get_all, get_by_article
- [ ] ReceptionRepository: create, get_all, get_by_id, update_*
- [ ] Все тесты проходят

---

## 🌐 ЭТАП 2: СЕРВЕР — API РОУТЕРЫ (4 часа)

### Цель
Реализовать REST API эндпоинты согласно спецификации из docs/API.md.

### Задачи

| # | Задача | Файл | Статус |
|---|--------|------|--------|
| 2.1 | Health роутер | server/src/api/routes_health.py | ⬜ |
| 2.2 | Products роутер | server/src/api/routes_products.py | ⬜ |
| 2.3 | Receptions роутер | server/src/api/routes_receptions.py | ⬜ |
| 2.4 | Files роутер (upload) | server/src/api/routes_files.py | ⬜ |
| 2.5 | Обновить main_server.py | server/src/main_server.py | ⬜ |

### Файл: server/src/api/routes_health.py

```python
"""Health check endpoint."""
from datetime import datetime
from fastapi import APIRouter
from common.models import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Проверка работоспособности сервера."""
    return HealthResponse(status="ok", time=datetime.utcnow())
```

### Файл: server/src/api/routes_products.py

```python
"""Эндпоинты для работы с товарами."""
from typing import List
from fastapi import APIRouter, HTTPException, Query

from common.models import ProductRead, APIError
from server.src.db.repository import ProductRepository

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=List[ProductRead])
def get_products(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> List[ProductRead]:
    """Получить список товаров."""
    return ProductRepository.get_all(limit=limit, offset=offset)


@router.get("/{article}", response_model=ProductRead, responses={404: {"model": APIError}})
def get_product_by_article(article: str) -> ProductRead:
    """Получить товар по артикулу."""
    product = ProductRepository.get_by_article(article)
    if not product:
        raise HTTPException(
            status_code=404,
            detail={"detail": "Product not found", "code": "product_not_found"}
        )
    return product
```

### Файл: server/src/api/routes_receptions.py

```python
"""Эндпоинты для работы с приёмками."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body

from common.models import (
    ReceptionCreate, ReceptionRead, ReceptionShort,
    ReceptionStatus, ReceptionItemControlUpdate, APIError
)
from server.src.db.repository import ReceptionRepository

router = APIRouter(prefix="/receptions", tags=["Receptions"])


@router.post("", response_model=ReceptionRead, status_code=201)
def create_reception(data: ReceptionCreate) -> ReceptionRead:
    """Создать новую приёмку."""
    return ReceptionRepository.create(data)


@router.get("", response_model=List[ReceptionShort])
def get_receptions(
    status: Optional[ReceptionStatus] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> List[ReceptionShort]:
    """Получить список приёмок."""
    return ReceptionRepository.get_all(status=status, limit=limit, offset=offset)


@router.get("/{reception_id}", response_model=ReceptionRead, responses={404: {"model": APIError}})
def get_reception(reception_id: int) -> ReceptionRead:
    """Получить приёмку по ID."""
    reception = ReceptionRepository.get_by_id(reception_id)
    if not reception:
        raise HTTPException(
            status_code=404,
            detail={"detail": "Reception not found", "code": "reception_not_found"}
        )
    return reception


@router.post("/{reception_id}/control-results", response_model=ReceptionRead, responses={404: {"model": APIError}})
def update_control_results(
    reception_id: int,
    items: List[ReceptionItemControlUpdate] = Body(..., embed=True, alias="items")
) -> ReceptionRead:
    """Обновить результаты контроля по позициям."""
    reception = ReceptionRepository.update_control_results(reception_id, items)
    if not reception:
        raise HTTPException(
            status_code=404,
            detail={"detail": "Reception not found", "code": "reception_not_found"}
        )
    return reception
```

### Файл: server/src/api/routes_files.py

```python
"""Эндпоинты для загрузки файлов."""
import shutil
from pathlib import Path
from datetime import date

from fastapi import APIRouter, HTTPException, UploadFile, File

from server.src.config import get_config
from server.src.db.repository import ReceptionRepository

router = APIRouter(prefix="/receptions", tags=["Files"])


def get_receipt_folder(reception_id: int) -> Path:
    """Получить/создать папку для приёмки."""
    config = get_config()
    base_path = Path(config["paths"]["receipts_root"])
    folder_name = f"{date.today().isoformat()}_{reception_id:04d}"
    folder_path = base_path / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path


@router.post("/{reception_id}/document")
async def upload_document(reception_id: int, file: UploadFile = File(...)):
    """Загрузить документ ТТН."""
    reception = ReceptionRepository.get_by_id(reception_id)
    if not reception:
        raise HTTPException(status_code=404, detail="Reception not found")

    folder = get_receipt_folder(reception_id)
    
    # Определить расширение
    ext = Path(file.filename).suffix or ".pdf"
    file_path = folder / f"document{ext}"

    # Сохранить файл
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Обновить путь в БД (относительный)
    relative_path = str(file_path.relative_to(Path(get_config()["paths"]["receipts_root"]).parent))
    ReceptionRepository.update_document_path(reception_id, relative_path)

    return {"id": reception_id, "document_path": relative_path}


@router.post("/{reception_id}/video")
async def upload_video(reception_id: int, file: UploadFile = File(...)):
    """Загрузить видео контроля."""
    reception = ReceptionRepository.get_by_id(reception_id)
    if not reception:
        raise HTTPException(status_code=404, detail="Reception not found")

    folder = get_receipt_folder(reception_id)
    
    ext = Path(file.filename).suffix or ".avi"
    file_path = folder / f"video{ext}"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    relative_path = str(file_path.relative_to(Path(get_config()["paths"]["receipts_root"]).parent))
    ReceptionRepository.update_video_path(reception_id, relative_path)

    return {"id": reception_id, "video_path": relative_path}
```

### Файл: server/src/main_server.py (обновлённый)

```python
"""Точка входа сервера FastAPI."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.src.config import load_config
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
config = load_config()
app = FastAPI(
    title=config["app"]["name"],
    version=config["app"]["version"],
    lifespan=lifespan
)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
        log_level="info"
    )
```

### Тесты этапа 2

```python
# tests/test_server_api.py
import pytest
from fastapi.testclient import TestClient
from server.src.main_server import app
from server.src.db.migrations import reset_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup():
    reset_db()
    yield

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_products():
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    assert len(response.json()) >= 5

def test_get_product_by_article():
    response = client.get("/api/v1/products/BOLT-M10")
    assert response.status_code == 200
    assert response.json()["article"] == "BOLT-M10"

def test_product_not_found():
    response = client.get("/api/v1/products/NONEXISTENT")
    assert response.status_code == 404

def test_create_reception():
    response = client.post("/api/v1/receptions", json={
        "ttn_number": "ТТН-001",
        "ttn_date": "2025-01-15",
        "supplier": "ООО Тест",
        "items": [
            {"article": "BOLT-M10", "name": "Болт М10", "quantity": 100, "unit": "шт"}
        ]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["status"] == "pending"

def test_get_receptions():
    # Создать
    client.post("/api/v1/receptions", json={
        "ttn_number": "ТТН-002",
        "ttn_date": "2025-01-15",
        "supplier": "ООО Тест",
        "items": []
    })
    
    response = client.get("/api/v1/receptions")
    assert response.status_code == 200
    assert len(response.json()) >= 1
```

### ✅ Чеклист этапа 2

- [ ] GET /api/v1/health работает
- [ ] GET /api/v1/products возвращает список
- [ ] GET /api/v1/products/{article} работает
- [ ] POST /api/v1/receptions создаёт приёмку
- [ ] GET /api/v1/receptions возвращает список
- [ ] GET /api/v1/receptions/{id} возвращает детали
- [ ] POST /api/v1/receptions/{id}/document загружает файл
- [ ] POST /api/v1/receptions/{id}/video загружает видео
- [ ] POST /api/v1/receptions/{id}/control-results обновляет контроль
- [ ] Все тесты API проходят

---

## ⚙️ ЭТАП 3: КЛИЕНТ — СЕРВИСЫ (5 часов)

### Цель
Реализовать бизнес-логику клиента: OCR, камера, синхронизация с сервером.

### Задачи

| # | Задача | Файл | Статус |
|---|--------|------|--------|
| 3.1 | Загрузчик конфига клиента | client/src/config.py | ⬜ |
| 3.2 | HTTP клиент к серверу | client/src/services/sync_service.py | ⬜ |
| 3.3 | OCR распознавание | client/src/services/ocr_service.py | ⬜ |
| 3.4 | Работа с камерой | client/src/services/camera_service.py | ⬜ |
| 3.5 | Валидация контроля | client/src/services/validator_service.py | ⬜ |
| 3.6 | Локальное хранение | client/src/services/storage_service.py | ⬜ |

### Файл: client/src/services/sync_service.py

```python
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
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            return response.status_code == 200
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
        try:
            response = requests.post(
                f"{self.base_url}/receptions",
                json=data.model_dump(mode="json"),
                timeout=self.timeout
            )
            response.raise_for_status()
            return ReceptionRead(**response.json())
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
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    f"{self.base_url}/receptions/{reception_id}/document",
                    files={"file": (file_path.name, f)},
                    timeout=self.timeout * 2  # Больше времени для загрузки
                )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to upload document: {e}")
            return False

    def upload_video(self, reception_id: int, file_path: Path) -> bool:
        """Загрузить видео."""
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    f"{self.base_url}/receptions/{reception_id}/video",
                    files={"file": (file_path.name, f)},
                    timeout=self.timeout * 5  # Ещё больше для видео
                )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to upload video: {e}")
            return False

    def send_control_results(
        self,
        reception_id: int,
        items: List[ReceptionItemControlUpdate]
    ) -> Optional[ReceptionRead]:
        """Отправить результаты контроля."""
        try:
            response = requests.post(
                f"{self.base_url}/receptions/{reception_id}/control-results",
                json={"items": [item.model_dump(mode="json") for item in items]},
                timeout=self.timeout
            )
            response.raise_for_status()
            return ReceptionRead(**response.json())
        except requests.RequestException as e:
            logger.error(f"Failed to send control results: {e}")
            return None
```

### Файл: client/src/services/ocr_service.py

```python
"""OCR сервис для распознавания документов ТТН."""
import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import date

import cv2
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

from client.src.config import get_config
from common.models import OCRResult, OCRItem, ReceptionItemCreate

logger = logging.getLogger(__name__)

# Паттерны для извлечения данных
PATTERNS = {
    "ttn_number": r"(?:ТТН|накладная|товарн\w*\s*накладн\w*)[^\d]*[№#]?\s*(\d[\d\-/]+)",
    "date": r"(\d{2})[./](\d{2})[./](\d{2,4})",
    "supplier": r"(?:поставщик|грузоотправитель|от(?:правитель)?)[:\s]+([А-Яа-яЁё\s\"\-]+(?:ООО|ИП|АО|ЗАО)?[А-Яа-яЁё\s\"\-]*)",
    "article": r"(?:арт(?:икул)?\.?|art\.?)[:\s]*([A-Za-zА-Яа-я0-9\-]+)",
    "quantity": r"(\d+(?:[.,]\d+)?)\s*(шт|кг|м|л|уп|ед)?\.?",
}


class OCRService:
    """Сервис распознавания документов."""

    def __init__(self):
        config = get_config()
        self.tesseract_path = config["tesseract"]["path"]
        self.languages = "+".join(config["tesseract"]["languages"])
        self.psm = config["tesseract"]["psm"]
        self.poppler_path = config["poppler"]["path"]

        # Настройка pytesseract
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

    def process_document(self, file_path: Path) -> OCRResult:
        """Обработать документ (PDF или изображение)."""
        logger.info(f"Processing document: {file_path}")

        # Конвертировать в изображения
        if file_path.suffix.lower() == ".pdf":
            images = self._pdf_to_images(file_path)
        else:
            images = [cv2.imread(str(file_path))]

        if not images:
            logger.error("Failed to load images from document")
            return OCRResult()

        # Объединить текст со всех страниц
        full_text = ""
        for img in images:
            processed = self._preprocess_image(img)
            text = self._extract_text(processed)
            full_text += text + "\n"

        # Парсить результат
        return self._parse_ttn(full_text)

    def _pdf_to_images(self, pdf_path: Path) -> List[np.ndarray]:
        """Конвертировать PDF в список изображений."""
        try:
            pil_images = convert_from_path(
                str(pdf_path),
                poppler_path=self.poppler_path,
                dpi=300
            )
            return [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in pil_images]
        except Exception as e:
            logger.error(f"Failed to convert PDF: {e}")
            return []

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Предобработка изображения для OCR."""
        # Конвертировать в grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Бинаризация (адаптивный threshold)
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        # Удаление шума
        denoised = cv2.medianBlur(binary, 3)

        return denoised

    def _extract_text(self, image: np.ndarray) -> str:
        """Извлечь текст из изображения."""
        try:
            config = f"--psm {self.psm} --oem 3"
            text = pytesseract.image_to_string(
                image,
                lang=self.languages,
                config=config
            )
            return text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def _parse_ttn(self, text: str) -> OCRResult:
        """Парсить текст ТТН и извлечь данные."""
        result = OCRResult()

        # Извлечь номер ТТН
        match = re.search(PATTERNS["ttn_number"], text, re.IGNORECASE)
        if match:
            result.ttn_number = match.group(1).strip()

        # Извлечь дату
        match = re.search(PATTERNS["date"], text)
        if match:
            day, month, year = match.groups()
            if len(year) == 2:
                year = "20" + year
            try:
                result.ttn_date = date(int(year), int(month), int(day))
            except ValueError:
                pass

        # Извлечь поставщика
        match = re.search(PATTERNS["supplier"], text, re.IGNORECASE)
        if match:
            result.supplier = match.group(1).strip()

        # Извлечь позиции (упрощённая логика)
        result.items = self._extract_items(text)

        return result

    def _extract_items(self, text: str) -> List[OCRItem]:
        """Извлечь позиции товаров из текста."""
        items = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue

            item = OCRItem(raw_text=line)
            confidence = {}

            # Попробовать найти артикул
            match = re.search(PATTERNS["article"], line, re.IGNORECASE)
            if match:
                item.article = match.group(1).strip()
                confidence["article"] = 0.7  # Примерная уверенность

            # Попробовать найти количество
            match = re.search(PATTERNS["quantity"], line)
            if match:
                qty_str = match.group(1).replace(",", ".")
                try:
                    item.quantity = float(qty_str)
                    confidence["quantity"] = 0.8
                except ValueError:
                    pass
                if match.group(2):
                    item.unit = match.group(2)
                    confidence["unit"] = 0.9

            # Если есть хотя бы артикул или количество - это может быть позиция
            if item.article or item.quantity:
                # Имя = вся строка минус найденные части (упрощённо)
                item.name = line[:50]  # Первые 50 символов как имя
                confidence["name"] = 0.5

                item.field_confidence = confidence
                items.append(item)

        return items

    def ocr_items_to_reception_items(
        self,
        ocr_items: List[OCRItem],
        confidence_threshold: float = 0.6
    ) -> List[ReceptionItemCreate]:
        """Конвертировать OCR результаты в позиции для создания приёмки."""
        result = []

        for ocr_item in ocr_items:
            suspicious = []
            
            # Проверить уверенность по каждому полю
            for field, conf in ocr_item.field_confidence.items():
                if conf < confidence_threshold:
                    suspicious.append(field)

            item = ReceptionItemCreate(
                article=ocr_item.article or "",
                name=ocr_item.name or ocr_item.raw_text[:100],
                quantity=ocr_item.quantity or 0,
                unit=ocr_item.unit or "шт",
                suspicious_fields=suspicious
            )
            result.append(item)

        return result
```

### Файл: client/src/services/camera_service.py

```python
"""Сервис для работы с веб-камерой."""
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal, QThread, QMutex
from PySide6.QtGui import QImage

from client.src.config import get_config

logger = logging.getLogger(__name__)


class CameraWorker(QThread):
    """Поток для захвата видео с камеры."""
    frame_ready = Signal(QImage)
    error = Signal(str)

    def __init__(self, camera_index: int, resolution: tuple, fps: int):
        super().__init__()
        self.camera_index = camera_index
        self.resolution = resolution
        self.fps = fps
        self.running = False
        self.capture = None
        self.mutex = QMutex()

        # Для записи
        self.recording = False
        self.video_writer = None
        self.output_path = None

    def run(self):
        """Основной цикл захвата."""
        self.capture = cv2.VideoCapture(self.camera_index)
        if not self.capture.isOpened():
            self.error.emit("Не удалось открыть камеру")
            return

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)

        self.running = True

        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                continue

            # Записать кадр если идёт запись
            self.mutex.lock()
            if self.recording and self.video_writer:
                self.video_writer.write(frame)
            self.mutex.unlock()

            # Конвертировать в QImage для отображения
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frame_ready.emit(q_image.copy())

            # Ограничить FPS
            self.msleep(int(1000 / self.fps))

        # Очистка
        if self.video_writer:
            self.video_writer.release()
        self.capture.release()

    def start_recording(self, output_path: Path):
        """Начать запись видео."""
        self.mutex.lock()
        config = get_config()
        codec = cv2.VideoWriter_fourcc(*config["camera"]["codec"])
        self.output_path = output_path
        self.video_writer = cv2.VideoWriter(
            str(output_path),
            codec,
            self.fps,
            self.resolution
        )
        self.recording = True
        self.mutex.unlock()
        logger.info(f"Started recording to {output_path}")

    def stop_recording(self) -> Optional[Path]:
        """Остановить запись и вернуть путь к файлу."""
        self.mutex.lock()
        self.recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        path = self.output_path
        self.output_path = None
        self.mutex.unlock()
        logger.info(f"Stopped recording: {path}")
        return path

    def stop(self):
        """Остановить захват."""
        self.running = False
        self.wait()


class CameraService(QObject):
    """Сервис управления камерой."""
    frame_ready = Signal(QImage)
    recording_started = Signal()
    recording_stopped = Signal(str)  # путь к файлу
    error = Signal(str)

    def __init__(self):
        super().__init__()
        config = get_config()
        self.camera_index = config["camera"]["default_index"]
        self.resolution = tuple(config["camera"]["resolution"])
        self.fps = config["camera"]["fps"]
        self.container = config["camera"]["container"]
        
        self.worker: Optional[CameraWorker] = None

    @staticmethod
    def list_available_cameras(max_check: int = 5) -> List[int]:
        """Получить список доступных камер."""
        available = []
        for i in range(max_check):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available

    def start_preview(self, camera_index: Optional[int] = None):
        """Запустить превью с камеры."""
        if self.worker and self.worker.isRunning():
            self.stop_preview()

        index = camera_index if camera_index is not None else self.camera_index
        self.worker = CameraWorker(index, self.resolution, self.fps)
        self.worker.frame_ready.connect(self.frame_ready.emit)
        self.worker.error.connect(self.error.emit)
        self.worker.start()

    def stop_preview(self):
        """Остановить превью."""
        if self.worker:
            self.worker.stop()
            self.worker = None

    def start_recording(self, output_dir: Path) -> Path:
        """Начать запись видео."""
        if not self.worker:
            raise RuntimeError("Camera not started")

        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"video_{datetime.now().strftime('%H%M%S')}.{self.container}"
        output_path = output_dir / filename

        self.worker.start_recording(output_path)
        self.recording_started.emit()
        return output_path

    def stop_recording(self) -> Optional[Path]:
        """Остановить запись и вернуть путь."""
        if not self.worker:
            return None

        path = self.worker.stop_recording()
        if path:
            self.recording_stopped.emit(str(path))
        return path

    def is_recording(self) -> bool:
        """Проверить идёт ли запись."""
        return self.worker is not None and self.worker.recording
```

### Файл: client/src/services/validator_service.py

```python
"""Сервис валидации входного контроля."""
from typing import Dict, Any, Callable

from common.models import ValidationResult, ControlType
from client.src.config import get_config


class ValidatorService:
    """Сервис для выполнения различных типов контроля."""

    def __init__(self):
        self.validators: Dict[ControlType, Callable] = {
            ControlType.WEIGHT_CHECK: self._validate_weight,
            ControlType.QUANTITY_CHECK: self._validate_quantity,
            ControlType.DIMENSION_CHECK: self._validate_dimension,
            ControlType.VISUAL_CHECK: self._validate_visual,
        }

    def validate(
        self,
        control_type: ControlType,
        params: Dict[str, Any],
        actual_values: Dict[str, Any]
    ) -> ValidationResult:
        """Выполнить валидацию по типу контроля."""
        validator = self.validators.get(control_type)
        if not validator:
            return ValidationResult(
                passed=False,
                message=f"Неизвестный тип контроля: {control_type}",
                details={}
            )
        return validator(params, actual_values)

    def get_instructions(self, control_type: ControlType, params: Dict[str, Any]) -> str:
        """Получить инструкции для оператора."""
        config = get_config()
        control_config = config["validation"]["control_types"].get(control_type.value, {})
        description = control_config.get("description", control_type.value)

        if control_type == ControlType.WEIGHT_CHECK:
            target = params.get("target_weight", "?")
            tolerance = params.get("tolerance", "?")
            return f"{description}\nОжидаемый вес: {target} кг (±{tolerance} кг)"

        elif control_type == ControlType.QUANTITY_CHECK:
            expected = params.get("expected_count", "?")
            return f"{description}\nОжидаемое количество: {expected}"

        elif control_type == ControlType.DIMENSION_CHECK:
            dims = []
            for d in ["length", "width", "height"]:
                if d in params:
                    dims.append(f"{d}: {params[d]}")
            tolerance = params.get("tolerance", "?")
            return f"{description}\nРазмеры: {', '.join(dims)} (±{tolerance})"

        elif control_type == ControlType.VISUAL_CHECK:
            checklist = params.get("checklist", [])
            items = "\n".join(f"• {item}" for item in checklist)
            return f"{description}\nЧек-лист:\n{items}"

        return description

    def _validate_weight(
        self,
        params: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> ValidationResult:
        """Проверка веса."""
        target = params.get("target_weight", 0)
        tolerance = params.get("tolerance", 0)
        measured = actual.get("measured_weight", 0)

        diff = abs(measured - target)
        passed = diff <= tolerance

        return ValidationResult(
            passed=passed,
            message="Вес в норме" if passed else f"Отклонение веса: {diff:.2f} кг",
            details={
                "target_weight": target,
                "tolerance": tolerance,
                "measured_weight": measured,
                "difference": diff
            }
        )

    def _validate_quantity(
        self,
        params: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> ValidationResult:
        """Проверка количества."""
        expected = params.get("expected_count", 0)
        counted = actual.get("counted", 0)

        passed = counted == expected

        return ValidationResult(
            passed=passed,
            message="Количество совпадает" if passed else f"Расхождение: {counted - expected}",
            details={
                "expected_count": expected,
                "counted": counted,
                "difference": counted - expected
            }
        )

    def _validate_dimension(
        self,
        params: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> ValidationResult:
        """Проверка размеров."""
        tolerance = params.get("tolerance", 0)
        issues = []

        for dim in ["length", "width", "height"]:
            if dim in params and dim in actual:
                expected = params[dim]
                measured = actual[dim]
                if abs(measured - expected) > tolerance:
                    issues.append(f"{dim}: {measured} (ожид. {expected})")

        passed = len(issues) == 0

        return ValidationResult(
            passed=passed,
            message="Размеры в норме" if passed else f"Отклонения: {', '.join(issues)}",
            details={
                "expected": {k: v for k, v in params.items() if k != "tolerance"},
                "measured": actual,
                "tolerance": tolerance
            }
        )

    def _validate_visual(
        self,
        params: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> ValidationResult:
        """Визуальный осмотр (всегда на усмотрение оператора)."""
        passed = actual.get("passed", False)
        notes = actual.get("notes", "")

        return ValidationResult(
            passed=passed,
            message="Визуальный осмотр пройден" if passed else "Обнаружены дефекты",
            details={
                "checklist": params.get("checklist", []),
                "operator_notes": notes,
                "operator_decision": passed
            }
        )
```

### ✅ Чеклист этапа 3

- [ ] config.py загружает конфигурацию клиента
- [ ] SyncService: check_health, get_products, create_reception, upload_*
- [ ] OCRService: process_document, pdf_to_images, preprocess, parse
- [ ] CameraService: list_cameras, start/stop_preview, start/stop_recording
- [ ] ValidatorService: validate по всем типам контроля
- [ ] Все сервисы логируют ошибки

---

## 🖥️ ЭТАП 4: КЛИЕНТ — UI ДИАЛОГИ (5 часов)

### Цель
Реализовать диалоговые окна: загрузка документа, результаты OCR, входной контроль.

### Задачи

| # | Задача | Файл | Статус |
|---|--------|------|--------|
| 4.1 | Виджет отображения видео | client/src/ui/video_widget.py | ⬜ |
| 4.2 | Таблица позиций с подсветкой | client/src/ui/results_widget.py | ⬜ |
| 4.3 | Диалог загрузки документа и OCR | client/src/ui/document_dialog.py | ⬜ |
| 4.4 | Диалог входного контроля | client/src/ui/control_dialog.py | ⬜ |
| 4.5 | Диалог истории приёмок | client/src/ui/history_dialog.py | ⬜ |
| 4.6 | QSS стили | client/src/ui/styles.py | ⬜ |

*(Код диалогов аналогичен предыдущим этапам — см. полную реализацию)*

### ✅ Чеклист этапа 4

- [ ] VideoWidget отображает кадры с камеры
- [ ] ResultsWidget показывает таблицу с подсветкой suspicious_fields
- [ ] DocumentDialog: выбор файла, OCR, редактирование, создание приёмки
- [ ] ControlDialog: видео, инструкции, ввод результатов
- [ ] HistoryDialog: список приёмок, детали
- [ ] Стили согласованы

---

## 🔗 ЭТАП 5: КЛИЕНТ — MAINWINDOW (3 часа)

### Цель
Собрать главное окно, интегрировать все компоненты.

### Задачи

| # | Задача | Файл | Статус |
|---|--------|------|--------|
| 5.1 | Обновить MainWindow | client/src/ui/main_window.py | ⬜ |
| 5.2 | Статус бар (сервер, камера) | client/src/ui/main_window.py | ⬜ |
| 5.3 | Интеграция диалогов | client/src/ui/main_window.py | ⬜ |
| 5.4 | Обновить main_client.py | client/src/main_client.py | ⬜ |

### ✅ Чеклист этапа 5

- [ ] MainWindow с тремя кнопками
- [ ] Статус бар показывает состояние сервера и камеры
- [ ] "Принять ТМЦ" открывает DocumentDialog
- [ ] "История" открывает HistoryDialog
- [ ] "Настройки" открывает диалог настроек
- [ ] Периодическая проверка health сервера

---

## 🧪 ЭТАП 6: ИНТЕГРАЦИЯ И ТЕСТЫ (4 часа)

### Цель
Провести E2E тестирование, исправить баги.

### Задачи

| # | Задача | Файл | Статус |
|---|--------|------|--------|
| 6.1 | E2E тест: полный цикл приёмки | tests/test_e2e.py | ⬜ |
| 6.2 | Тест: работа без камеры | tests/test_e2e.py | ⬜ |
| 6.3 | Тест: работа без сервера | tests/test_e2e.py | ⬜ |
| 6.4 | Исправление багов | - | ⬜ |
| 6.5 | Обновить bat-файлы | run_*.bat | ⬜ |
| 6.6 | Финальная проверка | - | ⬜ |

### E2E сценарии

```
СЦЕНАРИЙ 1: Полный цикл приёмки
1. Запустить сервер
2. Запустить клиент
3. Проверить статус "сервер онлайн"
4. Нажать "Принять ТМЦ"
5. Загрузить PDF
6. Проверить OCR результат
7. Исправить suspicious поля
8. Создать приёмку
9. Пройти входной контроль (если есть)
10. Проверить историю

СЦЕНАРИЙ 2: Без камеры
1. Запустить без камеры
2. Проверить предупреждение
3. Создать приёмку
4. Контроль без видео

СЦЕНАРИЙ 3: Сервер недоступен
1. Запустить клиент без сервера
2. Проверить статус "офлайн"
3. Попробовать создать приёмку
4. Проверить сообщение об ошибке
```

### ✅ Чеклист этапа 6

- [ ] Все E2E сценарии проходят
- [ ] Ошибки обрабатываются корректно
- [ ] Логи информативны
- [ ] bat-файлы работают
- [ ] README актуален

---

## 🔄 КОМАНДЫ ДЛЯ РАБОТЫ

### Начать этап:
```
Начинаю ЭТАП {N}: {название}
Задачи этапа: [список]
```

### Завершить задачу:
```
✅ Задача {N.M} выполнена: {название}
Файл: {путь}
```

### Завершить этап:
```
✅ ЭТАП {N} ЗАВЕРШЕН

Чеклист:
- [x] Пункт 1
- [x] Пункт 2

Тесты: все проходят

Переход к ЭТАПУ {N+1}
```

---

## 📊 ОБЩИЙ ЧЕКЛИСТ КАЧЕСТВА

Перед завершением проверь:

- [ ] Код типизирован (type hints)
- [ ] Есть docstrings
- [ ] Логирование ошибок
- [ ] Нет хардкода (всё из config)
- [ ] Исключения обрабатываются
- [ ] PEP 8 соблюдён
- [ ] Используются модели из common/models.py

---

## 🚀 НАЧАЛО РАБОТЫ

Для начала скажи:
**"Начинаю ЭТАП 1: СЕРВЕР — БАЗА ДАННЫХ"**

И последовательно выполняй задачи по плану.

---

**Версия промпта:** 2.0
**Дата:** 2025
**Архитектура:** Клиент-сервер (PySide6 + FastAPI)
