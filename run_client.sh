#!/bin/bash
# ============================================
#  TMC Warehouse - Запуск клиента (Linux)
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║      TMC Warehouse - КЛИЕНТ           ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "[ОШИБКА] Python3 не найден!"
    exit 1
fi

# Проверка venv
if [ ! -d "venv" ]; then
    echo "[INFO] Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация venv
source venv/bin/activate

# Проверка зависимостей
if ! pip show PySide6 &> /dev/null; then
    echo "[INFO] Установка зависимостей..."
    pip install -r requirements.txt
fi

# Проверка Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "[ПРЕДУПРЕЖДЕНИЕ] Tesseract не найден!"
    echo "Установите: sudo apt install tesseract-ocr tesseract-ocr-rus"
fi

# Проверка сервера
echo "[INFO] Проверка сервера..."
if curl -s http://127.0.0.1:8000/api/v1/health > /dev/null 2>&1; then
    echo "[OK] Сервер доступен"
else
    echo "[ПРЕДУПРЕЖДЕНИЕ] Сервер недоступен!"
    echo "Запустите: ./run_server.sh"
    read -p "Продолжить без сервера? (y/n): " choice
    if [ "$choice" != "y" ]; then
        exit 0
    fi
fi

echo ""
echo "[INFO] Запуск клиента..."
echo ""

# Запуск
python -m client.src.main_client
