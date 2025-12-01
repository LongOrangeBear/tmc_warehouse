#!/bin/bash
# Run TMC Warehouse Server

echo "Starting TMC Warehouse Server..."

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Initialize database if needed
echo "Initializing database..."
python -c "from server.src.db.migrations import init_db, seed_products; init_db(); seed_products()"

# Run server
echo "Starting FastAPI server..."
python -m uvicorn server.src.main_server:app --host 127.0.0.1 --port 8000 --reload
