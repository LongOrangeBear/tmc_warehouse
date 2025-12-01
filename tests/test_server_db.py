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
