@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
::  TMC Warehouse - Запуск клиента
:: ============================================

cd /d "%~dp0"

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║      TMC Warehouse - КЛИЕНТ           ║
echo  ╚═══════════════════════════════════════╝
echo.

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python 3.12 и добавьте в PATH
    goto :error
)

:: Проверка/создание venv
if not exist "venv" (
    echo [INFO] Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать venv
        goto :error
    )
)

:: Активация venv
echo [INFO] Активация виртуального окружения...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ОШИБКА] Не удалось активировать venv
    goto :error
)

:: Проверка зависимостей
pip show PySide6 >nul 2>&1
if errorlevel 1 (
    echo [INFO] Установка зависимостей...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить зависимости
        goto :error
    )
)

:: Проверка Tesseract
where tesseract >nul 2>&1
if errorlevel 1 (
    echo [ПРЕДУПРЕЖДЕНИЕ] Tesseract не найден в PATH
    echo OCR может не работать. Проверьте config/config.json
    echo.
)

:: Проверка сервера
echo [INFO] Проверка доступности сервера...
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/api/v1/health >temp_health.txt 2>nul
set /p HEALTH_CODE=<temp_health.txt
del temp_health.txt 2>nul

if "%HEALTH_CODE%"=="200" (
    echo [OK] Сервер доступен
) else (
    echo [ПРЕДУПРЕЖДЕНИЕ] Сервер недоступен!
    echo Запустите сначала run_server.bat
    echo.
    set /p CONTINUE="Продолжить без сервера? (y/n): "
    if /i not "!CONTINUE!"=="y" goto :end
)

echo.
echo [INFO] Запуск клиентского приложения...
echo.
echo ────────────────────────────────────────────
echo.

:: Запуск клиента
python -m client.src.main_client

:: Если клиент завершился с ошибкой
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Клиент завершился с ошибкой
    goto :error
)

goto :end

:error
echo.
echo ════════════════════════════════════════════
echo  Произошла ошибка. Проверьте сообщения выше.
echo ════════════════════════════════════════════
pause
exit /b 1

:end
echo.
echo [INFO] Клиент закрыт
pause
