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
        raise HTTPException(status_code=404, detail="Product not found")
    return product
