# tests/test_models.py
"""
Тесты Pydantic моделей из common/models.py

Запуск:
    pytest tests/test_models.py -v
"""
import pytest
from datetime import date, datetime


class TestModelsImport:
    """Тесты импорта моделей."""
    
    def test_import_common_models(self):
        """Все модели импортируются без ошибок."""
        from common.models import (
            ControlType,
            ControlStatus,
            ReceptionStatus,
            SyncStatus,
            APIError,
            HealthResponse,
            ValidationResult,
            ProductBase,
            ProductCreate,
            ProductRead,
            ReceptionItemBase,
            ReceptionItemCreate,
            ReceptionItemRead,
            ReceptionBase,
            ReceptionCreate,
            ReceptionRead,
            ReceptionShort,
            OCRItem,
            OCRResult,
        )
        
        # Если дошли сюда - всё импортировалось
        assert True


class TestEnums:
    """Тесты Enum классов."""
    
    def test_control_type_values(self):
        """ControlType содержит все нужные значения."""
        from common.models import ControlType
        
        assert ControlType.WEIGHT_CHECK.value == "weight_check"
        assert ControlType.VISUAL_CHECK.value == "visual_check"
        assert ControlType.DIMENSION_CHECK.value == "dimension_check"
        assert ControlType.QUANTITY_CHECK.value == "quantity_check"
    
    def test_reception_status_values(self):
        """ReceptionStatus содержит все нужные значения."""
        from common.models import ReceptionStatus
        
        assert ReceptionStatus.PENDING.value == "pending"
        assert ReceptionStatus.IN_PROGRESS.value == "in_progress"
        assert ReceptionStatus.COMPLETED.value == "completed"
        assert ReceptionStatus.SYNCED.value == "synced"


class TestProductModels:
    """Тесты моделей товаров."""
    
    def test_product_create_minimal(self):
        """ProductCreate с минимальными полями."""
        from common.models import ProductCreate
        
        product = ProductCreate(
            article="TEST-001",
            name="Тестовый товар"
        )
        
        assert product.article == "TEST-001"
        assert product.name == "Тестовый товар"
        assert product.unit == "шт"  # default
        assert product.requires_control == False  # default
    
    def test_product_create_full(self):
        """ProductCreate со всеми полями."""
        from common.models import ProductCreate, ControlType
        
        product = ProductCreate(
            article="TEST-002",
            name="Товар с контролем",
            unit="кг",
            requires_control=True,
            control_type=ControlType.WEIGHT_CHECK,
            control_params={"target_weight": 10.0, "tolerance": 0.5}
        )
        
        assert product.requires_control == True
        assert product.control_type == ControlType.WEIGHT_CHECK
        assert product.control_params["target_weight"] == 10.0


class TestReceptionModels:
    """Тесты моделей приёмок."""
    
    def test_reception_create(self):
        """ReceptionCreate создаётся корректно."""
        from common.models import ReceptionCreate, ReceptionItemCreate
        
        reception = ReceptionCreate(
            ttn_number="ТТН-001",
            ttn_date=date(2025, 1, 15),
            supplier="ООО Тест",
            items=[
                ReceptionItemCreate(
                    article="TEST-001",
                    name="Товар",
                    quantity=100,
                    unit="шт"
                )
            ]
        )
        
        assert reception.ttn_number == "ТТН-001"
        assert len(reception.items) == 1
        assert reception.items[0].quantity == 100
    
    def test_reception_item_suspicious_fields(self):
        """ReceptionItemCreate с suspicious_fields."""
        from common.models import ReceptionItemCreate
        
        item = ReceptionItemCreate(
            article="TEST",
            name="Товар",
            quantity=10,
            unit="шт",
            suspicious_fields=["article", "quantity"]
        )
        
        assert "article" in item.suspicious_fields
        assert len(item.suspicious_fields) == 2


class TestOCRModels:
    """Тесты OCR моделей."""
    
    def test_ocr_item(self):
        """OCRItem создаётся корректно."""
        from common.models import OCRItem
        
        item = OCRItem(
            raw_text="BOLT-M10 Болт М10 100 шт",
            article="BOLT-M10",
            name="Болт М10",
            quantity=100,
            unit="шт",
            field_confidence={
                "article": 0.9,
                "name": 0.8,
                "quantity": 0.95,
                "unit": 0.85
            }
        )
        
        assert item.article == "BOLT-M10"
        assert item.field_confidence["article"] == 0.9
    
    def test_ocr_result(self):
        """OCRResult создаётся корректно."""
        from common.models import OCRResult, OCRItem
        
        result = OCRResult(
            ttn_number="ТТН-001",
            ttn_date=date(2025, 1, 15),
            supplier="ООО Поставщик",
            items=[
                OCRItem(raw_text="line 1"),
                OCRItem(raw_text="line 2")
            ]
        )
        
        assert result.ttn_number == "ТТН-001"
        assert len(result.items) == 2


class TestValidationResult:
    """Тесты ValidationResult."""
    
    def test_validation_passed(self):
        """ValidationResult для успешной проверки."""
        from common.models import ValidationResult
        
        result = ValidationResult(
            passed=True,
            message="Вес в норме",
            details={"measured": 10.0, "target": 10.0}
        )
        
        assert result.passed == True
        assert "measured" in result.details
    
    def test_validation_failed(self):
        """ValidationResult для неуспешной проверки."""
        from common.models import ValidationResult
        
        result = ValidationResult(
            passed=False,
            message="Превышен допуск",
            details={"difference": 1.5}
        )
        
        assert result.passed == False
