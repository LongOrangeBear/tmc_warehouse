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
