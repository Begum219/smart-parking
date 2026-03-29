import cv2

def find_cameras():
    """Bağlı kameraları tespit eder"""
    available_cameras = []
    
    for i in range(10):  # 0-9 arası dene
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"✅ Kamera {i} bulundu!")
            available_cameras.append(i)
            cap.release()
        else:
            print(f"❌ Kamera {i} yok")
    
    return available_cameras

# Test et
cameras = find_cameras()
print(f"\n📷 Toplam {len(cameras)} kamera bulundu: {cameras}")