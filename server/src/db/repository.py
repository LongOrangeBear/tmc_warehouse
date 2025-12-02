"""CRUD операции с базой данных."""
import json
from datetime import datetime
from typing import List, Optional

from peewee import fn

from server.src.db.models import database, Product, Reception, ReceptionItem
from common.models import (
    ProductCreate, ProductRead,
    ReceptionCreate, ReceptionRead, ReceptionShort, ReceptionItemRead,
    ReceptionStatus, ControlStatus, ControlType
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
            # Считаем товары, которые ещё не проверены (pending)
            pending_count = ReceptionItem.select().where(
                (ReceptionItem.reception == reception) &
                (ReceptionItem.control_status == ControlStatus.PENDING.value)
            ).count()
            
            # Если нет непроверенных товаров - приёмка завершена
            if pending_count == 0:
                # Проверяем, есть ли хотя бы один товар
                total_items = ReceptionItem.select().where(
                    ReceptionItem.reception == reception
                ).count()
                
                if total_items > 0:
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
            suspicious_fields=item.get_suspicious_fields_list(),
            control_type=ControlType(item.product.control_type) if item.product and item.product.control_type else None,
            control_params=item.product.get_control_params_dict() if item.product and item.product.control_params else None,
            photos=item.get_photos_list()
        )
