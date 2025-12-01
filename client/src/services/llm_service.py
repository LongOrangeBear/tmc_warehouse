"""Сервис для взаимодействия с LLM (OpenAI)."""
import logging
import base64
from pathlib import Path
from typing import Optional, Dict, Any
import json

import openai
from openai import OpenAI

from client.src.config import get_config

import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file


class LLMService:
    """Сервис для работы с LLM."""

    def __init__(self):
        config = get_config()
        self.provider = config.get("llm", {}).get("provider", "openai")
        # Prioritize environment variable, fallback to config
        self.api_key = os.getenv("OPENAI_API_KEY") or config.get("llm", {}).get("api_key", "")
        self.model = config.get("llm", {}).get("model", "gpt-4o-mini")
        
        # Enforce model restriction
        if self.model != "gpt-4o-mini":
            logger.warning(f"Configured model '{self.model}' is not 'gpt-4o-mini'. Enforcing 'gpt-4o-mini' as per project rules.")
            self.model = "gpt-4o-mini"
            
        self.base_url = config.get("llm", {}).get("base_url", "https://api.openai.com/v1")
        
        self.client: Optional[OpenAI] = None
        
        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                logger.info(f"LLM Service initialized with model {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
        else:
            logger.warning("LLM API key is missing. LLM features will be disabled.")

    def parse_ttn_text(self, text: str) -> Dict[str, Any]:
        """Парсинг текста ТТН с помощью LLM."""
        if not self.client:
            logger.warning("LLM client not initialized")
            return {}

        prompt = """
        Ты - эксперт по разбору документов ТТН (Товарно-транспортная накладная).
        Твоя задача - извлечь данные из текста ТТН и вернуть их в формате JSON.
        
        Структура JSON:
        {
            "ttn_number": "номер документа",
            "ttn_date": "YYYY-MM-DD",
            "supplier": "название поставщика",
            "items": [
                {
                    "article": "артикул",
                    "name": "наименование товара",
                    "quantity": 1.0,
                    "unit": "шт"
                }
            ]
        }
        
        Правила:
        1. Игнорируй метаданные (ИНН, КПП, адреса, банковские счета), если они не относятся к поставщику.
        2. Поставщик обычно указан как "Грузоотправитель" или "Поставщик".
        3. Товары находятся в табличной части.
        4. Если артикула нет, оставь пустую строку.
        5. Количество должно быть числом (float).
        6. Дату приведи к формату YYYY-MM-DD.
        
        Текст документа:
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts data from documents to JSON."},
                    {"role": "user", "content": prompt + "\n\n" + text}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            logger.info("LLM response received")
            logger.debug(f"LLM raw response: {content}")
            
            return json.loads(content)
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return {}

    def parse_ttn_image(self, image_path: Path) -> Dict[str, Any]:
        """Парсинг изображения ТТН с помощью Vision LLM."""
        if not self.client:
            logger.warning("LLM client not initialized")
            return {}

        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = """
            Проанализируй изображение ТТН и извлеки данные в JSON.
            Структура: ttn_number, ttn_date (YYYY-MM-DD), supplier, items (article, name, quantity, unit).
            Игнорируй рукописные пометки, если они не относятся к количеству.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            logger.info("LLM Vision response received")
            return json.loads(content)
        except Exception as e:
            logger.error(f"LLM Vision parsing failed: {e}")
            return {}
