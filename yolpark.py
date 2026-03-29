import cv2
import json
import numpy as np
from pathlib import Path

class MultiCameraParkingCoordinateTool:
    def __init__(self, camera_id, camera_name, image_path, start_space_name="A1"):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        
        if self.image is None:
            raise ValueError(f"❌ Görüntü yüklenemedi: {image_path}")
        
        self.original_image = self.image.copy()
        self.parking_spaces = []
        self.road_zones = []  # ⬅️ YENİ: Yol/yasak alanlar
        self.current_polygon = []
        
        # Park yeri isimlendirme (A1, A2, B1, B2...)
        self.start_space_name = start_space_name
        self.current_space_name = start_space_name
        
        # Mod: "parking" veya "road"
        self.mode = "parking"  # ⬅️ YENİ: Varsayılan park yeri modu
        
        self.drawing = False
        self.window_name = f"Kamera {camera_id}: {camera_name}"
        
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.5
        self.font_color = (0, 255, 0)
        self.thickness = 1
        
        self.point_color = (0, 255, 0)
        self.line_color = (255, 0, 0)
        self.polygon_color = (0, 255, 255)
        self.point_radius = 5
        
    def increment_space_name(self):
        """A1 -> A2 -> A3 ... A8 -> B1 -> B2 ..."""
        letter = self.current_space_name[0]
        num = int(self.current_space_name[1:])
        
        num += 1
        if num > 8:  # 8'den sonra sonraki harfe geç
            letter = chr(ord(letter) + 1)  # A->B, B->C
            num = 1
        
        self.current_space_name = f"{letter}{num}"
        
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_polygon.append([x, y])
            print(f"📍 Nokta {len(self.current_polygon)} eklendi: ({x}, {y})")
            self.draw_current_state()
            
        elif event == cv2.EVENT_RBUTTONDOWN:
            if len(self.current_polygon) >= 3:
                if self.mode == "parking":
                    # Park yeri kaydet
                    self.parking_spaces.append({
                        "space_id": self.current_space_name,
                        "coordinates": self.current_polygon.copy()
                    })
                    print(f"\n{'='*50}")
                    print(f"✅ Park Yeri {self.current_space_name} KAYDEDİLDİ!")
                    print(f"{'='*50}")
                    print(f"Koordinatlar: {self.current_polygon}\n")
                    self.increment_space_name()
                else:
                    # Yol/yasak alan kaydet
                    zone_id = f"ROAD_{len(self.road_zones) + 1}"
                    self.road_zones.append({
                        "zone_id": zone_id,
                        "zone_type": "road",
                        "coordinates": self.current_polygon.copy()
                    })
                    print(f"\n{'='*50}")
                    print(f"🚫 YOL ALANI {zone_id} KAYDEDİLDİ!")
                    print(f"{'='*50}")
                    print(f"Koordinatlar: {self.current_polygon}\n")
                
                self.current_polygon = []
                self.draw_current_state()
            else:
                print(f"⚠️  En az 3 nokta gerekli! (Şu an: {len(self.current_polygon)})")
                
        elif event == cv2.EVENT_MBUTTONDOWN:
            if self.current_polygon:
                removed = self.current_polygon.pop()
                print(f"🗑️  Son nokta silindi: {removed}")
                self.draw_current_state()
    
    def draw_current_state(self):
        self.image = self.original_image.copy()
        
        # Kaydedilmiş park yerlerini çiz (MAVİ)
        for space in self.parking_spaces:
            coords = np.array(space['coordinates'], dtype=np.int32)
            cv2.polylines(self.image, [coords], True, (255, 255, 0), 2)  # Cyan
            
            overlay = self.image.copy()
            cv2.fillPoly(overlay, [coords], (255, 255, 0))
            cv2.addWeighted(overlay, 0.1, self.image, 0.9, 0, self.image)
            
            M = cv2.moments(coords)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(self.image, space['space_id'], (cx, cy),
                           self.font, 0.7, (0, 255, 0), 2)
        
        # Kaydedilmiş yol alanlarını çiz (KIRMIZI)
        for zone in self.road_zones:
            coords = np.array(zone['coordinates'], dtype=np.int32)
            cv2.polylines(self.image, [coords], True, (0, 0, 255), 2)  # Kırmızı
            
            overlay = self.image.copy()
            cv2.fillPoly(overlay, [coords], (0, 0, 255))
            cv2.addWeighted(overlay, 0.2, self.image, 0.8, 0, self.image)
            
            M = cv2.moments(coords)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(self.image, zone['zone_id'], (cx, cy),
                           self.font, 0.7, (0, 0, 255), 2)
        
        # Şu anki çizim
        if len(self.current_polygon) > 0:
            color = (255, 0, 0) if self.mode == "parking" else (0, 0, 255)
            
            for point in self.current_polygon:
                cv2.circle(self.image, tuple(point), self.point_radius, 
                          color, -1)
            
            if len(self.current_polygon) > 1:
                for i in range(len(self.current_polygon) - 1):
                    cv2.line(self.image, tuple(self.current_polygon[i]),
                            tuple(self.current_polygon[i + 1]),
                            color, 2)
            
            if len(self.current_polygon) > 2:
                cv2.line(self.image, tuple(self.current_polygon[-1]),
                        tuple(self.current_polygon[0]),
                        color, 1)
        
        # Bilgi metni
        mode_text = "PARK YERİ" if self.mode == "parking" else "YOL ALANI"
        mode_color = "(MAVİ)" if self.mode == "parking" else "(KIRMIZI)"
        
        info_text = [
            f"KAMERA: {self.camera_name}",
            f"MOD: {mode_text} {mode_color} | Park: {len(self.parking_spaces)} | Yol: {len(self.road_zones)}",
            f"ŞU AN: {self.current_space_name if self.mode == 'parking' else 'YOL_' + str(len(self.road_zones) + 1)}",
            "M: Mod değiştir | SOL TIK: Nokta | SAĞ TIK: Kaydet | S: Bitir | ESC: Çıkış"
        ]
        
        y_offset = 30
        for text in info_text:
            cv2.putText(self.image, text, (10, y_offset),
                       self.font, 0.5, (255, 255, 255), 1)
            y_offset += 25
        
        cv2.imshow(self.window_name, self.image)
    
    def save_to_json(self, output_path=None):
        if output_path is None:
            output_path = f"camera_{self.camera_id}_coordinates.json"
        
        output_data = {
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "image_path": self.image_path,
            "total_spaces": len(self.parking_spaces),
            "total_road_zones": len(self.road_zones),  # ⬅️ YENİ
            "spaces": self.parking_spaces,
            "road_zones": self.road_zones  # ⬅️ YENİ
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Kamera {self.camera_id} koordinatları '{output_path}' olarak kaydedildi!")
        print(f"   Park yerleri: {len(self.parking_spaces)}")
        print(f"   Yol alanları: {len(self.road_zones)}")
        return output_data
    
    def run(self):
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        print("\n" + "="*60)
        print(f"KAMERA {self.camera_id}: {self.camera_name}")
        print("="*60)
        print("KULLANIM:")
        print("  • M: Mod değiştir (Park Yeri ↔ Yol Alanı) ⭐")
        print("  • SOL TIK: Nokta ekle")
        print("  • SAĞ TIK: Alan kaydet (min 3 nokta)")
        print("  • ORTA TIK: Son noktayı sil")
        print("  • SPACE: Mevcut çizimi temizle")
        print("  • S: Kaydet ve sonraki kameraya geç")
        print("  • ESC: Kaydedip çıkış")
        print("="*60)
        print(f"📍 İlk önce PARK YERLERİNİ işaretle")
        print(f"📍 Sonra M tuşu ile YOL ALANLARI moduna geç")
        print("="*60 + "\n")
        
        self.draw_current_state()
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                print("\n⚠️  ESC tuşuna basıldı - Kaydediliyor...")
                break
            elif key == ord('s') or key == ord('S'):
                self.save_to_json()
                print("\n🎉 S tuşuna basıldı - Sonraki kameraya geçiliyor...")
                break
            elif key == ord('m') or key == ord('M'):  # ⬅️ YENİ: Mod değiştir
                self.mode = "road" if self.mode == "parking" else "parking"
                mode_name = "YOL ALANI (KIRMIZI)" if self.mode == "road" else "PARK YERİ (MAVİ)"
                print(f"\n🔄 Mod değiştirildi: {mode_name}")
                self.draw_current_state()
            elif key == ord(' '):
                if len(self.current_polygon) > 0:
                    self.current_polygon = []
                    print("🗑️  Çizim temizlendi!")
                    self.draw_current_state()
        
        cv2.destroyWindow(self.window_name)  # Sadece bu pencereyi kapat
        
        if len(self.parking_spaces) > 0:
            self.save_to_json()
            print(f"\n✅ Toplam {len(self.parking_spaces)} park yeri kaydedildi.")
        
        return self.parking_spaces


def capture_live_snapshot(camera_id, camera_name, output_filename):
    """Canlı kamera görüntüsünden snapshot çek"""
    print(f"\n📷 {camera_name} açılıyor...")
    print("="*60)
    print("KONTROLLER:")
    print("  • Kamerayı konumlandır")
    print("  • SPACE: Snapshot çek ve koordinat belirlemeye geç")
    print("  • ESC: İptal et")
    print("="*60 + "\n")
    
    cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print(f"❌ Kamera {camera_id} açılamadı!")
        return None
    
    # Kamera ayarları - TESPİT SİSTEMİYLE AYNI ÇÖZÜNÜRLÜK!
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)   # 640 → 1920
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # 480 → 1080
    
    print(f"✅ Kamera çözünürlük: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    
    window_name = f"CANLI: {camera_name}"
    cv2.namedWindow(window_name)
    
    snapshot_frame = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"❌ Frame alınamadı!")
            break
        
        # Bilgi yazısı
        info_text = "SPACE: Snapshot cek | ESC: Iptal"
        cv2.putText(frame, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow(window_name, frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):  # SPACE - Snapshot çek
            snapshot_frame = frame.copy()
            cv2.imwrite(output_filename, snapshot_frame)
            print(f"✅ Snapshot kaydedildi: {output_filename}")
            break
        elif key == 27:  # ESC - İptal
            print(f"⚠️  Snapshot çekme iptal edildi")
            break
    
    cap.release()
    cv2.destroyWindow(window_name)
    
    return snapshot_frame


# ========================================
# ANA PROGRAM
# ========================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SMART PARKING - MULTI KAMERA KOORDİNAT BELİRLEME")
    print("="*60)
    print("\n📋 İŞLEM AKIŞI:")
    print("  1. Kamera 1 açılacak (canlı görüntü)")
    print("  2. SPACE ile snapshot çek")
    print("  3. Park yerlerini işaretle")
    print("  4. S tuşuna bas → Kamera 2'ye geç")
    print("  5. Kamera 2 için aynı işlemler")
    print("="*60 + "\n")
    
    # KAMERA 1: A ve B bölümleri (16 park yeri)
    print("🎥 ADIM 1: KAMERA 1 (A-B Bölümü)")
    print("="*60)
    
    camera1_image = "camera_0_snapshot.jpg"
    snapshot1 = capture_live_snapshot(0, "Kamera 1 (A-B Bölümü)", camera1_image)
    
    if snapshot1 is not None:
        print("\n📐 Koordinat belirleme başlıyor...")
        print("Park yerleri: A1-A8, B1-B8 (16 park yeri)\n")
        
        tool1 = MultiCameraParkingCoordinateTool(
            camera_id=0,
            camera_name="Kamera 1 (A-B Bölümü)",
            image_path=camera1_image,
            start_space_name="A1"
        )
        tool1.run()
        
        # OpenCV event loop'u temizle
        cv2.waitKey(1)
        
        print("\n" + "="*60)
        print("✅ KAMERA 1 TAMAMLANDI!")
        print("="*60)
        print("\n⏳ 1 saniye içinde Kamera 2'ye geçiliyor...")
        import time
        time.sleep(1)
    else:
        print(f"⚠️  Kamera 1 snapshot alınamadı, atlanıyor...")
    
    # KAMERA 2: C bölümü (8 park yeri)
    print("\n🎥 ADIM 2: KAMERA 2 (C Bölümü)")
    print("="*60)
    
    camera2_image = "camera_1_snapshot.jpg"
    snapshot2 = capture_live_snapshot(1, "Kamera 2 (C Bölümü)", camera2_image)
    
    if snapshot2 is not None:
        print("\n📐 Koordinat belirleme başlıyor...")
        print("Park yerleri: C1-C8 (8 park yeri)\n")
        
        tool2 = MultiCameraParkingCoordinateTool(
            camera_id=1,
            camera_name="Kamera 2 (C Bölümü)",
            image_path=camera2_image,
            start_space_name="C1"
        )
        tool2.run()
        
        # OpenCV event loop'u temizle
        cv2.waitKey(1)
    else:
        print(f"⚠️  Kamera 2 snapshot alınamadı, atlanıyor...")
    
    print("\n" + "="*60)
    print("🎉 TÜM KAMERALAR İÇİN KOORDİNATLAR BELİRLENDİ!")
    print("="*60)
    print("Dosyalar:")
    if snapshot1 is not None:
        print("  • camera_0_coordinates.json (Kamera 1)")
    if snapshot2 is not None:
        print("  • camera_1_coordinates.json (Kamera 2)")
    print("="*60 + "\n")