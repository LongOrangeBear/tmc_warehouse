#!/usr/bin/env python3
"""
Скрипт для сравнения парсинга ТТН через OpenAI API и ChatBotHub API
"""

import json
import time
import base64
import requests
from pathlib import Path
from typing import Dict, Any, Optional

# ==================== КОНФИГУРАЦИЯ ====================

# OpenAI API (текущий способ)
OPENAI_CONFIG = {
    "api_key": "",  # ← Будет загружен из .env или config.json
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini"
}

# ChatBotHub API (новый способ)
CHATBOTHUB_CONFIG = {
    "base_url": "https://chatbothub.ru/api/v1",
    "schema_name": "ttn/parser",
    "bot_name": "ttn-parser",
    "model": "gpt-4o-mini",
    "guest_id": "tmc_warehouse_test_client"
}

# Промпт для OpenAI (идентичен текущему)
OPENAI_PROMPT = """Ты - эксперт по разбору документов ТТН (Товарно-транспортная накладная).
Твоя задача - извлечь данные из текста ТТН и вернуть их в формате JSON.

Структура JSON:
{{
    "ttn_number": "номер документа",
    "ttn_date": "YYYY-MM-DD",
    "supplier": "название поставщика",
    "items": [
        {{
            "article": "артикул",
            "name": "наименование товара",
            "quantity": 1.0,
            "unit": "шт"
        }}
    ]
}}

Правила:
1. Игнорируй метаданные (ИНН, КПП, адреса, банковские счета), если они не относятся к поставщику.
2. Поставщик обычно указан как "Грузоотправитель" или "Поставщик".
3. Товары находятся в табличной части.
4. Если артикула нет, оставь пустую строку "".
5. Количество должно быть числом (float).
6. Дату приведи к формату YYYY-MM-DD.
7. Игнорируй рукописные пометки, если они не относятся к количеству.

Текст документа:
{text}"""

# ==================== ТЕСТОВЫЕ ДАННЫЕ ====================

SAMPLE_TTN_TEXT = """
ТОВАРНО-ТРАНСПОРТНАЯ НАКЛАДНАЯ №12345
Дата: 02.12.2025

Грузоотправитель: ООО "Поставщик Тестовый"
ИНН: 1234567890
КПП: 123456789

Грузополучатель: ООО "Получатель"

ТОВАРНАЯ ЧАСТЬ:
┌─────────┬────────────────────────────┬────────────┬────────┐
│ Артикул │ Наименование              │ Количество │ Ед.изм │
├─────────┼────────────────────────────┼────────────┼────────┤
│ A001    │ Товар первый              │ 10.0       │ шт     │
│ A002    │ Товар второй              │ 5.5        │ кг     │
│         │ Товар без артикула        │ 3.0        │ шт     │
└─────────┴────────────────────────────┴────────────┴────────┘

Итого: 3 позиции
"""

# ==================== ЗАГРУЗКА КОНФИГУРАЦИИ ====================

def load_openai_config():
    """Загрузка конфигурации OpenAI из config.json или .env"""
    import os
    
    # Попытка загрузить из .env вручную (если нет dotenv)
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key == 'OPENAI_API_KEY':
                        os.environ['OPENAI_API_KEY'] = value
    
    # Попытка загрузить из переменных окружения
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        # Попытка загрузить из config.json
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    api_key = config.get("llm", {}).get("api_key", "")
        except Exception as e:
            print(f"⚠️  Не удалось загрузить config.json: {e}")
    
    OPENAI_CONFIG["api_key"] = api_key
    return bool(api_key)

# ==================== ФУНКЦИИ ПАРСИНГА ====================

