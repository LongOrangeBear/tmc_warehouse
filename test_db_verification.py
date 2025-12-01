import sys
import os
import logging
from pathlib import Path
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from PySide6.QtWidgets import QApplication
from client.src.ui.results_widget import ResultsWidget
from common.models import ReceptionItemCreate

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DB_VERIFICATION_TEST")

def test_db_verification():
    """Test database verification in ResultsWidget."""
    app = QApplication(sys.argv)
    
    widget = ResultsWidget()
    
    # Create test items (artикулы из seed_db.py)
    items = [
        ReceptionItemCreate(
            article="512",
            name="Ноутбук ASUS VivoBook",
            quantity=2,
            unit="шт",
            suspicious_fields=[]
        ),
        ReceptionItemCreate(
            article="999",  # Не существует в БД
            name="Несуществующий товар",
            quantity=1,
            unit="шт",
            suspicious_fields=["article"]
        ),
        ReceptionItemCreate(
            article="514",  # Есть в БД, но НЕ требует контроля
            name="Клавиатура Logitech K120",
            quantity=5,
            unit="шт",
            suspicious_fields=[]
        )
    ]
    
    logger.info("Setting items in ResultsWidget...")
    widget.set_items(items)
    
    logger.info("Checking table content...")
    for row in range(widget.rowCount()):
        article = widget.item(row, 0).text()
        db_status = widget.item(row, 5).text()
        tooltip = widget.item(row, 5).toolTip()
        logger.info(f"Row {row}: Article={article}, DB Status={db_status}, Tooltip={tooltip}")
    
    widget.show()
    logger.info("✅ Visual test: Check the 'БД' column for verification icons")
    
    # Don't exec - just show for inspection
    # app.exec()

if __name__ == "__main__":
    test_db_verification()
