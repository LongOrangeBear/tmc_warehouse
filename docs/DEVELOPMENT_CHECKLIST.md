# ✅ ЧЕКЛИСТ ГОТОВНОСТИ К РАЗРАБОТКЕ
## TMC Warehouse System

---

## 📋 1. ПРОГРАММНОЕ ОБЕСПЕЧЕНИЕ НА WINDOWS

### Обязательное ПО

| # | Компонент | Статус | Как проверить |
|---|-----------|--------|---------------|
| 1 | Python 3.12 | ⬜ | `python --version` |
| 2 | pip | ⬜ | `pip --version` |
| 3 | Tesseract OCR 5.x | ⬜ | `tesseract --version` |
| 4 | Tesseract rus.traineddata | ⬜ | Проверить папку tessdata |
| 5 | Poppler (pdftoppm) | ⬜ | `pdftoppm -v` |

### Ссылки для скачивания

```
Python 3.12:
https://www.python.org/downloads/release/python-3120/

Tesseract OCR (Windows installer):
https://github.com/UB-Mannheim/tesseract/wiki
→ Выбрать "tesseract-ocr-w64-setup-5.x.x.exe"
→ При установке отметить "Russian" в языках

Poppler for Windows:
https://github.com/oswindows/poppler-windows/releases
→ Скачать последний Release-xx.xx.x.zip
→ Распаковать в C:\poppler
```

---

## 📁 2. ФАЙЛЫ ПРОЕКТА

### Структура (текущая)
```
tmc_warehouse/
├── common/
│   ├── __init__.py          ✅ есть
│   └── models.py            ✅ есть
├── config/
│   └── config.json          ✅ есть
├── docs/
│   ├── API.md               ✅ есть
│   ├── ARCHITECTURE.md      ✅ есть
│   ├── INSTALL.md           ✅ есть
│   └── USER_GUIDE.md        ✅ есть
├── server/
│   └── src/
│       ├── __init__.py      ✅ есть
│       ├── main_server.py   ✅ есть
│       ├── config.py        ✅ есть
│       ├── db/
│       │   ├── __init__.py  ✅ есть
│       │   ├── models.py    ✅ есть
│       │   ├── migrations.py✅ есть
│       │   └── repository.py✅ есть
│       └── api/
│           ├── __init__.py  ✅ есть
│           ├── routes_*.py  ✅ есть
├── client/
│   └── src/
│       ├── __init__.py      ✅ есть
│       ├── main_client.py   ✅ есть
│       ├── config.py        ✅ есть
│       ├── services/
│       │   ├── __init__.py  ✅ есть
│       │   ├── ocr_service.py ✅ есть
│       │   ├── camera_service.py ✅ есть
│       │   ├── sync_service.py ✅ есть
│       │   └── storage_service.py ✅ есть
│       └── ui/
│           ├── __init__.py  ✅ есть
│           ├── main_window.py ✅ есть
│           ├── document_dialog.py ✅ есть
│           ├── results_widget.py ✅ есть
│           ├── video_widget.py ✅ есть
│           └── database_dialog.py ✅ есть
├── data/                    ✅ создано
├── tests/                   ✅ создано
├── requirements.txt         ✅ есть
├── README.md                ✅ есть
├── run_server.bat           ✅ есть
├── run_client.bat           ✅ есть
├── .gitignore               ✅ есть
└── seed_db.py               ✅ есть (генерация тестовых данных)
```

---

## 🧪 3. ТЕСТОВЫЕ ДАННЫЕ

### Для тестирования OCR нужны:

| # | Файл | Статус | Описание |
|---|------|--------|----------|
| 1 | test_ttn.pdf | ⬜ | Пример ТТН в PDF |
| 2 | test_ttn.jpg | ⬜ | Пример ТТН как изображение |

---

## ⚙️ 4. КОНФИГУРАЦИЯ

### Проверить config/config.json:

| Параметр | Значение | Проверить |
|----------|----------|-----------|
| tesseract.path | C:/Program Files/Tesseract-OCR/tesseract.exe | ⬜ Путь существует? |
| poppler.path | C:/poppler/bin | ⬜ Путь существует? |
| server.port | 8000 | ⬜ Порт свободен? |
| camera.default_index | 0 | ⬜ Камера подключена? |

---

## 🔧 5. ИНСТРУМЕНТЫ РАЗРАБОТКИ (опционально)

| # | Инструмент | Рекомендация |
|---|------------|--------------|
| 1 | VS Code | IDE с поддержкой Python |
| 2 | Python Extension | Для VS Code |
| 3 | Git | Контроль версий |
| 4 | Postman / Insomnia | Тестирование API |
| 5 | DB Browser for SQLite | Просмотр БД |

---

## 🚀 6. ПОРЯДОК ДЕЙСТВИЙ

### Шаг 1: Установка ПО
```
1. Установить Python 3.12 (☑ Add to PATH)
2. Установить Tesseract OCR (☑ Russian language)
3. Распаковать Poppler в C:\poppler
4. Добавить в PATH:
   - C:\Program Files\Tesseract-OCR
   - C:\poppler\bin
5. Перезапустить терминал
```

### Шаг 2: Проверка окружения
```batch
python --version
pip --version
tesseract --version
pdftoppm -v
```

### Шаг 3: Подготовка проекта
```batch
cd путь\к\tmc_warehouse
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Шаг 4: Проверка зависимостей
```batch
python -c "import PySide6; print('PySide6 OK')"
python -c "import fastapi; print('FastAPI OK')"
python -c "import cv2; print('OpenCV OK')"
python -c "import pytesseract; print('Pytesseract OK')"
python -c "import peewee; print('Peewee OK')"
```

### Шаг 5: Начать разработку
```
Открыть TMC_WAREHOUSE_PROMPT_V2.md
Начать с: "Начинаю ЭТАП 1: СЕРВЕР — БАЗА ДАННЫХ"
```

---

## ❓ ЧАСТЫЕ ПРОБЛЕМЫ

### "tesseract is not recognized"
```
Решение: Добавить C:\Program Files\Tesseract-OCR в PATH
или указать полный путь в config.json
```

### "Unable to get page count. Is poppler installed?"
```
Решение: Установить Poppler, добавить C:\poppler\bin в PATH
```

### "No module named 'PySide6'"
```
Решение: pip install PySide6
```

### "Address already in use" (порт 8000)
```
Решение: Изменить порт в config.json или закрыть процесс:
netstat -ano | findstr :8000
taskkill /PID <номер> /F
```

---

## ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ

Перед началом разработки убедитесь:

- [x] Python 3.12 установлен и в PATH
- [x] Tesseract OCR установлен с русским языком
- [x] Poppler установлен и в PATH
- [x] Виртуальное окружение создано
- [x] Все pip пакеты установлены
- [x] Пути в config.json корректны
- [x] Тестовый PDF для OCR есть
- [x] Промпт TMC_WAREHOUSE_PROMPT_V2.md готов

**Все пункты выполнены. Система готова к работе!** 🚀
