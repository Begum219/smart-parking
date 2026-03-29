import cv2
import json
import numpy as np
import requests
from datetime import datetime
from ultralytics import YOLO
from pyzbar.pyzbar import decode
import pytesseract
from pathlib import Path

class ParkingDetectionSystem:
    def __init__(self, parking_coords_path, tesseract_path=None, api_url="http://localhost:5000"):
        """
        Parametreler:
        - parking_coords_path: JSON dosyasının yolu
        - tesseract_path: Tesseract kurulum yolu (Windows için gerekli)
        - api_url: .NET Backend API URL'si
        """
        
        self.api_url = api_url  # ⬅️ API URL
        
        # Tesseract yolunu ayarla (Windows için)
        if tesseract_path:
            pytesseract.pytesseract.pytesseract_cmd = tesseract_path
        
        # Park yeri koordinatlarını yükle
        with open(parking_coords_path, 'r', encoding='utf-8') as f:
            self.parking_data = json.load(f)
        
        self.parking_spaces = self.parking_data['parking_lot']['spaces']
        print(f"✓ {len(self.parking_spaces)} park yeri yüklendi")
        
        # YOLO modelini yükle
        print("🔄 YOLO modelini yükle...")
        self.model = YOLO('yolov8n.pt')  # nano model (hızlı)
        print("✓ YOLO modeli hazır")
        
        # Sınıf adları (COCO dataset)
        self.class_names = self.model.names
        
        # İşaret renkleri
        self.vehicle_color = (0, 255, 0)  # Yeşil
        self.detected_color = (0, 0, 255)  # Kırmızı
        self.plate_color = (255, 0, 0)    # Mavi
        self.qr_color = (0, 255, 255)     # Sarı - QR kod
        
        # TRACKING: Araçları izlemek için
        self.tracked_vehicles = {}  # {vehicle_id: {...}}
        self.next_vehicle_id = 1
        self.max_distance = 100  # Piksel (tracking mesafesi)
        
        # API gönderme timer
        self.last_api_send = {}
        self.api_send_interval = 3  # 3 saniyede bir gönder
        
        # API bağlantısını test et
        self.test_api_connection()
        
    def test_api_connection(self):
        """API bağlantısını test et"""
        try:
            response = requests.get(f"{self.api_url}/api/parking/status", timeout=5)
            if response.status_code == 200:
                print(f"✓ .NET API bağlantısı başarılı: {self.api_url}")
            else:
                print(f"⚠ API yanıt verdi ama status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ .NET API bağlantı kurulamadı: {self.api_url}")
            print("   Kontrol et: API çalışıyor mu? URL doğru mu?")
        except Exception as e:
            print(f"⚠ API test hatası: {e}")
    
    def send_to_api(self, vehicle_data):
        """Tespit edilen araçları .NET API'ye gönder"""
        vehicle_id = vehicle_data['vehicle_id']
        
        # Aynı araçı çok sık gönderme
        import time
        now = time.time()
        if vehicle_id in self.last_api_send:
            if now - self.last_api_send[vehicle_id] < self.api_send_interval:
                return
        
        try:
            # Payload hazırla
            payload = {
                "vehicleId": vehicle_data['vehicle_id'],
                "parkingSpaceId": vehicle_data['parking_space_id'],
                "parkingSpaceName": vehicle_data['parking_space_name'],
                "qrCode": vehicle_data['qr'] if vehicle_data['qr'] else None,
                "plateNumber": vehicle_data['plate'] if vehicle_data['plate'] else None,
                "confidence": float(vehicle_data['confidence']),
                "framesDetected": vehicle_data['frames'],
                "detectionTime": datetime.now().isoformat(),
                "status": "occupied"
            }
            
            # POST isteği
            response = requests.post(
                f"{self.api_url}/api/parking/detect",
                json=payload,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                print(f"  ✓ Araç {vehicle_id} .NET API'ye gönderildi")
                self.last_api_send[vehicle_id] = now
            else:
                print(f"  ⚠ API hata ({response.status_code}): {response.text[:100]}")
        
        except requests.exceptions.Timeout:
            print(f"  ⚠ .NET API timeout")
        except requests.exceptions.ConnectionError:
            print(f"  ⚠ .NET API bağlantı kurulamadı")
        except Exception as e:
            print(f"  ⚠ API gönderme hatası: {e}")
        
    def get_centroid(self, bbox):
        """Bounding box'ın merkezini al"""
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        return (cx, cy)
    
    def distance(self, p1, p2):
        """İki nokta arasındaki mesafe"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def track_vehicle(self, bbox, space_id, space_name, plate_text, confidence):
        """Aracı takip et veya yeni ID ata"""
        centroid = self.get_centroid(bbox)
        
        closest_id = None
        closest_dist = self.max_distance
        
        for vehicle_id, vehicle_data in list(self.tracked_vehicles.items()):
            dist = self.distance(centroid, vehicle_data['centroid'])
            
            if dist < closest_dist:
                closest_dist = dist
                closest_id = vehicle_id
        
        if closest_id is not None:
            # Mevcut araçı güncelle
            self.tracked_vehicles[closest_id]['centroid'] = centroid
            self.tracked_vehicles[closest_id]['space_id'] = space_id
            self.tracked_vehicles[closest_id]['space_name'] = space_name
            self.tracked_vehicles[closest_id]['plate'] = plate_text
            self.tracked_vehicles[closest_id]['confidence'] = confidence
            self.tracked_vehicles[closest_id]['frames'] += 1
            
            return closest_id, self.tracked_vehicles[closest_id]
        else:
            # Yeni araç
            vehicle_id = self.next_vehicle_id
            self.next_vehicle_id += 1
            
            self.tracked_vehicles[vehicle_id] = {
                'centroid': centroid,
                'space_id': space_id,
                'space_name': space_name,
                'plate': plate_text,
                'confidence': confidence,
                'frames': 1
            }
            
            return vehicle_id, self.tracked_vehicles[vehicle_id]
        
    def point_in_polygon(self, point, polygon):
        """Noktanın polygon içinde olup olmadığını kontrol et"""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def find_parking_space(self, bbox):
        """
        Bounding box'ı hangi park yerine ait olduğunu bul
        bbox: [x1, y1, x2, y2]
        """
        # Bounding box merkezini hesapla
        center = self.get_centroid(bbox)
        
        # Her park yeri için kontrol et
        for space in self.parking_spaces:
            polygon = space['coordinates']
            if self.point_in_polygon(center, polygon):
                return space['id'], space['name']
        
        return None, None
    
    def read_qr_code(self, frame, bbox):
        """Araç bounding box'ı içindeki QR kodları oku"""
        x1, y1, x2, y2 = bbox
        
        # Araç bölgesini çıkar
        vehicle_region = frame[y1:y2, x1:x2]
        
        if vehicle_region.size == 0:
            return ""
        
        try:
            # QR kodları decode et
            qr_codes = decode(vehicle_region)
            
            if qr_codes:
                # İlk QR kodun datası
                qr_data = qr_codes[0].data.decode('utf-8')
                return qr_data
        except Exception as e:
            pass
        
        return ""
    
    def extract_plate_region(self, frame, bbox):
        """
        Araç bounding box'ından plaka bölgesini çıkar
        bbox: [x1, y1, x2, y2]
        """
        x1, y1, x2, y2 = bbox
        
        # Plaka genelde araçın alt kısmında
        # Yüksekliğin alt %30'unu al
        height = y2 - y1
        plate_y1 = int(y2 - height * 0.3)
        plate_y2 = y2
        
        # Bölgeyi çıkar
        plate_region = frame[plate_y1:plate_y2, x1:x2]
        return plate_region
    
    def read_plate(self, plate_region):
        """OCR ile plakayı oku"""
        if plate_region.size == 0:
            return ""
        
        # Görüntüyü ön işle
        gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
        
        # Kontrast artır
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Thresholding
        _, binary = cv2.threshold(enhanced, 150, 255, cv2.THRESH_BINARY)
        
        # OCR
        try:
            text = pytesseract.image_to_string(binary, 
                                               config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            return text.strip()
        except:
            return ""
    
    def run_camera(self, camera_id=0, confidence_threshold=0.5):
        """Kameradan canlı tespit yap"""
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            print("❌ Kamera açılamadı!")
            return
        
        print(f"✓ Kamera açıldı")
        print(f"✓ .NET API: {self.api_url}")
        print("\nKontroller:")
        print("  S: Ekran görüntüsü kaydet")
        print("  ESC: Çıkış")
        print("\n" + "="*60)
        
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Frame alınamadı")
                break
            
            frame_count += 1
            
            # YOLO deteksiyonu
            results = self.model(frame, conf=confidence_threshold, verbose=False)
            
            # Detaylı çıktı (her 30 frame'de bir)
            if frame_count % 30 == 0:
                print(f"\n📹 Frame {frame_count}")
            
            detected_vehicles = []
            
            # Sonuçları işle
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Bounding box koordinatları
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # Sınıf ID
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Araç ise (COCO'da araçlar: 2=car, 5=bus, 7=truck)
                    if class_id in [2, 5, 7]:
                        # Park yerini bul
                        space_id, space_name = self.find_parking_space([x1, y1, x2, y2])
                        
                        # QR KOD OKUMA
                        qr_data = self.read_qr_code(frame, [x1, y1, x2, y2])
                        
                        # Eğer QR kod okunamazsa OCR dene
                        plate_text = qr_data if qr_data else ""
                        if not plate_text:
                            plate_region = self.extract_plate_region(frame, [x1, y1, x2, y2])
                            plate_text = self.read_plate(plate_region)
                        
                        # Araçı takip et
                        vehicle_id, vehicle_data = self.track_vehicle(
                            [x1, y1, x2, y2], space_id, space_name, plate_text, confidence
                        )
                        
                        vehicle_info = {
                            'vehicle_id': vehicle_id,
                            'bbox': [x1, y1, x2, y2],
                            'parking_space_id': space_id,
                            'parking_space_name': space_name,
                            'plate': plate_text,
                            'qr': qr_data,
                            'confidence': confidence,
                            'frames': vehicle_data['frames']
                        }
                        detected_vehicles.append(vehicle_info)
                        
                        # ⬇️ API'YE GÖNDER ⬇️
                        self.send_to_api(vehicle_info)
                        # ⬆️ ⬆️ ⬆️
                        
                        # Ekrana çiz
                        # Bounding box
                        color = self.vehicle_color
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # Vehicle ID
                        cv2.putText(frame, f"ID:{vehicle_id}", (x1, y1 - 50),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                        
                        # Park yeri bilgisi
                        if space_id:
                            label = f"Space: {space_id}"
                            cv2.putText(frame, label, (x1, y1 - 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        # Plaka/QR bilgisi
                        if qr_data:
                            cv2.putText(frame, f"QR: {qr_data[:15]}", (x1, y1 - 10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.qr_color, 2)
                        elif plate_text:
                            cv2.putText(frame, f"Plate: {plate_text}", (x1, y1 - 10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.plate_color, 2)
                        
                        # Confidence
                        cv2.putText(frame, f"Conf: {confidence:.2f}", (x1, y2 + 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Park yeri polygonlarını çiz
            self.draw_parking_spaces(frame)
            
            # Bilgi paneli
            info_text = f"Araclar: {len(detected_vehicles)} | Takip: {len(self.tracked_vehicles)} | Frame: {frame_count}"
            cv2.putText(frame, info_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Görüntüyü göster
            cv2.imshow("Smart Parking Detection", frame)
            
            # Tespit edilen araçları konsolda göster
            if len(detected_vehicles) > 0 and frame_count % 30 == 0:
                for i, vehicle in enumerate(detected_vehicles):
                    print(f"  🚗 Araç ID {vehicle['vehicle_id']} (Frame'de: {vehicle['frames']}x):")
                    print(f"    - Park Yeri: {vehicle['parking_space_name']} (ID: {vehicle['parking_space_id']})")
                    if vehicle['qr']:
                        print(f"    - QR Kod: {vehicle['qr']} ✓")
                    else:
                        print(f"    - Plaka: {vehicle['plate'] if vehicle['plate'] else 'Okunamadı'}")
                    print(f"    - Güven: {vehicle['confidence']:.2%}")
            
            # Tuş kontrolü
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("\nÇıkılıyor...")
                break
            elif key == ord('s') or key == ord('S'):
                filename = f"parking_detection_{frame_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"✓ Kaydedildi: {filename}")
        
        cap.release()
        cv2.destroyAllWindows()
        print("✓ Kamera kapatıldı")
    
    def draw_parking_spaces(self, frame):
        """Park yerlerini çiz"""
        for space in self.parking_spaces:
            coords = np.array(space['coordinates'], dtype=np.int32)
            cv2.polylines(frame, [coords], True, (255, 0, 0), 1)
            
            # ID yazısı
            M = cv2.moments(coords)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(frame, str(space['id']), (cx - 10, cy),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)


if __name__ == "__main__":
    # Paths
    PARKING_COORDS = "parking_coordinates.json"
    
    # Tesseract path (Windows için - kendi yolunu koy)
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # BURASI ÖNEMLİ - .NET API'nin portunu gir
    API_URL = "http://localhost:5197"
    
    if not Path(PARKING_COORDS).exists():
        print(f"❌ {PARKING_COORDS} bulunamadı!")
    else:
        system = ParkingDetectionSystem(PARKING_COORDS, TESSERACT_PATH, API_URL)
        system.run_camera(camera_id=1, confidence_threshold=0.05)