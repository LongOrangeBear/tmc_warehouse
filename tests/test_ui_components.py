"""Test UI components instantiation."""
import sys
from PySide6.QtWidgets import QApplication
from client.src.ui import (
    VideoWidget, ResultsWidget, DocumentDialog, 
    ControlDialog, HistoryDialog
)
from common.models import ReceptionRead, ReceptionStatus
from datetime import datetime

def test_ui_components():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # 1. VideoWidget
    video = VideoWidget()
    assert video is not None
    print("VideoWidget OK")
    
    # 2. ResultsWidget
    results = ResultsWidget()
    assert results is not None
    print("ResultsWidget OK")
    
    # 3. DocumentDialog
    # Mock services to avoid real calls during init if any
    # But our init mostly sets up UI, services are called on actions
    doc_dialog = DocumentDialog()
    assert doc_dialog is not None
    print("DocumentDialog OK")
    
    # 4. ControlDialog
    # Needs a reception object
    reception = ReceptionRead(
        id=1,
        ttn_number="TEST",
        ttn_date=datetime.now().date(),
        supplier="Test",
        status=ReceptionStatus.PENDING,
        created_at=datetime.now(),
        items=[
            {
                "id": 1, "reception_id": 1, "article": "A1", "name": "Test Item", 
                "quantity": 10, "unit": "pcs", "control_required": True, 
                "control_status": "pending"
            }
        ]
    )
    ctrl_dialog = ControlDialog(reception)
    assert ctrl_dialog is not None
    print("ControlDialog OK")
    
    # 5. HistoryDialog
    hist_dialog = HistoryDialog()
    assert hist_dialog is not None
    print("HistoryDialog OK")
    
    print("All UI components instantiated successfully")

if __name__ == "__main__":
    test_ui_components()
