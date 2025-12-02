import asyncio
import logging
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from client.src.services.ocr_service import OCRService
from client.src.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("OCR_TEST")

async def test_all_files():
    ocr_service = OCRService()
    test_dir = Path("test_data")
    
    if not test_dir.exists():
        logger.error("test_data directory not found!")
        return

    files = sorted([f for f in test_dir.iterdir() if f.is_file()])
    
    logger.info(f"Found {len(files)} files in test_data")
    logger.info("="*60)

    results = []

    for file_path in files:
        logger.info(f"📄 Processing: {file_path.name}")
        try:
            # Process document
            result = ocr_service.process_document(file_path)
            
            # Print summary
            logger.info(f"  ✅ TTN: {result.ttn_number}")
            logger.info(f"  ✅ Date: {result.ttn_date}")
            logger.info(f"  ✅ Supplier: {result.supplier}")
            logger.info(f"  📦 Items found: {len(result.items)}")
            
            for i, item in enumerate(result.items, 1):
                logger.info(f"    {i}. [{item.article}] {item.name[:40]}... | {item.quantity} {item.unit}")
            
            results.append({
                "file": file_path.name,
                "status": "SUCCESS",
                "items": len(result.items),
                "ttn": result.ttn_number
            })
            
        except Exception as e:
            logger.error(f"  ❌ FAILED: {e}")
            results.append({
                "file": file_path.name,
                "status": "FAILED",
                "error": str(e)
            })
        
        logger.info("-" * 60)

    # Final Summary
    logger.info("\n" + "="*60)
    logger.info("📊 FINAL SUMMARY")
    logger.info("="*60)
    for res in results:
        status_icon = "✅" if res["status"] == "SUCCESS" else "❌"
        details = f"{res['items']} items, TTN: {res.get('ttn')}" if res["status"] == "SUCCESS" else f"Error: {res.get('error')}"
        logger.info(f"{status_icon} {res['file']:<20} | {details}")

if __name__ == "__main__":
    asyncio.run(test_all_files())
