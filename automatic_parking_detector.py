import cv2
import json
import numpy as np
from pathlib import Path

class ParkingGridDetector:
    def __init__(self):
        self.parking_spaces = []
        self.space_id = 1
        
    def capture_from_camera(self, camera_id=1):
        """Kameradan frame yakala"""
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            print("❌ Kamera açılamadı!")
            return False
        
        print("✓ Kamera açıldı")
        print("SPACE: Frame yakala | ESC: Çık\n")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            cv2.imshow("Kamera - SPACE tuşuna bas", frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 32:  # SPACE
                print("Frame yakalandı!")
                cv2.imwrite("parking_frame.jpg", frame)
                print("✓ parking_frame.jpg kaydedildi")
                
                print("\n🔄 Analiz ediliyor...\n")
                self.detect_parking_spaces(frame)
                
                print(f"\n✓ {len(self.parking_spaces)} park yeri tespit edildi!")
                
                if len(self.parking_spaces) > 0:
                    self.visualize_parking_spaces(frame)
                    
                    save = input("\nJSON'a kaydet? (e/h): ")
                    if save.lower() == 'e':
                        self.save_to_json()
                        print("✓ Kaydedildi!")
                
                break
            
            elif key == 27:  # ESC
                print("Çıkılıyor...")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return True
    
    def detect_parking_spaces(self, frame):
        """Izgarayı tespit et - morfoloji ve kontür yöntemi"""
        
        # 1. Gri renge çevir
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 2. Kontrast artır
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # DEBUG: Gri görüntüyü göster
        cv2.imshow("DEBUG: Gray", gray)
        
        # 3. Siyah çizgileri tespit et (ters threshold)
        # Siyah çizgiler 0-100 aralığında, beyaz boşluklar 200-255
        _, binary = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
        
        cv2.imshow("DEBUG: Binary (Siyah Çizgiler)", binary)
        
        # 4. Morfolojik işlemler
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        
        cv2.imshow("DEBUG: Morfoloji", binary)
        
        # 5. Yatay çizgileri ayıkla
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 2))
        h_lines = cv2.morphologyEx(binary.copy(), cv2.MORPH_OPEN, h_kernel)
        
        cv2.imshow("DEBUG: Yatay Cizgiler", h_lines)
        
        # 6. Dikey çizgileri ayıkla
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 50))
        v_lines = cv2.morphologyEx(binary.copy(), cv2.MORPH_OPEN, v_kernel)
        
        cv2.imshow("DEBUG: Dikey Cizgiler", v_lines)
        
        # 7. Yatay çizgilerin Y koordinatlarını bul
        h_positions = []
        contours_h, _ = cv2.findContours(h_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours_h:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 50:  # Yeterince geniş
                h_positions.append(y + h // 2)
        
        h_positions = sorted(set(h_positions))
        
        print(f"  Yatay çizgiler (ham): {len(h_positions)} -> {h_positions}")
        
        # 8. Dikey çizgilerin X koordinatlarını bul
        v_positions = []
        contours_v, _ = cv2.findContours(v_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours_v:
            x, y, w, h = cv2.boundingRect(cnt)
            if h > 50:  # Yeterince uzun
                v_positions.append(x + w // 2)
        
        v_positions = sorted(set(v_positions))
        
        print(f"  Dikey çizgiler (ham): {len(v_positions)} -> {v_positions}")
        
        # 9. Yakın çizgileri birleştir
        h_positions = self.merge_close_positions(h_positions, threshold=50)
        v_positions = self.merge_close_positions(v_positions, threshold=50)
        
        print(f"  Temizlenmiş yatay: {len(h_positions)} -> {h_positions}")
        print(f"  Temizlenmiş dikey: {len(v_positions)} -> {v_positions}")
        
        # 10. Park yerlerini oluştur
        self.parking_spaces = []
        self.space_id = 1
        
        if len(h_positions) >= 2 and len(v_positions) >= 2:
            for i in range(len(h_positions) - 1):
                for j in range(len(v_positions) - 1):
                    y1 = h_positions[i]
                    y2 = h_positions[i + 1]
                    x1 = v_positions[j]
                    x2 = v_positions[j + 1]
                    
                    width = x2 - x1
                    height = y2 - y1
                    
                    if width > 40 and height > 40:  # Minimum boyut
                        coordinates = [
                            [x1, y1],
                            [x2, y1],
                            [x2, y2],
                            [x1, y2]
                        ]
                        
                        self.parking_spaces.append({
                            "id": self.space_id,
                            "coordinates": coordinates,
                            "name": f"Park Yeri {self.space_id}"
                        })
                        self.space_id += 1
        else:
            print("  ⚠ Yeterli çizgi tespit edilemedi!")
    
    def merge_close_positions(self, positions, threshold=50):
        """Çok yakın pozisyonları birleştir"""
        if not positions:
            return positions
        
        merged = [positions[0]]
        for pos in positions[1:]:
            if abs(pos - merged[-1]) > threshold:
                merged.append(pos)
        
        return merged
    
    def visualize_parking_spaces(self, frame):
        """Park yerlerini göster"""
        display = frame.copy()
        
        for space in self.parking_spaces:
            coords = np.array(space['coordinates'], dtype=np.int32)
            cv2.polylines(display, [coords], True, (0, 255, 255), 2)
            
            x, y = coords[0]
            cv2.putText(display, str(space['id']), (x + 5, y + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        info = f"Toplam Park Yeri: {len(self.parking_spaces)}"
        cv2.putText(display, info, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.imshow("Tespit Edilen Park Yerleri", display)
        cv2.waitKey(0)
    
    def save_to_json(self, output_path="parking_coordinates.json"):
        """Koordinatları JSON'a kaydet"""
        if len(self.parking_spaces) == 0:
            print("⚠ Kaydedilecek park yeri yok!")
            return
        
        output_data = {
            "parking_lot": {
                "total_spaces": len(self.parking_spaces),
                "spaces": self.parking_spaces
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ {len(self.parking_spaces)} park yeri '{output_path}'a kaydedildi!")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PARK YERİ OTOMATIK TESPİTİ (Morfoloji)")
    print("="*60 + "\n")
    
    detector = ParkingGridDetector()
    detector.capture_from_camera(camera_id=1)