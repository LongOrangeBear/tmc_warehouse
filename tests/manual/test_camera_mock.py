import sys
import os
import time
import logging
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from client.src.services.camera_service import CameraService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CAMERA_TEST")

def test_mock_camera():
    app = QApplication(sys.argv)
    
    service = CameraService()
    
    # Force mock mode by setting index to -1 (or ensuring no camera exists)
    # The updated logic automatically switches to mock if index 0 fails
    
    output_dir = Path("test_video_output")
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    
    def on_frame(image):
        logger.info(f"Frame received: {image.width()}x{image.height()}")

    def on_error(msg):
        logger.error(f"Camera error: {msg}")

    service.frame_ready.connect(on_frame)
    service.error.connect(on_error)
    
    logger.info("Starting preview...")
    service.start_preview(camera_index=-1) # Explicitly request mock
    
    # Record for 3 seconds
    def start_rec():
        logger.info("Starting recording...")
        service.start_recording(output_dir)
        
    def stop_rec():
        logger.info("Stopping recording...")
        path = service.stop_recording()
        logger.info(f"Video saved to: {path}")
        service.stop_preview()
        app.quit()

    QTimer.singleShot(1000, start_rec)
    QTimer.singleShot(4000, stop_rec)
    
    app.exec()
    
    # Verify file exists
    files = list(output_dir.glob("*.avi"))
    if files:
        logger.info(f"✅ SUCCESS: Video file created: {files[0]}")
        logger.info(f"File size: {files[0].stat().st_size} bytes")
    else:
        logger.error("❌ FAILED: No video file created")

if __name__ == "__main__":
    test_mock_camera()
