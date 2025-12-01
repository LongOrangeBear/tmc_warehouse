import sys
import os
import logging
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from server.src.db.models import database, Product
from common.models import ControlType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("SEED_DB")

def seed_database():
    logger.info("🌱 Seeding database with test products...")
    
    # Ensure tables exist
    database.connect()
    database.create_tables([Product], safe=True)
    
    products = [
        # TTN_1_A_654.pdf (Electronics)
        {
            "article": "512",
            "name": "Ноутбук ASUS VivoBook",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_scratches": "Проверить корпус на царапины и вмятины",
                "check_power_on": "Включить и проверить загрузку BIOS",
                "check_screen": "Проверить экран на битые пиксели",
                "check_keyboard": "Проверить работу клавиатуры",
                "instructions": "1. Осмотреть упаковку на повреждения\n2. Проверить комплектность (ноутбук, зарядка, документы)\n3. Включить и убедиться в загрузке\n4. Проверить отсутствие механических повреждений"
            }
        },
        {
            "article": "513",
            "name": "Монитор Samsung 27\"",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_screen_crack": "Проверить экран на трещины и сколы",
                "check_dead_pixels": "Включить и проверить на битые пиксели",
                "check_stand": "Проверить целостность подставки",
                "instructions": "1. Осмотреть упаковку\n2. Проверить экран на трещины\n3. Включить и проверить изображение\n4. Проверить все разъемы"
            }
        },
        {
            "article": "514",
            "name": "Клавиатура Logitech K120",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_package": "Проверить целостность упаковки",
                "check_cable": "Проверить кабель на повреждения",
                "instructions": "1. Проверить упаковку\n2. Осмотреть корпус\n3. Проверить кабель USB"
            }
        },
        {
            "article": "515",
            "name": "Мышь беспроводная A4Tech",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_batteries": "Проверить наличие батареек",
                "check_receiver": "Проверить наличие USB-приемника",
                "instructions": "1. Проверить комплектность\n2. Осмотреть на повреждения\n3. Убедиться в наличии приемника"
            }
        },
        {
            "article": "516",
            "name": "Кабель HDMI 2м",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_connectors": "Проверить разъемы на повреждения",
                "check_cable": "Проверить целостность кабеля",
                "instructions": "1. Осмотреть разъемы\n2. Проверить отсутствие перегибов\n3. Проверить длину (должно быть 2м)"
            }
        },
        
        # TTN_2_Б_1287.pdf (Construction)
        {
            "article": "CEM-500",
            "name": "Цемент М500",
            "unit": "мешок",
            "requires_control": True,
            "control_type": ControlType.WEIGHT_CHECK,
            "control_params": {
                "min_weight": 49.5,
                "max_weight": 50.5,
                "check_packaging": "Проверить целостность мешка",
                "instructions": "1. Взвесить мешок (допуск 49.5-50.5 кг)\n2. Проверить отсутствие разрывов\n3. Проверить срок годности\n4. Проверить маркировку М500"
            }
        },
        {
            "article": "BRICK-150",
            "name": "Кирпич красный М150",
            "unit": "паллета",
            "requires_control": True,
            "control_type": ControlType.QUANTITY_CHECK,
            "control_params": {
                "count_per_pallet": 200,
                "check_quality": "Проверить на сколы и трещины (выборочно 10 шт)",
                "instructions": "1. Пересчитать количество на паллете (должно быть 200 шт)\n2. Визуально осмотреть 10 случайных кирпичей\n3. Проверить отсутствие крупных сколов\n4. Проверить брак (не более 5%)"
            }
        },
        {
            "article": "ARM-500",
            "name": "Арматура А500С d12мм",
            "unit": "тонна",
            "requires_control": True,
            "control_type": ControlType.WEIGHT_CHECK,
            "control_params": {
                "min_weight": 995,
                "max_weight": 1005,
                "check_diameter": "Штангенциркулем проверить диаметр (12мм ±0.3мм)",
                "check_rust": "Проверить отсутствие ржавчины",
                "instructions": "1. Взвесить партию (995-1005 кг)\n2. Проверить диаметр штангенциркулем\n3. Осмотреть на коррозию\n4. Проверить сертификат качества"
            }
        },
        
        # TTN_3_В_4521.pdf (Food)
        {
            "article": "MILK-32",
            "name": "Молоко «Простоквашино» 3.2% 1л",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_expiration": "Срок годности не менее 5 дней",
                "check_leakage": "Проверить герметичность упаковки",
                "check_temperature": "Температура хранения +2...+6°C",
                "instructions": "1. Проверить срок годности\n2. Осмотреть упаковку на протечки\n3. Проверить целостность крышки\n4. Убедиться в отсутствии вздутия"
            }
        },
        {
            "article": "SMET-20",
            "name": "Сметана «Домик в деревне» 20%",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_expiration": "Срок годности не менее 3 дней",
                "check_packaging": "Проверить герметичность стаканчика",
                "check_temperature": "Температура +2...+6°C",
                "instructions": "1. Проверить дату изготовления\n2. Осмотреть упаковку\n3. Проверить фольгу на целостность\n4. Убедиться в правильной температуре хранения"
            }
        },
        {
            "article": "CHEESE-50",
            "name": "Сыр «Российский» 50%",
            "unit": "кг",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_mold": "Проверить отсутствие плесени",
                "check_packaging": "Вакуумная упаковка должна быть герметична",
                "check_expiration": "Срок годности не менее 7 дней",
                "instructions": "1. Проверить срок годности\n2. Осмотреть на плесень\n3. Проверить вакуумную упаковку\n4. Взвесить (допуск ±50г)"
            }
        },
        {
            "article": "BUTTER-V",
            "name": "Масло сливочное «Вологодское»",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_expiration": "Срок годности не менее 10 дней",
                "check_packaging": "Проверить фольгу на целостность",
                "check_temperature": "Хранить при -3...+6°C",
                "instructions": "1. Проверить дату производства\n2. Осмотреть фольгу на разрывы\n3. Проверить ГОСТ\n4. Убедиться в правильной температуре"
            }
        },
        {
            "article": "YOGURT-D",
            "name": "Йогурт «Danone» ассорти 125г",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_expiration": "Срок годности не менее 5 дней",
                "check_seal": "Проверить фольгу на герметичность",
                "check_swelling": "Проверить отсутствие вздутия",
                "instructions": "1. Проверить срок годности\n2. Осмотреть фольгу\n3. Проверить отсутствие вздутия стаканчика\n4. Температура хранения +2...+6°C"
            }
        },
        {
            "article": "TVOROG-9",
            "name": "Творог «Савушкин» 9% 200г",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_expiration": "Срок годности не менее 3 дней",
                "check_packaging": "Герметичность упаковки",
                "instructions": "1. Проверить дату производства\n2. Осмотреть упаковку на целостность\n3. Проверить температуру хранения\n4. Убедиться в отсутствии вздутия"
            }
        },
        {
            "article": "KEFIR-1",
            "name": "Кефир «Био Баланс» 1% 1л",
            "unit": "шт",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {
                "check_expiration": "Срок годности не менее 3 дней",
                "check_leakage": "Проверить на протечки",
                "check_bottle": "Проверить целостность бутылки и крышки",
                "instructions": "1. Проверить срок годности\n2. Осмотреть бутылку на трещины\n3. Проверить крышку на герметичность\n4. Убедиться в отсутствии вздутия"
            }
        },
        
        # img.png (Generic)
        {
            "article": "1",
            "name": "Компьютеры",
            "unit": "шт.",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {"check_completeness": True}
        },
        {
            "article": "2",
            "name": "Телефоны",
            "unit": "шт.",
            "requires_control": True,
            "control_type": ControlType.VISUAL_CHECK,
            "control_params": {"check_screen": True}
        }
    ]
    
    count = 0
    for p_data in products:
        try:
            # Check if exists
            existing = Product.get_or_none(Product.article == p_data["article"])
            if existing:
                # Update
                query = Product.update(
                    name=p_data["name"],
                    unit=p_data["unit"],
                    requires_control=p_data["requires_control"],
                    control_type=p_data.get("control_type"),
                    control_params=json.dumps(p_data.get("control_params")) if p_data.get("control_params") else None
                ).where(Product.id == existing.id)
                query.execute()
                logger.info(f"Updated: {p_data['article']} - {p_data['name']}")
            else:
                # Create
                Product.create(
                    article=p_data["article"],
                    name=p_data["name"],
                    unit=p_data["unit"],
                    requires_control=p_data["requires_control"],
                    control_type=p_data.get("control_type"),
                    control_params=json.dumps(p_data.get("control_params")) if p_data.get("control_params") else None
                )
                logger.info(f"Created: {p_data['article']} - {p_data['name']}")
                count += 1
        except Exception as e:
            logger.error(f"Error processing {p_data['article']}: {e}")
            
    logger.info(f"✅ Seeding complete. Added {count} new products.")
    database.close()

if __name__ == "__main__":
    seed_database()
