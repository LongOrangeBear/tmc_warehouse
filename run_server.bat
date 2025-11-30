@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
::  TMC Warehouse - Запуск сервера
:: ============================================

cd /d "%~dp0"

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║      TMC Warehouse - СЕРВЕР           ║
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
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [INFO] Установка зависимостей...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить зависимости
        goto :error
    )
)

:: Создание директорий данных
if not exist "data\database" mkdir "data\database"
if not exist "data\receipts" mkdir "data\receipts"
if not exist "data\logs" mkdir "data\logs"

echo.
echo [INFO] Запуск сервера FastAPI...
echo [INFO] API доступен по адресу: http://127.0.0.1:8000
echo [INFO] Документация: http://127.0.0.1:8000/docs
echo [INFO] Для остановки нажмите Ctrl+C
echo.
echo ────────────────────────────────────────────
echo.

:: Запуск сервера
python -m server.src.main_server

:: Если сервер завершился с ошибкой
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Сервер завершился с ошибкой
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
echo [INFO] Сервер остановлен
pause
