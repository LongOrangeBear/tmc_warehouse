#!/bin/bash
# Run TMC Warehouse Client

echo "Starting TMC Warehouse Client..."

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run client
python client/src/main_client.py
