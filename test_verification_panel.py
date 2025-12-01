"""Simple test for DocumentDialog verification panel."""
import sys
import os

sys.path.append(os.getcwd())

from PySide6.QtWidgets import QApplication
from client.src.ui.document_dialog import DocumentDialog

def test_verification_panel():
    """Test that the verification panel displays correctly."""
    app = QApplication(sys.argv)
    
    dialog = DocumentDialog()
    
    # Check that verification panel exists
    assert hasattr(dialog, 'verification_panel'), "verification_panel missing"
    assert hasattr(dialog, 'product_info_label'), "product_info_label missing"
    assert hasattr(dialog, 'instructions_label'), "instructions_label missing"
    assert hasattr(dialog, 'mark_verified_btn'), "mark_verified_btn missing"
    
    print("✅ Verification panel structure is correct")
    
    # Show dialog for visual inspection
    dialog.show()
    print("✅ Dialog displayed successfully")
    print("👀 Visual inspection: should see 3 panels (Preview | Form+Table | Verification)")
    
    # Don't exec - just test structure
    # app.exec()

if __name__ == "__main__":
    test_verification_panel()
