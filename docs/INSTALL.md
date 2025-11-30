# INSTALL: установка и запуск системы приёма ТМЦ

Этот документ описывает установку и запуск системы в режиме разработки / тестового задания.

## 1. Системные требования

- ОС: Windows 10 или Windows 11.
- Python 3.12 (x64).
- Доступ к интернету для установки зависимостей (pip).
- Установленный Tesseract OCR (с языком `rus`).
- Установленный Poppler для Windows (для pdf2image).

## 2. Подготовка окружения

### 2.1. Установка Python

1. Скачайте Python 3.12 с официального сайта python.org.
2. При установке отметьте галочку "Add Python to PATH".
3. После установки проверьте в терминале (PowerShell / cmd):

   ```bash
   python --version
   ```

   Должна отображаться версия 3.12.x.

### 2.2. Установка Tesseract OCR

1. Скачайте установщик Tesseract для Windows (например, с репозитория UB Mannheim).
2. Установите Tesseract в директорию по умолчанию:

   ```
   C:\Program Files\Tesseract-OCR\
   ```

3. Убедитесь, что установлены языковые данные для русского (`rus.traineddata`).

4. Опционально добавьте путь `C:\Program Files\Tesseract-OCR\` в системную переменную PATH.

### 2.3. Установка Poppler

1. Скачайте сборку Poppler для Windows (например, из репозитория `oschwartz10612/poppler-windows`).
2. Распакуйте архив, например, в:

   ```
   C:\poppler
   ```

3. В конфиге (`config/config.json`) укажите:

   ```json
   "poppler": {
     "path": "C:/poppler/bin"
   }
   ```

## 3. Установка зависимостей проекта

1. Откройте терминал в корне проекта `tmc_warehouse/`.
2. Создайте виртуальное окружение (рекомендуется):

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

## 4. Конфигурация

Файл конфигурации: `config/config.json`.

Проверьте и при необходимости поправьте:

- пути к БД, логам, директориям приёмок;
- путь к Tesseract (`tesseract.path`);
- путь к Poppler (`poppler.path`);
- настройки камеры (`camera.default_index` и т.д.);
- адрес сервера (`server.host`, `server.port`).

Пример значения:

```json
{
  "app": {
    "name": "TMC Warehouse",
    "version": "1.0.0",
    "language": "ru"
  },
  "paths": {
    "database": "data/database/warehouse.db",
    "receipts_root": "data/receipts",
    "logs": "data/logs"
  },
  "tesseract": {
    "path": "C:/Program Files/Tesseract-OCR/tesseract.exe",
    "languages": ["rus"],
    "psm": 6
  },
  "poppler": {
    "path": "C:/poppler/bin"
  },
  "camera": {
    "default_index": 0,
    "resolution": [1280, 720],
    "fps": 30,
    "codec": "MJPG",
    "container": "avi"
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8000,
    "base_url": "http://127.0.0.1:8000/api/v1",
    "timeout": 30
  },
  "sync": {
    "retry_count": 3,
    "retry_delay": 5
  },
  "validation": {
    "control_types": {
      "weight_check": {
        "description": "Проверка веса",
        "params": ["target_weight", "tolerance"]
      },
      "visual_check": {
        "description": "Визуальный осмотр",
        "params": ["checklist"]
      },
      "dimension_check": {
        "description": "Проверка размеров",
        "params": ["length", "width", "height", "tolerance"]
      },
      "quantity_check": {
        "description": "Пересчёт количества",
        "params": ["expected_count"]
      }
    }
  }
}
```

## 5. Структура директорий данных

При первом запуске убедитесь, что существуют каталоги:

- `data/database/`
- `data/receipts/`
- `data/logs/`

Если их нет, создайте вручную или настройте код так, чтобы он создавал их автоматически при старте.

## 6. Запуск сервера

В активированном виртуальном окружении:

```bash
python -m server.src.main_server
```

Или через файл `run_server.bat`, если он настроен.

По умолчанию сервер стартует на `http://127.0.0.1:8000`.

Проверьте:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Должен вернуться JSON со статусом `"ok"`.

## 7. Запуск клиента

В активированном виртуальном окружении:

```bash
python -m client.src.main_client
```

Или через `run_client.bat`.

Клиент при старте может:

- проверить доступность сервера;
- при необходимости показать пользователю предупреждение.

## 8. (Опционально) Сборка exe (PyInstaller)

Для тестового задания достаточно запускать из исходников.  
Если требуется собрать exe, общий подход:

1. Установить PyInstaller:

   ```bash
   pip install pyinstaller
   ```

2. Собрать сервер:

   ```bash
   pyinstaller --onefile --name server.exe server/src/main_server.py
   ```

3. Собрать клиент:

   ```bash
   pyinstaller --onefile --name client.exe client/src/main_client.py
   ```

4. Убедиться, что рядом с exe доступны:
   - `config/config.json`,
   - директория `data/`,
   - каталоги `tessdata` (для Tesseract) и бинарники Poppler (если нужны).

Параметры PyInstaller могут изменяться в зависимости от итоговой реализации.
