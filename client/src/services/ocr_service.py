"""OCR сервис для распознавания документов ТТН."""
import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from datetime import date, datetime

import cv2
import numpy as np
import pytesseract
import pdfplumber
from pdf2image import convert_from_path

from client.src.config import get_config
from common.models import OCRResult, OCRItem, ReceptionItemCreate
from client.src.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Паттерны для извлечения данных (Regex fallback)
PATTERNS = {
    "ttn_number": r"(?:ТТН|накладная|товарн\w*\s*накладн\w*)[^\d]*[№#]?\s*(\d[\d\-/]+)",
    "date": r"(\d{2})[./](\d{2})[./](\d{2,4})",
    "supplier": r"(?:поставщик|грузоотправитель|от(?:правитель)?)[:\s]+([А-Яа-яЁё\s\"\-]+(?:ООО|ИП|АО|ЗАО)?[А-Яа-яЁё\s\"\-]*)",
    "article": r"(?:арт(?:икул)?\.?|art\.?)[:\s]*([A-Za-zА-Яа-я0-9\-]+)",
    "quantity": r"(\d+(?:[.,]\d+)?)\s*(шт|кг|м|л|уп|ед)?\.?",
}

# Паттерны строк-мусора
SKIP_PATTERNS = [
    r'^\s*ИНН\s+\d+',
    r'^\s*КПП\s+\d+',
    r'к/с\s+\d{20}',
    r'р/с\s+\d{20}',
    r'^\d{6},\s*г\.',
    r'^\d{6}[,\s]+[А-Яа-я]',
    r'(?:Водитель|Лицензи|Регистрационн|Паспорт)',
    r'Срок\s+доставки',
    r'БИК\s+\d{9}',
    r'ОГРН\s+\d{13}',
    r'Адрес[:\s]+\d{6}',
    r'^[А-Яа-я]+\s+[А-Я]\.[А-Я]\.',
    r'Организация\s+ИНН',
    r'^\s*«[^»]+»\s*$',
]


