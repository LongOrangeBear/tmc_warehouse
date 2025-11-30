@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
::  TMC Warehouse - Первоначальная настройка
:: ============================================

cd /d "%~dp0"

echo.
echo  ╔═══════════════════════════════════════════════════╗
echo  ║   TMC Warehouse - ПЕРВОНАЧАЛЬНАЯ НАСТРОЙКА        ║
echo  ╚═══════════════════════════════════════════════════╝
echo.

:: ────────────────────────────────────────────
echo [1/5] Проверка Python...
:: ────────────────────────────────────────────

python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [ОШИБКА] Python не найден!
    echo.
    echo   Установите Python 3.12:
    echo   https://www.python.org/downloads/release/python-3120/
    echo.
    echo   ВАЖНО: При установке отметьте "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   [OK] Python %PYVER%

:: ────────────────────────────────────────────
echo.
echo [2/5] Создание виртуального окружения...
:: ────────────────────────────────────────────

if exist "venv" (
    echo   [INFO] venv уже существует, пропускаем...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo   [ОШИБКА] Не удалось создать venv
        pause
        exit /b 1
    )
    echo   [OK] venv создан
)

:: ────────────────────────────────────────────
echo.
echo [3/5] Активация окружения и установка зависимостей...
:: ────────────────────────────────────────────

call venv\Scripts\activate.bat

echo   Установка пакетов (это может занять несколько минут)...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

if errorlevel 1 (
    echo   [ОШИБКА] Не удалось установить зависимости
    echo   Попробуйте запустить вручную:
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo   [OK] Все зависимости установлены

:: ────────────────────────────────────────────
echo.
echo [4/5] Создание директорий данных...
:: ────────────────────────────────────────────

if not exist "data" mkdir "data"
if not exist "data\database" mkdir "data\database"
if not exist "data\receipts" mkdir "data\receipts"
if not exist "data\logs" mkdir "data\logs"
if not exist "test_data" mkdir "test_data"

echo   [OK] Директории созданы

:: ────────────────────────────────────────────
echo.
echo [5/5] Проверка установленных пакетов...
:: ────────────────────────────────────────────

echo.
echo   Проверка основных библиотек:

python -c "import PySide6; print('   [OK] PySide6')" 2>nul || echo "   [ОШИБКА] PySide6"
python -c "import fastapi; print('   [OK] FastAPI')" 2>nul || echo "   [ОШИБКА] FastAPI"
python -c "import peewee; print('   [OK] Peewee')" 2>nul || echo "   [ОШИБКА] Peewee"
python -c "import cv2; print('   [OK] OpenCV')" 2>nul || echo "   [ОШИБКА] OpenCV"
python -c "import pytesseract; print('   [OK] Pytesseract')" 2>nul || echo "   [ОШИБКА] Pytesseract"
python -c "import pdf2image; print('   [OK] pdf2image')" 2>nul || echo "   [ОШИБКА] pdf2image"
python -c "import pydantic; print('   [OK] Pydantic')" 2>nul || echo "   [ОШИБКА] Pydantic"
python -c "import requests; print('   [OK] Requests')" 2>nul || echo "   [ОШИБКА] Requests"

:: ────────────────────────────────────────────
:: Итоги
:: ────────────────────────────────────────────

echo.
echo ════════════════════════════════════════════════════
echo.
echo   ✅ НАСТРОЙКА ЗАВЕРШЕНА!
echo.
echo   Теперь проверьте внешние зависимости:
echo.
echo   1. Tesseract OCR:
echo      tesseract --version
echo      Если не найден - установите с:
echo      https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo   2. Poppler:
echo      pdftoppm -v
echo      Если не найден - скачайте с:
echo      https://github.com/oswindows/poppler-windows/releases
echo      Распакуйте в C:\poppler и добавьте C:\poppler\bin в PATH
echo.
echo   3. Запустите check_environment.bat для полной проверки
echo.
echo ════════════════════════════════════════════════════
echo.

pause
