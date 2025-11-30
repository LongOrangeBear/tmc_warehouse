# tests/test_server_api.py
"""
Тесты REST API сервера.

Запуск:
    pytest tests/test_server_api.py -v
"""
import pytest


class TestHealthEndpoint:
    """Тесты эндпоинта /health."""
    
    def test_health_returns_ok(self, test_client):
        """Health endpoint возвращает статус ok."""
        response = test_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "time" in data
    
    def test_health_returns_datetime(self, test_client):
        """Health endpoint возвращает валидную дату."""
        response = test_client.get("/api/v1/health")
        data = response.json()
        
        # Проверить что time похоже на datetime
        assert "T" in data["time"] or "-" in data["time"]


class TestProductsEndpoint:
    """Тесты эндпоинта /products."""
    
    def test_get_products_returns_list(self, test_client):
        """GET /products возвращает список."""
        response = test_client.get("/api/v1/products")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_product_by_article_not_found(self, test_client):
        """GET /products/{article} возвращает 404 для несуществующего."""
        response = test_client.get("/api/v1/products/NONEXISTENT-12345")
        
        assert response.status_code == 404


class TestReceptionsEndpoint:
    """Тесты эндпоинта /receptions."""
    
    def test_create_reception(self, test_client, sample_reception_data):
        """POST /receptions создаёт приёмку."""
        response = test_client.post("/api/v1/receptions", json=sample_reception_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] > 0
        assert data["ttn_number"] == sample_reception_data["ttn_number"]
        assert data["status"] == "pending"
    
    def test_get_receptions_returns_list(self, test_client):
        """GET /receptions возвращает список."""
        response = test_client.get("/api/v1/receptions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_reception_not_found(self, test_client):
        """GET /receptions/{id} возвращает 404 для несуществующей."""
        response = test_client.get("/api/v1/receptions/99999")
        
        assert response.status_code == 404
