# 🚀 GitHub Actions: Автоматическая сборка Windows EXE

## Полное руководство для проекта TMC Warehouse

---

## 📋 СОДЕРЖАНИЕ

1. [Обзор и архитектура](#1-обзор-и-архитектура)
2. [Настройка репозитория](#2-настройка-репозитория)
3. [Workflow файлы](#3-workflow-файлы)
4. [PyInstaller конфигурация](#4-pyinstaller-конфигурация)
5. [Использование](#5-использование)
6. [Релизы](#6-релизы)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. ОБЗОР И АРХИТЕКТУРА

### Что делает GitHub Actions для нашего проекта:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GITHUB ACTIONS PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   git push / PR                                                         │
│        │                                                                │
│        ▼                                                                │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    JOB: test-linux                               │  │
│   │                    (ubuntu-latest)                               │  │
│   │  ┌─────────────────────────────────────────────────────────┐    │  │
│   │  │ 1. Checkout code                                        │    │  │
│   │  │ 2. Setup Python 3.12                                    │    │  │
│   │  │ 3. Install Tesseract + Poppler                          │    │  │
│   │  │ 4. pip install -r requirements.txt                      │    │  │
│   │  │ 5. pytest tests/ --cov                                  │    │  │
│   │  │ 6. Upload coverage report                               │    │  │
│   │  └─────────────────────────────────────────────────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│        │                                                                │
│        │ (параллельно)                                                 │
│        ▼                                                                │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    JOB: test-windows                             │  │
│   │                    (windows-latest)                              │  │
│   │  ┌─────────────────────────────────────────────────────────┐    │  │
│   │  │ 1. Checkout code                                        │    │  │
│   │  │ 2. Setup Python 3.12                                    │    │  │
│   │  │ 3. Install Tesseract (choco)                            │    │  │
│   │  │ 4. Install Poppler (choco)                              │    │  │
│   │  │ 5. pip install -r requirements.txt                      │    │  │
│   │  │ 6. pytest tests/                                        │    │  │
│   │  └─────────────────────────────────────────────────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│        │                                                                │
│        │ (после успешных тестов)                                       │
│        ▼                                                                │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    JOB: build-windows                            │  │
│   │                    (windows-latest)                              │  │
│   │  ┌─────────────────────────────────────────────────────────┐    │  │
│   │  │ 1. Checkout code                                        │    │  │
│   │  │ 2. Setup Python + dependencies                          │    │  │
│   │  │ 3. pip install pyinstaller                              │    │  │
│   │  │ 4. PyInstaller → tmc_server.exe                         │    │  │
│   │  │ 5. PyInstaller → tmc_client.exe                         │    │  │
│   │  │ 6. Package with config + data                           │    │  │
│   │  │ 7. Upload artifacts (ZIP)                               │    │  │
│   │  └─────────────────────────────────────────────────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│        │                                                                │
│        │ (только при создании тега v*.*.*)                             │
│        ▼                                                                │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                    JOB: release                                  │  │
│   │  ┌─────────────────────────────────────────────────────────┐    │  │
│   │  │ 1. Download artifacts                                   │    │  │
│   │  │ 2. Create GitHub Release                                │    │  │
│   │  │ 3. Upload EXE files to release                          │    │  │
│   │  └─────────────────────────────────────────────────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Что ты получаешь:

| Триггер | Результат |
|---------|-----------|
| `git push` в любую ветку | Тесты на Linux + Windows |
| `git push` в `main` | Тесты + Сборка EXE + Артефакты |
| `git tag v1.0.0` + `push` | Тесты + Сборка + GitHub Release |
| Pull Request | Тесты (без сборки) |

---

## 2. НАСТРОЙКА РЕПОЗИТОРИЯ

### Шаг 1: Создать структуру папок

```bash
# В корне проекта
mkdir -p .github/workflows
mkdir -p scripts
mkdir -p tests
```

### Шаг 2: Структура должна быть такой

```
tmc_warehouse/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Основной CI/CD pipeline
│       └── release.yml         # Релизы (опционально, отдельно)
├── scripts/
│   ├── build_server.spec       # PyInstaller spec для сервера
│   ├── build_client.spec       # PyInstaller spec для клиента
│   └── package.py              # Скрипт упаковки
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_server_db.py
│   ├── test_server_api.py
│   └── test_client_services.py
├── common/
├── server/
├── client/
├── config/
│   ├── config.json             # Windows конфиг
│   └── config_linux.json       # Linux конфиг
├── requirements.txt
├── requirements-dev.txt        # Тестовые зависимости
└── pyproject.toml              # Метаданные проекта
```

### Шаг 3: Создать requirements-dev.txt

```txt
# requirements-dev.txt
-r requirements.txt

# Testing
pytest==8.0.0
pytest-cov==4.1.0
pytest-asyncio==0.23.0
httpx==0.26.0

# Build
pyinstaller==6.3.0

# Linting (опционально)
ruff==0.1.14
black==24.1.0
mypy==1.8.0
```

---

## 3. WORKFLOW ФАЙЛЫ

### Основной файл: `.github/workflows/ci.yml`

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*.*.*' ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: '3.12'

jobs:
  # ════════════════════════════════════════════════════════════════
  # JOB 1: Тесты на Linux (быстрые)
  # ════════════════════════════════════════════════════════════════
  test-linux:
    name: Test on Linux
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            tesseract-ocr \
            tesseract-ocr-rus \
            poppler-utils \
            libgl1-mesa-glx \
            libglib2.0-0 \
            libxcb-xinerama0 \
            libxkbcommon-x11-0 \
            libxcb-cursor0 \
            xvfb

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run linting (optional)
        continue-on-error: true
        run: |
          pip install ruff
          ruff check server/ client/ common/

      - name: Run tests with coverage
        run: |
          # Используем xvfb для GUI тестов
          xvfb-run -a pytest tests/ -v \
            --cov=server \
            --cov=client \
            --cov=common \
            --cov-report=xml \
            --cov-report=term-missing \
            --ignore=tests/test_camera.py

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: false

  # ════════════════════════════════════════════════════════════════
  # JOB 2: Тесты на Windows
  # ════════════════════════════════════════════════════════════════
  test-windows:
    name: Test on Windows
    runs-on: windows-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install Tesseract OCR
        run: |
          choco install tesseract --params "/Languages:rus" -y
        shell: powershell

      - name: Install Poppler
        run: |
          choco install poppler -y
        shell: powershell

      - name: Add to PATH
        run: |
          echo "C:\Program Files\Tesseract-OCR" >> $env:GITHUB_PATH
          echo "C:\ProgramData\chocolatey\lib\poppler\tools\poppler-24.02.0\Library\bin" >> $env:GITHUB_PATH
        shell: powershell

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run tests
        run: |
          pytest tests/ -v --ignore=tests/test_camera.py
        shell: powershell

  # ════════════════════════════════════════════════════════════════
  # JOB 3: Сборка Windows EXE
  # ════════════════════════════════════════════════════════════════
  build-windows:
    name: Build Windows EXE
    runs-on: windows-latest
    needs: [test-linux, test-windows]
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v')
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install Tesseract OCR
        run: |
          choco install tesseract --params "/Languages:rus" -y
        shell: powershell

      - name: Install Poppler
        run: |
          choco install poppler -y
        shell: powershell

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller==6.3.0
        shell: powershell

      - name: Get version
        id: version
        run: |
          if ("${{ github.ref }}" -match "refs/tags/v(.+)") {
            echo "VERSION=$($matches[1])" >> $env:GITHUB_OUTPUT
          } else {
            echo "VERSION=dev-${{ github.sha }}" >> $env:GITHUB_OUTPUT
          }
        shell: powershell

      - name: Build Server EXE
        run: |
          pyinstaller `
            --onefile `
            --name "tmc_server" `
            --icon "resources/icons/server.ico" `
            --add-data "common;common" `
            --hidden-import "peewee" `
            --hidden-import "uvicorn.logging" `
            --hidden-import "uvicorn.loops" `
            --hidden-import "uvicorn.loops.auto" `
            --hidden-import "uvicorn.protocols" `
            --hidden-import "uvicorn.protocols.http" `
            --hidden-import "uvicorn.protocols.http.auto" `
            --hidden-import "uvicorn.protocols.websockets" `
            --hidden-import "uvicorn.protocols.websockets.auto" `
            --hidden-import "uvicorn.lifespan" `
            --hidden-import "uvicorn.lifespan.on" `
            server/src/main_server.py
        shell: powershell

      - name: Build Client EXE
        run: |
          pyinstaller `
            --onefile `
            --windowed `
            --name "tmc_client" `
            --icon "resources/icons/client.ico" `
            --add-data "common;common" `
            --hidden-import "PySide6.QtCore" `
            --hidden-import "PySide6.QtGui" `
            --hidden-import "PySide6.QtWidgets" `
            --hidden-import "cv2" `
            --hidden-import "pytesseract" `
            --hidden-import "pdf2image" `
            client/src/main_client.py
        shell: powershell

      - name: Create distribution package
        run: |
          # Создать папку дистрибутива
          New-Item -ItemType Directory -Force -Path "dist/tmc_warehouse"
          
          # Копировать exe файлы
          Copy-Item "dist/tmc_server.exe" "dist/tmc_warehouse/"
          Copy-Item "dist/tmc_client.exe" "dist/tmc_warehouse/"
          
          # Копировать конфиг
          New-Item -ItemType Directory -Force -Path "dist/tmc_warehouse/config"
          Copy-Item "config/config.json" "dist/tmc_warehouse/config/"
          
          # Создать папки данных
          New-Item -ItemType Directory -Force -Path "dist/tmc_warehouse/data/database"
          New-Item -ItemType Directory -Force -Path "dist/tmc_warehouse/data/receipts"
          New-Item -ItemType Directory -Force -Path "dist/tmc_warehouse/data/logs"
          
          # Копировать bat файлы
          Copy-Item "run_server.bat" "dist/tmc_warehouse/"
          Copy-Item "run_client.bat" "dist/tmc_warehouse/"
          
          # Создать README
          @"
          TMC Warehouse System v${{ steps.version.outputs.VERSION }}
          ================================================
          
          Запуск:
          1. Запустите run_server.bat (оставьте окно открытым)
          2. Запустите run_client.bat
          
          Требования:
          - Windows 10/11
          - Tesseract OCR (установить отдельно)
          - Poppler (установить отдельно)
          
          Конфигурация: config/config.json
          "@ | Out-File -FilePath "dist/tmc_warehouse/README.txt" -Encoding UTF8
          
          # Создать архив
          Compress-Archive -Path "dist/tmc_warehouse/*" -DestinationPath "dist/tmc_warehouse_${{ steps.version.outputs.VERSION }}.zip"
        shell: powershell

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: tmc-warehouse-windows-${{ steps.version.outputs.VERSION }}
          path: |
            dist/tmc_warehouse_*.zip
          retention-days: 30

  # ════════════════════════════════════════════════════════════════
  # JOB 4: Создание релиза (только для тегов)
  # ════════════════════════════════════════════════════════════════
  release:
    name: Create Release
    runs-on: ubuntu-latest
    needs: [build-windows]
    if: startsWith(github.ref, 'refs/tags/v')
    
    permissions:
      contents: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Get version from tag
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          pattern: tmc-warehouse-windows-*
          path: artifacts
          merge-multiple: true

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          name: TMC Warehouse v${{ steps.version.outputs.VERSION }}
          body: |
            ## TMC Warehouse System v${{ steps.version.outputs.VERSION }}
            
            ### 📦 Установка
            1. Скачайте `tmc_warehouse_${{ steps.version.outputs.VERSION }}.zip`
            2. Распакуйте в любую папку
            3. Установите [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
            4. Установите [Poppler](https://github.com/oswindows/poppler-windows/releases)
            5. Настройте пути в `config/config.json`
            
            ### 🚀 Запуск
            1. Запустите `run_server.bat`
            2. Запустите `run_client.bat`
            
            ### 📝 Изменения
            См. [CHANGELOG.md](CHANGELOG.md)
          files: |
            artifacts/*.zip
          draft: false
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 4. PYINSTALLER КОНФИГУРАЦИЯ

### Опциональные spec файлы для тонкой настройки

#### `scripts/build_server.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec для сервера."""

import sys
from pathlib import Path

# Путь к проекту
PROJECT_ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(PROJECT_ROOT / 'server' / 'src' / 'main_server.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / 'common'), 'common'),
    ],
    hiddenimports=[
        'peewee',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'pydantic',
        'starlette',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6',
        'PyQt5',
        'PyQt6',
        'tkinter',
        'matplotlib',
        'numpy',
        'cv2',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='tmc_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Консольное приложение
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / 'resources' / 'icons' / 'server.ico'),
)
```

#### `scripts/build_client.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec для клиента."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(PROJECT_ROOT / 'client' / 'src' / 'main_client.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / 'common'), 'common'),
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'cv2',
        'numpy',
        'pytesseract',
        'pdf2image',
        'PIL',
        'pydantic',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='tmc_client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI приложение (без консоли)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / 'resources' / 'icons' / 'client.ico'),
)
```

---

## 5. ИСПОЛЬЗОВАНИЕ

### Ежедневная работа (Ubuntu)

```bash
# Разработка как обычно
cd ~/projects/tmc_warehouse
source venv/bin/activate

# Пишешь код...

# Локальные тесты
pytest tests/ -v

# Коммит и пуш
git add .
git commit -m "feat: добавил OCR сервис"
git push origin develop
```

### Проверка статуса сборки

```
1. Открой GitHub → твой репозиторий → Actions
2. Увидишь статус всех jobs
3. Зелёная галочка = всё ОК
4. Красный крест = есть ошибки (кликни чтобы увидеть логи)
```

### Скачивание артефактов (EXE)

```
1. GitHub → Actions → выбери успешный workflow
2. Scroll down → Artifacts
3. Скачай "tmc-warehouse-windows-..."
4. Распакуй ZIP
5. Тестируй на Windows
```

### Мерж в main (для сборки)

```bash
# Когда готов к сборке
git checkout main
git merge develop
git push origin main

# GitHub Actions автоматически:
# - Запустит тесты
# - Соберёт EXE
# - Выложит артефакты
```

---

## 6. РЕЛИЗЫ

### Создание релиза

```bash
# 1. Убедись что main стабилен
git checkout main
git pull

# 2. Обнови версию в коде (если есть)
# Например в config/config.json или __version__.py

# 3. Создай и запуш тег
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# GitHub Actions автоматически:
# - Запустит тесты
# - Соберёт EXE
# - Создаст GitHub Release
# - Прикрепит ZIP с exe к релизу
```

### Версионирование (SemVer)

```
v1.0.0 - Первый релиз
v1.0.1 - Багфиксы
v1.1.0 - Новые фичи (обратно совместимые)
v2.0.0 - Ломающие изменения
```

### Просмотр релизов

```
GitHub → твой репозиторий → Releases
```

---

## 7. TROUBLESHOOTING

### Ошибка: "Tesseract not found"

```yaml
# В workflow, после установки добавить в PATH:
- name: Add Tesseract to PATH
  run: |
    echo "C:\Program Files\Tesseract-OCR" >> $env:GITHUB_PATH
  shell: powershell
```

### Ошибка: "No module named 'xxx'"

```yaml
# Добавить в hidden-imports PyInstaller:
--hidden-import "имя_модуля"
```

### Ошибка: GUI тесты падают на Linux

```yaml
# Использовать xvfb (виртуальный дисплей):
- name: Run tests
  run: |
    xvfb-run -a pytest tests/ -v
```

### Ошибка: "EXE слишком большой" (>100MB)

```yaml
# Добавить excludes в PyInstaller:
--exclude-module "matplotlib"
--exclude-module "scipy"
--exclude-module "pandas"
```

### Ошибка: "Permission denied" при создании релиза

```yaml
# Добавить permissions в job:
permissions:
  contents: write
```

### Логи Actions слишком большие

```yaml
# Ограничить вывод pytest:
pytest tests/ -v --tb=short
```

---

## 📁 ИТОГОВАЯ СТРУКТУРА

После настройки твой проект должен выглядеть так:

```
tmc_warehouse/
├── .github/
│   └── workflows/
│       └── ci.yml                 ← Главный workflow
├── scripts/
│   ├── build_server.spec          ← Опционально
│   └── build_client.spec          ← Опционально
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py
├── resources/
│   └── icons/
│       ├── server.ico             ← Иконка сервера
│       └── client.ico             ← Иконка клиента
├── common/
├── server/
├── client/
├── config/
│   ├── config.json
│   └── config_linux.json
├── requirements.txt
├── requirements-dev.txt            ← Тестовые зависимости
├── .gitignore
└── README.md
```

---

## ✅ ЧЕКЛИСТ НАСТРОЙКИ

- [ ] Создана папка `.github/workflows/`
- [ ] Создан файл `ci.yml`
- [ ] Создан `requirements-dev.txt`
- [ ] Есть хотя бы один тест в `tests/`
- [ ] Репозиторий на GitHub
- [ ] Первый `git push` выполнен
- [ ] Actions запустился (проверить во вкладке Actions)
- [ ] Тесты проходят (зелёная галочка)
- [ ] Артефакты генерируются (для main ветки)

---

**Готово!** Теперь каждый push будет автоматически тестироваться, а push в main — собирать exe.
