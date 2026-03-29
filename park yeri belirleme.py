import cv2
import json
import numpy as np
from pathlib import Path

class ParkingCoordinateTool:
    def __init__(self, image_path):
        self.image = cv2.imread(image_path)
        self.original_image = self.image.copy()
        self.parking_spaces = []
        self.current_polygon = []
        self.current_id = 1
        self.drawing = False
        self.window_name = "Park Yeri Koordinat Belirleme"
        
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_color = (0, 255, 0)
        self.thickness = 1
        
        self.point_color = (0, 255, 0)
        self.line_color = (255, 0, 0)
        self.polygon_color = (0, 255, 255)
        self.point_radius = 5
        
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_polygon.append([x, y])
            print(f"Nokta {len(self.current_polygon)} eklendi: ({x}, {y})")
            print(f"💾 Devam etmek için SAĞ TIK YAP!")
            self.draw_current_state()
            
        elif event == cv2.EVENT_RBUTTONDOWN:
            if len(self.current_polygon) >= 3:
                self.parking_spaces.append({
                    "id": self.current_id,
                    "coordinates": self.current_polygon.copy(),
                    "name": f"Park Yeri {self.current_id}"
                })
                print(f"\n{'='*50}")
                print(f"✓✓✓ Park Yeri {self.current_id} KAYDEDILDI! ✓✓✓")
                print(f"{'='*50}")
                print(f"Koordinatlar: {self.current_polygon}")
                print(f"👉 Sonraki park yerine geçebilirsin...\n")
                
                self.current_id += 1
                self.current_polygon = []
                self.draw_current_state()
            else:
                print(f"⚠ HATA! Şu anda {len(self.current_polygon)} nokta var.")
                print(f"⚠ En az 3 nokta gerekli! Devam et...")
                self.draw_current_state()
                
        elif event == cv2.EVENT_MBUTTONDOWN:
            if self.current_polygon:
                removed = self.current_polygon.pop()
                print(f"Son nokta silindi: {removed}")
                self.draw_current_state()
    
    def draw_current_state(self):
        self.image = self.original_image.copy()
        
        for space in self.parking_spaces:
            coords = np.array(space['coordinates'], dtype=np.int32)
            cv2.polylines(self.image, [coords], True, self.polygon_color, 2)
            overlay = self.image.copy()
            cv2.fillPoly(overlay, [coords], (0, 255, 255))
            cv2.addWeighted(overlay, 0.1, self.image, 0.9, 0, self.image)
            
            M = cv2.moments(coords)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(self.image, str(space['id']), (cx, cy),
                           self.font, self.font_scale, (0, 0, 255), 2)
        
        if len(self.current_polygon) > 0:
            for point in self.current_polygon:
                cv2.circle(self.image, tuple(point), self.point_radius, 
                          self.point_color, -1)
            
            if len(self.current_polygon) > 1:
                for i in range(len(self.current_polygon) - 1):
                    cv2.line(self.image, tuple(self.current_polygon[i]),
                            tuple(self.current_polygon[i + 1]),
                            self.line_color, 2)
            
            if len(self.current_polygon) > 2:
                cv2.line(self.image, tuple(self.current_polygon[-1]),
                        tuple(self.current_polygon[0]),
                        (100, 100, 255), 1)
        
        info_text = [
            f"PARK YERLERİ: {len(self.parking_spaces)} | MEVCUT NOKTALAR: {len(self.current_polygon)}",
            "ADIM 1: Sol tık ile 4 köşeye noktalar koy",
            "ADIM 2: Sağ tık yap -> Park yeri kaydedilir",
            "SPACE: Temizle | S: Kaydet | ESC: Çıkış"
        ]
        
        y_offset = 30
        for text in info_text:
            cv2.putText(self.image, text, (10, y_offset),
                       self.font, 0.5, (255, 255, 255), 1)
            y_offset += 25
        
        cv2.imshow(self.window_name, self.image)
    
    def save_to_json(self, output_path="parking_coordinates.json"):
        output_data = {
            "parking_lot": {
                "total_spaces": len(self.parking_spaces),
                "spaces": self.parking_spaces
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Koordinatlar '{output_path}' olarak kaydedildi!")
        return output_data
    
    def run(self):
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        print("\n" + "="*60)
        print("PARK YERİ KOORDİNAT BELİRLEME ARACI")
        print("="*60)
        print("\nKULLANIM:")
        print("  • SOL TIKLA: Polygon noktası ekle")
        print("  • SAG TIKLA: Park yerini tamamla (min 3 nokta)")
        print("  • ORTA TIKLA: Son noktayı sil")
        print("  • SPACE: Mevcut çizimi temizle")
        print("  • S: JSON olarak kaydet")
        print("  • ESC: Çıkış")
        print("="*60 + "\n")
        
        self.draw_current_state()
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:
                print("\nÇıkılıyor...")
                break
            elif key == ord('s') or key == ord('S'):
                self.save_to_json()
            elif key == ord(' '):
                if len(self.current_polygon) > 0:
                    self.current_polygon = []
                    print("Çizim temizlendi!")
                    self.draw_current_state()
        
        cv2.destroyAllWindows()
        
        if len(self.parking_spaces) > 0:
            self.save_to_json()
            print(f"\nToplam {len(self.parking_spaces)} park yeri kaydedildi.")


if __name__ == "__main__":
    IMAGE_PATH = r"C:\Users\w11\Desktop\SmartParking\foto5.jpg"
    
    if not Path(IMAGE_PATH).exists():
        print(f"❌ Hata: '{IMAGE_PATH}' dosyası bulunamadı!")
        print("Lütfen resim dosyasını kontrol edin.")
    else:
        tool = ParkingCoordinateTool(IMAGE_PATH)
        tool.run()