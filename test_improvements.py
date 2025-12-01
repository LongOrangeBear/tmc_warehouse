import sys
import os
import logging
import json
import csv
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from PySide6.QtWidgets import QApplication
from client.src.config import save_config, get_config
from client.src.ui.history_dialog import HistoryDialog
from common.models import ReceptionShort, ReceptionStatus
from datetime import date

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IMPROVEMENTS_TEST")

def test_config_save():
    logger.info("Testing save_config...")
    original_config = get_config().copy()
    
    test_config = original_config.copy()
    test_config["test_key"] = "test_value"
    
    try:
        save_config(test_config)
        
        # Reload and check
        loaded = get_config()
        if loaded.get("test_key") == "test_value":
            logger.info("✅ Config saved and loaded successfully")
        else:
            logger.error("❌ Config save failed")
            
    finally:
        # Restore
        save_config(original_config)

def test_export_csv():
    logger.info("Testing CSV export...")
    app = QApplication(sys.argv)
    
    # Mock SyncService
    with patch('client.src.ui.history_dialog.SyncService') as MockSync:
        dialog = HistoryDialog()
        
        # Mock data
        dialog.receptions = [
            ReceptionShort(
                id=1, 
                ttn_number="TEST-1", 
                ttn_date=date.today(), 
                supplier="Supplier A", 
                status=ReceptionStatus.COMPLETED,
                created_at=date.today()
            ),
            ReceptionShort(
                id=2, 
                ttn_number="TEST-2", 
                ttn_date=date.today(), 
                supplier="Supplier B", 
                status=ReceptionStatus.PENDING,
                created_at=date.today()
            )
        ]
        
        # Mock QFileDialog
        output_file = Path("test_report.csv")
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=(str(output_file), "CSV")):
            # Mock QMessageBox to avoid blocking
            with patch('PySide6.QtWidgets.QMessageBox.information'):
                dialog._export_data()
                
        # Verify file
        if output_file.exists():
            logger.info(f"✅ CSV file created: {output_file}")
            with open(output_file, "r", encoding="utf-8-sig") as f:
                content = f.read()
                logger.info(f"Content:\n{content}")
                if "TEST-1" in content and "Supplier B" in content:
                    logger.info("✅ Content verified")
                else:
                    logger.error("❌ Content mismatch")
            output_file.unlink()
        else:
            logger.error("❌ CSV file not created")

if __name__ == "__main__":
    test_config_save()
    test_export_csv()
