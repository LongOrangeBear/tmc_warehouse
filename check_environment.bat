@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
::  TMC Warehouse - Проверка окружения
:: ============================================

cd /d "%~dp0"

echo.
echo  ╔═══════════════════════════════════════════════════╗
echo  ║   TMC Warehouse - ПРОВЕРКА ОКРУЖЕНИЯ              ║
echo  ╚═══════════════════════════════════════════════════╝
echo.

set ERRORS=0
set WARNINGS=0

:: ────────────────────────────────────────────
echo [1/7] Проверка Python...
:: ────────────────────────────────────────────

python --version >nul 2>&1
if errorlevel 1 (
    echo   [ОШИБКА] Python не найден!
    echo            Установите Python 3.12 с https://python.org
    set /a ERRORS+=1
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
    echo   [OK] Python !PYVER!
    
    :: Проверка версии 3.12+
    echo !PYVER! | findstr /r "^3\.1[2-9]\." >nul
    if errorlevel 1 (
        echo   [ПРЕДУПРЕЖДЕНИЕ] Рекомендуется Python 3.12+
        set /a WARNINGS+=1
    )
)

:: ────────────────────────────────────────────
echo.
echo [2/7] Проверка pip...
:: ────────────────────────────────────────────

pip --version >nul 2>&1
if errorlevel 1 (
    echo   [ОШИБКА] pip не найден!
    set /a ERRORS+=1
) else (
    for /f "tokens=2" %%v in ('pip --version 2^>^&1') do set PIPVER=%%v
    echo   [OK] pip !PIPVER!
)

:: ────────────────────────────────────────────
echo.
echo [3/7] Проверка Tesseract OCR...
:: ────────────────────────────────────────────

tesseract --version >nul 2>&1
if errorlevel 1 (
    :: Проверить стандартный путь
    if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        echo   [ПРЕДУПРЕЖДЕНИЕ] Tesseract найден, но не в PATH
        echo                    Добавьте C:\Program Files\Tesseract-OCR в PATH
        set /a WARNINGS+=1
    ) else (
        echo   [ОШИБКА] Tesseract не найден!
        echo            Установите с https://github.com/UB-Mannheim/tesseract/wiki
        set /a ERRORS+=1
    )
) else (
    for /f "tokens=2" %%v in ('tesseract --version 2^>^&1 ^| findstr /r "^tesseract"') do set TESSVER=%%v
    echo   [OK] Tesseract !TESSVER!
    
    :: Проверка русского языка
    tesseract --list-langs 2>&1 | findstr "rus" >nul
    if errorlevel 1 (
        echo   [ПРЕДУПРЕЖДЕНИЕ] Русский язык (rus) не установлен!
        echo                    Переустановите Tesseract с выбором Russian
        set /a WARNINGS+=1
    ) else (
        echo   [OK] Русский язык (rus) установлен
    )
)

:: ────────────────────────────────────────────
echo.
echo [4/7] Проверка Poppler...
:: ────────────────────────────────────────────

pdftoppm -v >nul 2>&1
if errorlevel 1 (
    :: Проверить стандартный путь
    if exist "C:\poppler\bin\pdftoppm.exe" (
        echo   [ПРЕДУПРЕЖДЕНИЕ] Poppler найден, но не в PATH
        echo                    Добавьте C:\poppler\bin в PATH
        set /a WARNINGS+=1
    ) else (
        echo   [ОШИБКА] Poppler не найден!
        echo            Скачайте с https://github.com/oswindows/poppler-windows/releases
        echo            Распакуйте в C:\poppler
        set /a ERRORS+=1
    )
) else (
    echo   [OK] Poppler установлен
)

:: ────────────────────────────────────────────
echo.
echo [5/7] Проверка виртуального окружения...
:: ────────────────────────────────────────────

if exist "venv\Scripts\activate.bat" (
    echo   [OK] venv существует
) else (
    echo   [INFO] venv не найден (будет создан при первом запуске)
)

:: ────────────────────────────────────────────
echo.
echo [6/7] Проверка конфигурации...
:: ────────────────────────────────────────────

if exist "config\config.json" (
    echo   [OK] config/config.json существует
) else (
    echo   [ОШИБКА] config/config.json не найден!
    set /a ERRORS+=1
)

:: ────────────────────────────────────────────
echo.
echo [7/7] Проверка структуры проекта...
:: ────────────────────────────────────────────

set MISSING=0

if not exist "common\models.py" (
    echo   [ОШИБКА] common/models.py не найден
    set /a MISSING+=1
)
if not exist "server\src\main_server.py" (
    echo   [ОШИБКА] server/src/main_server.py не найден
    set /a MISSING+=1
)
if not exist "client\src\main_client.py" (
    echo   [ОШИБКА] client/src/main_client.py не найден
    set /a MISSING+=1
)
if not exist "requirements.txt" (
    echo   [ОШИБКА] requirements.txt не найден
    set /a MISSING+=1
)

if %MISSING%==0 (
    echo   [OK] Основные файлы на месте
) else (
    set /a ERRORS+=%MISSING%
)

:: ────────────────────────────────────────────
:: Итоги
:: ────────────────────────────────────────────

echo.
echo ════════════════════════════════════════════════════
echo.

if %ERRORS%==0 (
    if %WARNINGS%==0 (
        echo   ✅ ВСЁ ГОТОВО К РАЗРАБОТКЕ!
        echo.
        echo   Следующие шаги:
        echo   1. Запустите: run_server.bat
        echo   2. В новом окне: run_client.bat
    ) else (
        echo   ⚠️  ГОТОВО С ПРЕДУПРЕЖДЕНИЯМИ: %WARNINGS%
        echo.
        echo   Рекомендуется исправить предупреждения выше.
        echo   Разработку можно начать, но могут быть проблемы.
    )
) else (
    echo   ❌ ОБНАРУЖЕНЫ ОШИБКИ: %ERRORS%
    echo.
    echo   Исправьте ошибки выше перед началом разработки.
)

echo.
echo ════════════════════════════════════════════════════
echo.

pause
