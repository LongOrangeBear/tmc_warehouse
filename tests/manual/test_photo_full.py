import sys
import os
import logging
import time
from pathlib import Path
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())

from PySide6.QtWidgets import QApplication
from client.src.services.camera_service import CameraService
from client.src.services.storage_service import StorageService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PHOTO_TEST")

def test_photo_evidence():
    app = QApplication(sys.argv)
    
    camera_service = CameraService()
    storage_service = StorageService()
    
    # 1. Start Camera (Mock Mode)
    logger.info("Starting camera in MOCK mode...")
    camera_service.start_preview(camera_index=-1)
    
    # Wait for camera to warm up and generate frames
    time.sleep(2)
    
    # 2. Take Snapshot
    logger.info("Taking snapshot...")
    jpeg_data = camera_service.take_snapshot()
    
    if jpeg_data:
        logger.info(f"✅ Snapshot captured! Size: {len(jpeg_data)} bytes")
        
        # Verify it looks like a JPEG
        if jpeg_data.startswith(b'\xff\xd8'):
             logger.info("✅ Valid JPEG header detected")
        else:
             logger.error("❌ Invalid JPEG header")
             
        # 3. Save Photo
        reception_id = 999
        item_id = 123
        ttn_date = date.today()
        
        logger.info(f"Saving photo for Reception {reception_id}, Item {item_id}...")
        try:
            path = storage_service.save_photo(jpeg_data, reception_id, ttn_date, item_id)
            logger.info(f"✅ Photo saved to: {path}")
            
            if path.exists() and path.stat().st_size > 0:
                logger.info("✅ File exists and is not empty")
            else:
                logger.error("❌ File verification failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to save photo: {e}")
            
    else:
        logger.error("❌ Failed to capture snapshot (None returned)")
        
    camera_service.stop_preview()
    app.quit()

if __name__ == "__main__":
    test_photo_evidence()
