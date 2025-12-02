# API спецификация (сервер FastAPI)

Базовый URL: `http://{host}:{port}/api/v1`

Все ответы в случае ошибок отдают модель `APIError`:

```json
{
  "detail": "Сообщение об ошибке",
  "code": "optional_error_code"
}
```

## 1. Health

### 1.1. GET /health

Назначение: проверить работоспособность сервера.

Запрос: без тела.

Ответ 200:

```json
{
  "status": "ok",
  "time": "2025-01-01T12:34:56.789123"
}
```

Модель: `HealthResponse`.

---

## 2. Товары (справочник)

### 2.1. GET /products

Назначение: получить список товаров.

Параметры запроса (query):

- `limit: int` (опционально, по умолчанию 100)
- `offset: int` (опционально, по умолчанию 0)

Ответ 200:

```json
[
  {
    "id": 1,
    "article": "BOLT-M10",
    "name": "Болт М10",
    "unit": "шт",
    "requires_control": true,
    "control_type": "weight_check",
    "control_params": {
      "target_weight": 2.0,
      "tolerance": 0.1
    },
    "created_at": "2025-01-01T12:00:00"
  }
]
```

---

### 2.2. GET /products/{article}

Назначение: получить товар по артикулу.

Путь: `{article}` — строка.

Ответ 200: объект товара `ProductRead`.

Ответ 404:

```json
{
  "detail": "Product not found",
  "code": "product_not_found"
}
```

---

## 3. Приёмки ТМЦ

### 3.1. POST /receptions

Назначение: создать приёмку на основе данных, полученных после OCR и ручной правки на клиенте.

Тело запроса: `ReceptionCreate`

Пример:

```json
{
  "ttn_number": "ТТН-123",
  "ttn_date": "2025-01-10",
  "supplier": "ООО Ромашка",
  "items": [
    {
      "article": "BOLT-M10",
      "name": "Болт М10",
      "quantity": 100,
      "unit": "шт",
      "control_required": true,
      "control_status": null,
      "control_result": null,
      "notes": null,
      "suspicious_fields": ["article"]
    }
  ],
  "ocr_engine": "tesseract-5.3.0-rus"
}
```

Ответ 201: `ReceptionRead`.

---

### 3.2. GET /receptions

Назначение: получить список приёмок (для истории).

Параметры (query):

- `status: ReceptionStatus` (опционально)
- `limit: int` (опционально)
- `offset: int` (опционально)

Ответ 200: список `ReceptionShort`.

---

### 3.3. GET /receptions/{id}

Назначение: получить полную информацию по приёмке.

Путь: `{id}` — integer.

Ответ 200: `ReceptionRead`.

Ответ 404: `APIError`.

---

### 3.4. POST /receptions/{id}/document

Назначение: загрузить исходный документ ТТН (PDF/изображение).

Путь: `{id}` — integer.

Тип: `multipart/form-data`.

Поля формы:

- `file` — бинарный файл.

Ответ 200:

```json
{
  "id": 1,
  "document_path": "receipts/2025-01-10_0001/document.pdf"
}
```

---

### 3.5. POST /receptions/{id}/video

Назначение: загрузить видеофайл входного контроля.

Путь: `{id}` — integer.

Тип: `multipart/form-data`.

Поля формы:

- `file` — бинарный файл (AVI, MJPG).

Ответ 200:

```json
{
  "id": 1,
  "video_path": "receipts/2025-01-10_0001/video.avi"
}
```

---

### 3.6. POST /receptions/{id}/control-results

Назначение: записать результаты контроля по позициям и завершить приёмку.

Путь: `{id}` — integer.

Тело запроса:

```json
{
  "items": [
    {
      "id": 10,
      "control_status": "passed",
      "control_result": {
        "passed": true,
        "message": "Вес в норме",
        "details": {
          "target_weight": 2.0,
          "tolerance": 0.1,
          "measured_weight": 1.98
        }
      },
      "notes": "Ок"
    }
  ]
}
```

Ответ 200: обновлённая `ReceptionRead`.

Ответ 404: если приёмка не найдена.

---

## 4. Скачивание файлов

### 4.1. GET /receptions/{id}/document

Назначение: скачать документ ТТН (PDF/изображение).

Путь: `{id}` — integer.

Ответ 200: файл документа (PDF, PNG, JPG).

Headers:
```
Content-Type: application/pdf | image/png | image/jpeg
Content-Disposition: attachment; filename="reception_{id}_document.{ext}"
```

Ответ 404: `APIError` - приёмка не найдена или документ отсутствует.

---

### 4.2. GET /receptions/{id}/video

Назначение: скачать видео входного контроля.

Путь: `{id}` — integer.

Ответ 200: файл видео (AVI, MP4).

Headers:
```
Content-Type: video/x-msvideo | video/mp4 | video/quicktime  
Content-Disposition: attachment; filename="reception_{id}_video.{ext}"
```

Ответ 404: `APIError` - приёмка не найдена или видео отсутствует.

---

### 4.3. GET /receptions/{id}/items/{item_id}/photos

Назначение: скачать все фотографии товара в виде ZIP архива.

Путь:
- `{id}` — reception_id (integer)
- `{item_id}` — item_id (integer)

Ответ 200: ZIP архив с фотографиями.

Headers:
```
Content-Type: application/zip
Content-Disposition: attachment; filename="item_{item_id}_photos.zip"
```

Структура архива:
```
photo_1.jpg
photo_2.jpg
photo_3.jpg
...
```

Ответ 404: `APIError` - товар не найден или фото отсутствуют.

---

### 4.4. GET /receptions/{id}/items/{item_id}/photos/{photo_index}

Назначение: скачать конкретную фотографию товара по индексу.

Путь:
- `{id}` — reception_id (integer)
- `{item_id}` — item_id (integer)
- `{photo_index}` — индекс фото (integer, начиная с 0)

Ответ 200: изображение (JPG, PNG).

Headers:
```
Content-Type: image/jpeg | image/png
Content-Disposition: attachment; filename="item_{item_id}_photo_{index+1}.{ext}"
```

Ответ 404: `APIError` - товар не найден, фото отсутствуют, или индекс вне диапазона.

