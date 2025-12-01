import cv2
import sys
import platform

def test_camera():
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print(f"OpenCV: {cv2.__version__}")
    
    # List available backends
    backends = [
        ("CAP_ANY", cv2.CAP_ANY),
        ("CAP_DSHOW (Windows)", cv2.CAP_DSHOW),
        ("CAP_MSMF (Windows)", cv2.CAP_MSMF),
        ("CAP_V4L2 (Linux)", cv2.CAP_V4L2),
    ]
    
    print("\nTesting cameras...")
    
    for index in range(5):
        print(f"\n--- Checking Camera Index {index} ---")
        for backend_name, backend_id in backends:
            try:
                cap = cv2.VideoCapture(index, backend_id)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        print(f"✅ SUCCESS: Camera {index} opened with {backend_name}")
                        print(f"   Resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
                        cap.release()
                        return  # Found a working camera
                    else:
                        print(f"⚠️  Opened with {backend_name}, but failed to read frame.")
                    cap.release()
                else:
                    pass # print(f"   Failed with {backend_name}")
            except Exception as e:
                print(f"   Error with {backend_name}: {e}")
                
    print("\n❌ No working camera found on indices 0-4.")

if __name__ == "__main__":
    test_camera()
    input("\nPress Enter to exit...")
