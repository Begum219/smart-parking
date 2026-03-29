import cv2

print("Bağlı kameraları test ediyor...\n")

# 0-5 arasında kamera ID'lerini test et
for i in range(5):
    cap = cv2.VideoCapture(i)
    
    if cap.isOpened():
        print(f"✓ Kamera {i} BULUNDU!")
        
        # Test frame al
        ret, frame = cap.read()
        if ret:
            print(f"  - Çözünürlük: {frame.shape[1]}x{frame.shape[0]}")
            print(f"  - Bilgisayarındaki kamera bu!")
        
        cap.release()
        print()
    else:
        print(f"✗ Kamera {i} bulunamadı")

print("\nEn düşük ID'li kamera ('parking_detection_system.py'de kullanılacak)")