"""
QR KOD TEST SCRIPTI
pyzbar çalışıyor mu kontrol et
"""

import cv2
from pyzbar.pyzbar import decode
import sys

print("="*60)
print("🔍 QR KOD TEST")
print("="*60)

# Test 1: Kameradan canlı okuma
print("\n1️⃣ CANLI KAMERA TESTİ")
print("QR kodu kameraya göster, ESC ile çık")
print("-"*60)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("❌ Kamera açılamadı!")
    sys.exit(1)

# Çözünürlük artır
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("✅ Kamera açıldı - QR kodu göster...")

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    
    # QR kod oku
    qr_codes = decode(frame)
    
    if qr_codes:
        for qr in qr_codes:
            data = qr.data.decode('utf-8')
            points = qr.polygon
            
            # Çiz
            if len(points) == 4:
                pts = [(point.x, point.y) for point in points]
                for i in range(4):
                    cv2.line(frame, pts[i], pts[(i+1) % 4], (0, 255, 0), 3)
            
            # Yazı
            cv2.putText(frame, f"QR: {data}", (10, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            print(f"✅ QR OKUNDU! Data: {data}")
    else:
        # Okunamadı mesajı
        if frame_count % 30 == 0:
            print(f"⚠️  Frame {frame_count}: QR kod bulunamadı")
    
    cv2.imshow("QR Test - ESC ile cik", frame)
    
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*60)
print("Test tamamlandı!")
print("="*60)