"""Peewee ORM модели для SQLite."""
import json
from datetime import datetime, date
from pathlib import Path
from typing import List

from peewee import (
    SqliteDatabase, Model, AutoField, CharField, TextField,
    BooleanField, FloatField, DateField, DateTimeField,
    ForeignKeyField, IntegerField
)

from server.src.config import get_config

# Инициализация БД
def get_database() -> SqliteDatabase:
    config = get_config()
    # Ensure we use absolute path for DB to avoid CWD issues
    db_path_str = config["paths"]["database"]
    if not Path(db_path_str).is_absolute():
        # Calculate project root dynamically: models.py is in server/src/db/
        project_root = Path(__file__).parent.parent.parent.parent
        db_path = project_root / db_path_str
    else:
        db_path = Path(db_path_str)
        
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
    suspicious_fields = TextField(null=True)  # JSON list of field names
    photos = TextField(null=True) # JSON list of photo paths

    class Meta:
        table_name = "reception_items"

    def get_suspicious_fields_list(self) -> List[str]:
        if self.suspicious_fields:
            return json.loads(self.suspicious_fields)
        return []
        
    def get_photos_list(self) -> List[str]:
        if self.photos:
            return json.loads(self.photos)
        return []
