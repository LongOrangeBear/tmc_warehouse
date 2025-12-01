import asyncio
import logging
import sys
import os
import time
import threading
import uvicorn
import requests
from pathlib import Path
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from client.src.services.sync_service import SyncService
from common.models import ReceptionCreate, ReceptionItemCreate, ReceptionItemControlUpdate, ControlStatus, ControlType
from server.src.db.models import Reception, ReceptionItem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("INTEGRATION_TEST")

# Server configuration
HOST = "127.0.0.1"
PORT = 8001
BASE_URL = f"http://{HOST}:{PORT}/api/v1"

def run_server():
    """Run server in a separate thread."""
    logger.info("Starting server...")
    uvicorn.run("server.src.main_server:app", host=HOST, port=PORT, log_level="error")

def wait_for_server():
    """Wait for server to be ready."""
    for _ in range(10):
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                logger.info("Server is ready!")
                return True
        except:
            pass
        time.sleep(1)
    return False

def test_integration():
    # 1. Start Server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    if not wait_for_server():
        logger.error("❌ Server failed to start")
        return

    # 2. Initialize Client Service
    # Override config to point to test server
    os.environ["SERVER_URL"] = BASE_URL
    sync_service = SyncService()
    sync_service.base_url = BASE_URL # Force override
    
    # 3. Create Reception (Simulate OCR result)
    logger.info("Creating reception...")
    
    # Item that requires control (from seed_db)
    item1 = ReceptionItemCreate(
        article="512",
        name="Ноутбук ASUS VivoBook",
        quantity=5,
        unit="шт",
        suspicious_fields=[]
    )
    
    # Item that does NOT require control
    item2 = ReceptionItemCreate(
        article="514",
        name="Клавиатура Logitech K120",
        quantity=10,
        unit="шт",
        suspicious_fields=[]
    )
    
    reception_data = ReceptionCreate(
        ttn_number="TEST-INTEGRATION-001",
        ttn_date=date.today(),
        supplier="Test Supplier LLC",
        items=[item1, item2]
    )
    
    try:
        reception = sync_service.create_reception(reception_data)
        logger.info(f"✅ Reception created: ID={reception.id}")
        
        # Verify items in DB/Response
        items_map = {item.article: item for item in reception.items}
        
        # Check Item 1 (Requires Control)
        r_item1 = items_map.get("512")
        if r_item1 and r_item1.control_required:
            logger.info(f"✅ Item 512 correctly marked as control_required")
            logger.info(f"   Control Type: {r_item1.control_type}")
            logger.info(f"   Control Params: {r_item1.control_params}")
        else:
            logger.error("❌ Item 512 should require control!")
            
        # Check Item 2 (No Control)
        r_item2 = items_map.get("514")
        if r_item2 and not r_item2.control_required:
            logger.info(f"✅ Item 514 correctly marked as NO control")
        else:
            logger.error("❌ Item 514 should NOT require control!")
            
        # 4. Submit Control Result
        logger.info("Submitting control result for Item 512...")
        
        control_update = ReceptionItemControlUpdate(
            id=r_item1.id,
            control_status=ControlStatus.PASSED,
            control_result={"passed": True, "checked_by": "tester"},
            notes="All good"
        )
        
        updated_reception = sync_service.send_control_results(reception.id, [control_update])
        
        # Verify update
        updated_item1 = next(i for i in updated_reception.items if i.id == r_item1.id)
        if updated_item1.control_status == ControlStatus.PASSED:
            logger.info("✅ Control status updated to PASSED on server")
        else:
            logger.error(f"❌ Control status mismatch: {updated_item1.control_status}")
            
        # Verify Reception Status (Should be COMPLETED as all control items are done)
        if updated_reception.status == "completed": # ReceptionStatus.COMPLETED
             logger.info("✅ Reception status updated to COMPLETED")
        else:
             logger.error(f"❌ Reception status mismatch: {updated_reception.status}")

    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        raise

if __name__ == "__main__":
    test_integration()
