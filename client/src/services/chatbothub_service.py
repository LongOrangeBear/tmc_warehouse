"""Сервис для взаимодействия с ChatBotHub API."""
import logging
import base64
from pathlib import Path
from typing import Dict, Any
import json

import requests

from client.src.config import get_config

logger = logging.getLogger(__name__)


class ChatBotHubService:
    """Сервис для работы с ChatBotHub API."""

    def __init__(self):
        config = get_config()
        chatbothub_config = config.get("chatbothub", {})
        
        self.base_url = chatbothub_config.get("base_url", "https://localhost:8443/api/v1")
        self.schema_name = chatbothub_config.get("schema_name", "ttn/parser")
        self.bot_name = chatbothub_config.get("bot_name", "ttn-parser")
        self.guest_id = chatbothub_config.get("guest_id", "tmc_warehouse_client")
        self.model = chatbothub_config.get("model", "gpt-4o-mini")
        self.verify_ssl = chatbothub_config.get("verify_ssl", False)
        
        logger.info(f"ChatBotHub Service initialized with base_url: {self.base_url}")

    def parse_ttn_text(self, text: str) -> Dict[str, Any]:
        """
        Парсинг текста ТТН с помощью ChatBotHub API.
        
        Args:
            text: Текст ТТН документа
            
        Returns:
            Словарь с распарсенными данными в формате:
            {
                "ttn_number": str,
                "ttn_date": str (YYYY-MM-DD),
                "supplier": str,
                "items": [
                    {
                        "article": str,
                        "name": str,
                        "quantity": float,
                        "unit": str
                    }
                ]
            }
        """
        logger.info("Parsing TTN text via ChatBotHub API")
        
        try:
            response = requests.post(
                f"{self.base_url}/guest/llm/generate_structured",
                headers={
                    "Content-Type": "application/json",
                    "X-Guest-ID": self.guest_id
                },
                json={
                    "schema_name": self.schema_name,
                    "user_input": text,
                    "bot_name": self.bot_name,
                    "temperature": 0.1,
                    "model": self.model
                },
                timeout=30,
                verify=self.verify_ssl
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "error":
                logger.error(f"ChatBotHub API error: {data.get('message')}")
                return {}
            
            result_data = data.get("data", {})
            result = result_data.get("result", {})
            
            logger.info("ChatBotHub text parsing successful")
            logger.debug(f"Result: {result}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ChatBotHub API request failed: {e}")
            return {}
        except Exception as e:
            logger.error(f"ChatBotHub text parsing failed: {e}")
            return {}

    def parse_ttn_image(self, image_path: Path) -> Dict[str, Any]:
        """
        Парсинг изображения ТТН с помощью ChatBotHub Vision API.
        
        Args:
            image_path: Путь к файлу изображения
            
        Returns:
            Словарь с распарсенными данными (см. parse_ttn_text)
        """
        logger.info(f"Parsing TTN image via ChatBotHub Vision API: {image_path}")
        
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            ext = image_path.suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            
            image_uri = f"data:{mime_type};base64,{base64_image}"
            
            response = requests.post(
                f"{self.base_url}/guest/llm/generate_structured_vision",
                headers={
                    "Content-Type": "application/json",
                    "X-Guest-ID": self.guest_id
                },
                json={
                    "schema_name": self.schema_name,
                    "user_input": image_uri,
                    "bot_name": self.bot_name,
                    "temperature": 0.1,
                    "model": self.model
                },
                timeout=60,
                verify=self.verify_ssl
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "error":
                logger.error(f"ChatBotHub Vision API error: {data.get('message')}")
                return {}
            
            result_data = data.get("data", {})
            result = result_data.get("result", {})
            
            logger.info("ChatBotHub Vision parsing successful")
            logger.debug(f"Result: {result}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"ChatBotHub Vision API request failed: {e}")
            return {}
        except Exception as e:
            logger.error(f"ChatBotHub Vision parsing failed: {e}")
            return {}
