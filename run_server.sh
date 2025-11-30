#!/bin/bash
# ============================================
#  TMC Warehouse - Запуск сервера (Linux)
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║      TMC Warehouse - СЕРВЕР           ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "[ОШИБКА] Python3 не найден!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "[OK] Python $PYTHON_VERSION"

# Проверка/создание venv
if [ ! -d "venv" ]; then
    echo "[INFO] Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация venv
echo "[INFO] Активация venv..."
source venv/bin/activate

# Проверка зависимостей
if ! pip show fastapi &> /dev/null; then
    echo "[INFO] Установка зависимостей..."
    pip install -r requirements.txt
fi

# Создание директорий
mkdir -p data/database data/receipts data/logs

echo ""
echo "[INFO] Запуск сервера FastAPI..."
echo "[INFO] API: http://127.0.0.1:8000"
echo "[INFO] Docs: http://127.0.0.1:8000/docs"
echo "[INFO] Для остановки: Ctrl+C"
echo ""
echo "────────────────────────────────────────"
echo ""

# Запуск
python -m server.src.main_server