class OCRService:
    """Сервис распознавания документов (Hybrid: PDF Text + LLM + Tesseract)."""

    def __init__(self):
        config = get_config()
        self.tesseract_path = config["tesseract"]["path"]
        self.languages = "+".join(config["tesseract"]["languages"])
        self.psm = config["tesseract"]["psm"]
        self.poppler_path = config["poppler"]["path"]
        
        # Инициализация LLM сервиса
        self.llm_service = LLMService()

        # Настройка pytesseract
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

    def process_document(self, file_path: Path) -> OCRResult:
        """Обработать документ."""
        logger.info(f"Processing document: {file_path}")
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return OCRResult()

        # Check supported extensions
        supported_exts = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        if file_path.suffix.lower() not in supported_exts:
            logger.warning(f"Unsupported file format: {file_path.suffix}")
            return OCRResult()

        # 1. Попытка извлечь текст из PDF (если это PDF)
        if file_path.suffix.lower() == ".pdf":
            text_content = self._extract_text_from_pdf(file_path)
            if text_content and len(text_content.strip()) > 50:
                logger.info("PDF text extracted successfully. Using LLM/Regex parsing.")
                return self._process_text_content(text_content)
            else:
                logger.info("PDF text extraction failed or empty. Falling back to Vision/OCR.")

        # 2. Если текст не извлечен или это картинка -> Vision / OCR
        return self._process_image_content(file_path)

    def _extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """Извлечь текст из PDF с помощью pdfplumber."""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return None

    def _process_text_content(self, text: str) -> OCRResult:
        """Обработка текстового контента (LLM или Regex)."""
        # Попытка использовать LLM
        if self.llm_service.client:
            logger.info("Using LLM for text parsing")
            llm_result = self.llm_service.parse_ttn_text(text)
            if llm_result:
                return self._convert_llm_result(llm_result)
            else:
                logger.warning("LLM parsing returned empty result. Falling back to Regex.")
        
        # Fallback to Regex
        logger.info("Using Regex for text parsing")
        return self._parse_ttn_regex(text)

    def _process_image_content(self, file_path: Path) -> OCRResult:
        """Обработка изображения (LLM Vision или Tesseract)."""
        # Попытка использовать LLM Vision
        if self.llm_service.client:
            logger.info("Using LLM Vision for image parsing")
            # Если PDF - берем первую страницу как картинку
            image_path = file_path
            temp_image = None
            
            if file_path.suffix.lower() == ".pdf":
                try:
                    images = convert_from_path(str(file_path), poppler_path=self.poppler_path, first_page=1, last_page=1)
                    if images:
                        temp_image = file_path.parent / f"temp_vision_{file_path.stem}.jpg"
                        images[0].save(temp_image, "JPEG")
                        image_path = temp_image
                except Exception as e:
                    logger.error(f"Failed to convert PDF for Vision: {e}")
            
            if image_path.exists():
                llm_result = self.llm_service.parse_ttn_image(image_path)
                
                # Cleanup temp image
                if temp_image and temp_image.exists():
                    temp_image.unlink()
                    
                if llm_result:
                    return self._convert_llm_result(llm_result)
            
            logger.warning("LLM Vision failed. Falling back to Tesseract.")

        # Fallback to Tesseract
        logger.info("Using Tesseract OCR")
        # Конвертация в изображения для Tesseract
        if file_path.suffix.lower() == ".pdf":
            images = self._pdf_to_images(file_path)
        else:
            images = [cv2.imread(str(file_path))]

        full_text = ""
        for img in images:
            processed = self._preprocess_image(img)
            text = self._extract_text_tesseract(processed)
            full_text += text + "\n"

        return self._parse_ttn_regex(full_text)

    def _convert_llm_result(self, data: Dict[str, Any]) -> OCRResult:
        """Конвертация ответа LLM в OCRResult."""
        result = OCRResult()
        
        result.ttn_number = data.get("ttn_number")
        
        date_str = data.get("ttn_date")
        if date_str:
            try:
                result.ttn_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Failed to parse date from LLM: {date_str}")

        result.supplier = data.get("supplier")
        
        items = []
        for item_data in data.get("items", []):
            item = OCRItem(
                raw_text=str(item_data),
                article=item_data.get("article"),
                name=item_data.get("name"),
                quantity=float(item_data.get("quantity", 0)),
                unit=item_data.get("unit")
            )
            # LLM usually gives high confidence
            item.field_confidence = {
                "article": 0.9,
                "name": 0.9,
                "quantity": 0.9,
                "unit": 0.9
            }
            items.append(item)
            
        result.items = items
        return result

    # --- Tesseract & Regex Methods (Legacy/Fallback) ---

    def _pdf_to_images(self, pdf_path: Path) -> List[np.ndarray]:
        try:
            pil_images = convert_from_path(str(pdf_path), poppler_path=self.poppler_path, dpi=300)
            return [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in pil_images]
        except Exception as e:
            logger.error(f"Failed to convert PDF: {e}")
            return []

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return cv2.medianBlur(binary, 3)

    def _extract_text_tesseract(self, image: np.ndarray) -> str:
        try:
            config = f"--psm {self.psm} --oem 3"
            return pytesseract.image_to_string(image, lang=self.languages, config=config)
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def _parse_ttn_regex(self, text: str) -> OCRResult:
        """Парсинг текста с помощью Regex (старая логика)."""
        result = OCRResult()
        
        # TTN
        match = re.search(PATTERNS["ttn_number"], text, re.IGNORECASE)
        if match:
            result.ttn_number = match.group(1).strip()

        # Date
        match = re.search(PATTERNS["date"], text)
        if match:
            day, month, year = match.groups()
            if len(year) == 2: year = "20" + year
            try:
                result.ttn_date = date(int(year), int(month), int(day))
            except ValueError: pass

        # Supplier
        match = re.search(PATTERNS["supplier"], text, re.IGNORECASE)
        if match:
            result.supplier = match.group(1).strip()
        else:
            # Fallback supplier
            alt_match = re.search(r'((?:ООО|ИП|АО|ЗАО)\s+[«"][^»"]+[»"])', text)
            if alt_match:
                result.supplier = alt_match.group(1).strip()

        # Items
        result.items = self._extract_items_regex(text)
        return result

    def _extract_items_regex(self, text: str) -> List[OCRItem]:
        items = []
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5: continue
            if self._is_metadata_line(line): continue

            item = OCRItem(raw_text=line)
            confidence = {}

            match = re.search(PATTERNS["article"], line, re.IGNORECASE)
            if match:
                item.article = match.group(1).strip()
                confidence["article"] = 0.7

            match = re.search(PATTERNS["quantity"], line)
            if match:
                try:
                    item.quantity = float(match.group(1).replace(",", "."))
                    confidence["quantity"] = 0.8
                except ValueError: pass
                if match.group(2):
                    item.unit = match.group(2)
                    confidence["unit"] = 0.9

            if item.article or item.quantity:
                item.name = line[:100]
                confidence["name"] = 0.5
                item.field_confidence = confidence
                if self._is_valid_item(item):
                    items.append(item)
        return items

    def _is_metadata_line(self, line: str) -> bool:
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in SKIP_PATTERNS)

    def _is_valid_item(self, item: OCRItem) -> bool:
        fields_present = sum([
            bool(item.article and len(item.article) > 0),
            bool(item.name and len(item.name) > 5),
            bool(item.quantity and item.quantity > 0)
        ])
        return fields_present >= 2

    def ocr_items_to_reception_items(self, ocr_items: List[OCRItem], confidence_threshold: float = 0.5) -> List[ReceptionItemCreate]:
        result = []
        for ocr_item in ocr_items:
            suspicious = []
            for field, conf in ocr_item.field_confidence.items():
                if conf < confidence_threshold:
                    suspicious.append(field)

            item = ReceptionItemCreate(
                article=ocr_item.article or "",
                name=ocr_item.name or ocr_item.raw_text[:100],
                quantity=ocr_item.quantity or 0,
                unit=ocr_item.unit or "шт",
                suspicious_fields=suspicious
            )
            result.append(item)
        return result