def parse_ttn_via_openai(text: str) -> Dict[str, Any]:
    """
    Парсинг ТТН через OpenAI API (текущий способ)
    """
    print("🔄 Парсинг через OpenAI API...")
    
    if not OPENAI_CONFIG["api_key"]:
        return {
            "success": False,
            "error": "OpenAI API key not configured",
            "error_type": "ConfigError"
        }
    
    try:
        response = requests.post(
            f"{OPENAI_CONFIG['base_url']}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_CONFIG['api_key']}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENAI_CONFIG['model'],
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts data from documents to JSON."
                    },
                    {
                        "role": "user",
                        "content": OPENAI_PROMPT.format(text=text)
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            },
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        content = data['choices'][0]['message']['content']
        result = json.loads(content)
        
        return {
            "success": True,
            "data": result,
            "tokens": data.get('usage', {}),
            "raw_response": data
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


def parse_ttn_via_chatbothub(text: str) -> Dict[str, Any]:
    """
    Парсинг ТТН через ChatBotHub API (новый способ)
    """
    print("🔄 Парсинг через ChatBotHub API...")
    
    try:
        response = requests.post(
            f"{CHATBOTHUB_CONFIG['base_url']}/guest/llm/generate_structured",
            headers={
                "Content-Type": "application/json",
                "X-Guest-ID": CHATBOTHUB_CONFIG['guest_id']
            },
            json={
                "schema_name": CHATBOTHUB_CONFIG['schema_name'],
                "user_input": text,
                "bot_name": CHATBOTHUB_CONFIG['bot_name'],
                "temperature": 0.1,
                "model": CHATBOTHUB_CONFIG['model']
            },
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": data.get("status") == "success",
            "data": data.get("data", {}).get("result", {}),
            "tokens": data.get("data", {}).get("tokens_used", 0),
            "guest_id": data.get("data", {}).get("guest_id"),
            "raw_response": data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


def parse_ttn_image_via_openai(image_path: str) -> Dict[str, Any]:
    """
    Парсинг изображения ТТН через OpenAI Vision API
    """
    print(f"🔄 Парсинг изображения через OpenAI Vision API: {image_path}")
    
    if not OPENAI_CONFIG["api_key"]:
        return {
            "success": False,
            "error": "OpenAI API key not configured",
            "error_type": "ConfigError"
        }
    
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        response = requests.post(
            f"{OPENAI_CONFIG['base_url']}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_CONFIG['api_key']}",
                "Content-Type": "application/json"
            },
            json={
                "model": OPENAI_CONFIG['model'],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Проанализируй изображение ТТН и извлеки данные в JSON.\nСтруктура: ttn_number, ttn_date (YYYY-MM-DD), supplier, items (article, name, quantity, unit).\nИгнорируй рукописные пометки, если они не относятся к количеству.\nВерни ТОЛЬКО валидный JSON."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "response_format": {"type": "json_object"},
                "max_tokens": 2000
            },
            timeout=60
        )
        
        response.raise_for_status()
        data = response.json()
        
        content = data['choices'][0]['message']['content']
        result = json.loads(content)
        
        return {
            "success": True,
            "data": result,
            "tokens": data.get('usage', {}),
            "raw_response": data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


def parse_ttn_image_via_chatbothub(image_path: str) -> Dict[str, Any]:
    """
    Парсинг изображения ТТН через ChatBotHub API
    """
    print(f"🔄 Парсинг изображения через ChatBotHub API: {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        image_uri = f"data:{mime_type};base64,{image_data}"
        
        response = requests.post(
            f"{CHATBOTHUB_CONFIG['base_url']}/guest/llm/generate_structured",
            headers={
                "Content-Type": "application/json",
                "X-Guest-ID": CHATBOTHUB_CONFIG['guest_id']
            },
            json={
                "schema_name": CHATBOTHUB_CONFIG['schema_name'],
                "user_input": image_uri,
                "bot_name": CHATBOTHUB_CONFIG['bot_name'],
                "temperature": 0.1,
                "model": CHATBOTHUB_CONFIG['model']
            },
            timeout=60
        )
        
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": data.get("status") == "success",
            "data": data.get("data", {}).get("result", {}),
            "tokens": data.get("data", {}).get("tokens_used", 0),
            "guest_id": data.get("data", {}).get("guest_id"),
            "raw_response": data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


# ==================== СРАВНЕНИЕ РЕЗУЛЬТАТОВ ====================

def compare_results(openai_result: Dict, chatbothub_result: Dict) -> Dict[str, Any]:
    """
    Сравнение результатов парсинга
    """
    comparison = {
        "both_success": openai_result['success'] and chatbothub_result['success'],
        "openai_success": openai_result['success'],
        "chatbothub_success": chatbothub_result['success'],
        "data_match": False,
        "differences": []
    }
    
    if comparison['both_success']:
        openai_data = openai_result['data']
        chatbothub_data = chatbothub_result['data']
        
        for field in ['ttn_number', 'ttn_date', 'supplier']:
            if openai_data.get(field) != chatbothub_data.get(field):
                comparison['differences'].append({
                    "field": field,
                    "openai": openai_data.get(field),
                    "chatbothub": chatbothub_data.get(field)
                })
        
        openai_items = openai_data.get('items', [])
        chatbothub_items = chatbothub_data.get('items', [])
        
        if len(openai_items) != len(chatbothub_items):
            comparison['differences'].append({
                "field": "items_count",
                "openai": len(openai_items),
                "chatbothub": len(chatbothub_items)
            })
        
        comparison['data_match'] = len(comparison['differences']) == 0
    
    return comparison


def print_result(title: str, result: Dict[str, Any]):
    """
    Красивый вывод результата
    """
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)
    
    if result['success']:
        print("✅ Успех")
        print(f"\n📄 Результат:")
        print(json.dumps(result['data'], indent=2, ensure_ascii=False))
        print(f"\n🔢 Токены: {result.get('tokens', 'N/A')}")
    else:
        print("❌ Ошибка")
        print(f"Тип: {result.get('error_type', 'Unknown')}")
        print(f"Сообщение: {result.get('error', 'Unknown error')}")
        if 'traceback' in result:
            print(f"\nTraceback:\n{result['traceback']}")


def print_comparison(comparison: Dict[str, Any]):
    """
    Вывод результатов сравнения
    """
    print(f"\n{'='*60}")
    print("  📊 СРАВНЕНИЕ РЕЗУЛЬТАТОВ")
    print('='*60)
    
    if comparison['both_success']:
        if comparison['data_match']:
            print("✅ Результаты идентичны!")
        else:
            print("⚠️  Обнаружены различия:")
            for diff in comparison['differences']:
                print(f"\n  Поле: {diff['field']}")
                print(f"    OpenAI:     {diff['openai']}")
                print(f"    ChatBotHub: {diff['chatbothub']}")
    else:
        print("❌ Не удалось сравнить (один из запросов завершился с ошибкой)")
        print(f"   OpenAI: {'✅' if comparison['openai_success'] else '❌'}")
        print(f"   ChatBotHub: {'✅' if comparison['chatbothub_success'] else '❌'}")


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

def main():
    """
    Основная функция для запуска тестов
    """
    print("🚀 ТЕСТИРОВАНИЕ ПАРСЕРА ТТН")
    print("Сравнение OpenAI API vs ChatBotHub API\n")
    
    # Загрузка конфигурации
    has_openai_key = load_openai_config()
    
    if not has_openai_key:
        print("⚠️  OpenAI API ключ не настроен.")
        print("   Для полного сравнения добавьте ключ в .env или config.json\n")
    
    # ===== ТЕСТ 1: Парсинг текста =====
    print("\n" + "="*60)
    print("  ТЕСТ 1: Парсинг текста ТТН")
    print("="*60)
    
    start_time = time.time()
    openai_result = parse_ttn_via_openai(SAMPLE_TTN_TEXT)
    openai_time = time.time() - start_time
    
    start_time = time.time()
    chatbothub_result = parse_ttn_via_chatbothub(SAMPLE_TTN_TEXT)
    chatbothub_time = time.time() - start_time
    
    print_result("OpenAI API", openai_result)
    print(f"⏱️  Время: {openai_time:.2f}s")
    
    print_result("ChatBotHub API", chatbothub_result)
    print(f"⏱️  Время: {chatbothub_time:.2f}s")
    
    comparison = compare_results(openai_result, chatbothub_result)
    print_comparison(comparison)
    
    # ===== ТЕСТ 2: Парсинг изображения (если файл существует) =====
    test_image_path = Path(__file__).parent / "test_ttn_image.jpg"
    
    if test_image_path.exists():
        print("\n" + "="*60)
        print("  ТЕСТ 2: Парсинг изображения ТТН")
        print("="*60)
        
        start_time = time.time()
        openai_img_result = parse_ttn_image_via_openai(str(test_image_path))
        openai_img_time = time.time() - start_time
        
        start_time = time.time()
        chatbothub_img_result = parse_ttn_image_via_chatbothub(str(test_image_path))
        chatbothub_img_time = time.time() - start_time
        
        print_result("OpenAI Vision API", openai_img_result)
        print(f"⏱️  Время: {openai_img_time:.2f}s")
        
        print_result("ChatBotHub API", chatbothub_img_result)
        print(f"⏱️  Время: {chatbothub_img_time:.2f}s")
        
        img_comparison = compare_results(openai_img_result, chatbothub_img_result)
        print_comparison(img_comparison)
    else:
        print(f"\n⚠️  Пропущен ТЕСТ 2: файл '{test_image_path}' не найден")
        print("   Для тестирования изображений добавьте файл test_ttn_image.jpg в tests/manual/")
    
    # ===== ИТОГОВАЯ СТАТИСТИКА =====
    print("\n" + "="*60)
    print("  📈 ИТОГОВАЯ СТАТИСТИКА")
    print("="*60)
    
    if openai_result['success']:
        print(f"OpenAI время (текст): {openai_time:.2f}s")
    else:
        print(f"OpenAI время (текст): {openai_time:.2f}s (ОШИБКА)")
    
    print(f"ChatBotHub время (текст): {chatbothub_time:.2f}s")
    
    if openai_result['success'] and chatbothub_result['success']:
        print(f"Разница во времени: {abs(openai_time - chatbothub_time):.2f}s")
        print(f"\nРезультаты совпадают: {'✅ Да' if comparison.get('data_match') else '⚠️  Нет'}")
    
    print("\n" + "="*60)
    print("  ✅ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("="*60)


if __name__ == "__main__":
    main()
