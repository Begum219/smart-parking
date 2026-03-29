import cv2
import json
import numpy as np
import requests
import time
from datetime import datetime
from ultralytics import YOLO
from pyzbar.pyzbar import decode
import pytesseract
import threading

class CameraDetector:
    def __init__(self, camera_id, camera_name, coords_path, api_url, tesseract_path=None):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.api_url = api_url
        
        # Tesseract
        if tesseract_path:
            pytesseract.pytesseract.pytesseract_cmd = tesseract_path
        
        # Koordinatları yükle
        with open(coords_path, 'r', encoding='utf-8') as f:
            self.camera_data = json.load(f)
        
        self.parking_spaces = self.camera_data['spaces']
        self.road_zones = self.camera_data.get('road_zones', [])
        
        print(f"✅ Kamera {camera_id}: {len(self.parking_spaces)} park yeri yüklendi")
        if self.road_zones:
            print(f"   🚫 {len(self.road_zones)} yol alanı yüklendi")
        
        # YOLO
        self.model = YOLO('yolov8n.pt')
        
        # Tracking
        self.tracked_vehicles = {}
        self.next_vehicle_id = 1
        self.max_distance = 100
        
        # API timers
        self.last_api_send = {}
        self.api_send_interval = 3
        
        # Thread control
        self.running = True
    
    def point_in_polygon(self, point, polygon):
        """Nokta polygon içinde mi?"""
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
    
    def get_centroid(self, bbox):
        """Bbox merkezi"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    def distance(self, p1, p2):
        """2 nokta arası mesafe"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def find_parking_space(self, bbox):
        """Hangi park yerinde?"""
        center = self.get_centroid(bbox)
        for space in self.parking_spaces:
            if self.point_in_polygon(center, space['coordinates']):
                return space['space_id'], space['space_id']
        return None, None
    
    def is_in_road_zone(self, bbox):
        """Yol alanında mı? (YASAK!)"""
        center = self.get_centroid(bbox)
        for zone in self.road_zones:
            if self.point_in_polygon(center, zone['coordinates']):
                return True, zone['zone_id']
        return False, None
    
    def track_vehicle(self, bbox, space_id, space_name, plate, conf):
        """Araç tracking"""
        centroid = self.get_centroid(bbox)
        
        closest_id = None
        closest_dist = self.max_distance
        
        for vid, vdata in list(self.tracked_vehicles.items()):
            dist = self.distance(centroid, vdata['centroid'])
            if dist < closest_dist:
                closest_dist = dist
                closest_id = vid
        
        if closest_id is not None:
            # Güncelle
            self.tracked_vehicles[closest_id].update({
                'centroid': centroid,
                'space_id': space_id,
                'space_name': space_name,
                'plate': plate,
                'confidence': conf,
                'frames': self.tracked_vehicles[closest_id]['frames'] + 1
            })
            return closest_id, self.tracked_vehicles[closest_id]
        else:
            # Yeni araç
            vid = self.next_vehicle_id
            self.next_vehicle_id += 1
            self.tracked_vehicles[vid] = {
                'centroid': centroid,
                'space_id': space_id,
                'space_name': space_name,
                'plate': plate,
                'confidence': conf,
                'frames': 1
            }
            return vid, self.tracked_vehicles[vid]
    
    def read_qr_code(self, frame, bbox):
        """QR kod oku"""
        x1, y1, x2, y2 = bbox
        vehicle_region = frame[y1:y2, x1:x2]
        
        if vehicle_region.size == 0:
            return ""
        
        try:
            qr_codes = decode(vehicle_region)
            if qr_codes:
                return qr_codes[0].data.decode('utf-8')
        except:
            pass
        
        return ""
    
    def extract_plate_region(self, frame, bbox):
        """Plaka bölgesi (alt %30)"""
        x1, y1, x2, y2 = bbox
        height = y2 - y1
        plate_y1 = int(y2 - height * 0.3)
        return frame[plate_y1:y2, x1:x2]
    
    def read_plate(self, plate_region):
        """OCR ile plaka"""
        if plate_region.size == 0:
            return ""
        
        try:
            gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            _, binary = cv2.threshold(enhanced, 150, 255, cv2.THRESH_BINARY)
            
            text = pytesseract.image_to_string(
                binary,
                config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            )
            return text.strip()
        except:
            return ""
    
    def send_to_api(self, vehicle_data):
        """Normal park - API'ye gönder"""
        vehicle_id = vehicle_data['vehicle_id']
        
        now = time.time()
        if vehicle_id in self.last_api_send:
            if now - self.last_api_send[vehicle_id] < self.api_send_interval:
                return
        
        try:
            payload = {
                "cameraId": self.camera_id,
                "cameraName": self.camera_name,
                "vehicleId": vehicle_id,
                "parkingSpaceId": vehicle_data['parking_space_id'],
                "parkingSpaceName": vehicle_data['parking_space_name'],
                "qrCode": vehicle_data.get('qr'),
                "plateNumber": vehicle_data.get('plate'),
                "confidence": float(vehicle_data['confidence']),
                "framesDetected": vehicle_data['frames'],
                "detectionTime": datetime.now().isoformat(),
                "status": "occupied"
            }
            
            response = requests.post(
                f"{self.api_url}/api/parking/detect",
                json=payload,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                print(f"[{self.camera_name}] ✅ Araç {vehicle_id} API'ye gönderildi")
                self.last_api_send[vehicle_id] = now
        
        except Exception as e:
            pass  # Sessiz hata
    
    def issue_penalty(self, vehicle_data, zone_id):
        """🚨 CEZA KES!"""
        vehicle_id = vehicle_data['vehicle_id']
        
        penalty_key = f"penalty_{vehicle_id}"
        now = time.time()
        if penalty_key in self.last_api_send:
            if now - self.last_api_send[penalty_key] < 10:
                return
        
        plate_or_qr = vehicle_data.get('plate') or vehicle_data.get('qr') or "UNKNOWN"
        
        print(f"\n{'='*60}")
        print(f"🚨 CEZA KESİLİYOR! 🚨")
        print(f"Kamera: {self.camera_name}")
        print(f"Araç ID: {vehicle_id}")
        print(f"Alan: {zone_id} (YOL - YASAK!)")
        print(f"Plaka/QR: {plate_or_qr}")
        print(f"Ceza: 500 TL")
        print(f"{'='*60}\n")
        
        try:
            payload = {
                "cameraId": self.camera_id,
                "vehicleId": vehicle_id,
                "violationType": "WrongParking",
                "amount": 500.0,
                "description": f"Yol alanına park ({zone_id})",
                "plateNumber": vehicle_data.get('plate'),
                "qrCode": vehicle_data.get('qr'),
                "confidence": float(vehicle_data['confidence']),
                "detectionTime": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.api_url}/api/Penalty/issue",
                json=payload,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                print(f"[{self.camera_name}] ✅ Ceza API'ye kaydedildi!")
                self.last_api_send[penalty_key] = now
        
        except Exception as e:
            pass  # Sessiz hata
    
    def process_frame(self, frame, confidence_threshold=0.05):
        """Frame işle"""
        results = self.model(frame, conf=confidence_threshold, verbose=False)
        detected_vehicles = []
        
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Sadece araçlar (car, bus, truck)
                if class_id in [2, 5, 7]:
                    space_id, space_name = self.find_parking_space([x1, y1, x2, y2])
                    in_road, road_zone_id = self.is_in_road_zone([x1, y1, x2, y2])
                    
                    # QR/Plaka oku
                    qr_data = self.read_qr_code(frame, [x1, y1, x2, y2])
                    plate_text = qr_data if qr_data else ""
                    
                    if not plate_text:
                        plate_region = self.extract_plate_region(frame, [x1, y1, x2, y2])
                        plate_text = self.read_plate(plate_region)
                    
                    # Track
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
                        'frames': vehicle_data['frames'],
                        'in_road': in_road,
                        'road_zone_id': road_zone_id
                    }
                    detected_vehicles.append(vehicle_info)
                    
                    # 🚨 YOLA PARK = CEZA!
                    if in_road and (plate_text or qr_data):
                        self.issue_penalty(vehicle_info, road_zone_id)
                    
                    # Normal park = API
                    if space_id:
                        self.send_to_api(vehicle_info)
                    
                    # Çiz
                    color = (0, 0, 255) if in_road else (0, 255, 0)  # Kırmızı/Yeşil
                    thickness = 3 if in_road else 2
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                    
                    # ID
                    cv2.putText(frame, f"ID:{vehicle_id}", (x1, y1 - 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # YASAK ALAN UYARISI
                    if in_road:
                        cv2.putText(frame, "YASAK ALAN!", (x1, y1 - 70),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        cv2.putText(frame, "Ceza: 500 TL", (x1, y1 - 90),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    
                    # Park yeri
                    if space_id:
                        cv2.putText(frame, f"Space: {space_id}", (x1, y1 - 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Plaka/QR
                    if qr_data:
                        cv2.putText(frame, f"QR: {qr_data[:15]}", (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    elif plate_text:
                        cv2.putText(frame, f"Plaka: {plate_text}", (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                    
                    # Confidence
                    cv2.putText(frame, f"Conf: {confidence:.2f}", (x1, y2 + 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return detected_vehicles, frame
    
    def draw_zones(self, frame):
        """Park yerleri + Yolları çiz"""
        # Park yerleri (MAVİ)
        for space in self.parking_spaces:
            coords = np.array(space['coordinates'], dtype=np.int32)
            cv2.polylines(frame, [coords], True, (255, 255, 0), 1)
            
            M = cv2.moments(coords)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(frame, str(space['space_id']), (cx - 10, cy),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        # Yol alanları (KIRMIZI)
        for zone in self.road_zones:
            coords = np.array(zone['coordinates'], dtype=np.int32)
            cv2.polylines(frame, [coords], True, (0, 0, 255), 2)
            
            overlay = frame.copy()
            cv2.fillPoly(overlay, [coords], (0, 0, 255))
            cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
    
    def run(self):
        """Ana döngü"""
        cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            print(f"❌ Kamera {self.camera_id} açılamadı!")
            self.running = False
            return
        
        print(f"✅ {self.camera_name} başlatıldı")
        
        frame_count = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Tespit
            vehicles, frame = self.process_frame(frame, confidence_threshold=0.05)
            
            # Zonu çiz
            self.draw_zones(frame)
            
            # Bilgi paneli
            info = f"[{self.camera_name}] Araclar: {len(vehicles)} | Takip: {len(self.tracked_vehicles)}"
            cv2.putText(frame, info, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Göster
            cv2.imshow(self.camera_name, frame)
            
            # Konsol çıktısı (her 90 frame'de bir)
            if frame_count % 90 == 0 and len(vehicles) > 0:
                print(f"\n[{self.camera_name}] Araçlar: {len(vehicles)}")
                for v in vehicles:
                    status = "🚫 YOLDA!" if v['in_road'] else f"✅ {v['parking_space_name']}"
                    plate = v['qr'] or v['plate'] or "Okunamadı"
                    print(f"  Araç {v['vehicle_id']}: {status} | Plaka: {plate}")
            
            # ESC çıkış
            if cv2.waitKey(1) & 0xFF == 27:
                break
        
        cap.release()
        try:
            cv2.destroyWindow(self.camera_name)
        except:
            pass


# MAIN
if __name__ == "__main__":
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    API_URL = "http://localhost:5197"
    
    cameras = [
        {"id": 0, "name": "Kamera 1 (A-B Bölümü)", "coords": "camera_0_coordinates.json"},
        {"id": 1, "name": "Kamera 2 (C Bölümü)", "coords": "camera_1_coordinates.json"}
    ]
    
    detectors = []
    threads = []
    
    print("="*60)
    print("🚀 SMART PARKING BAŞLATILIYOR")
    print("="*60)
    
    # Kameraları başlat
    for cam in cameras:
        detector = CameraDetector(
            camera_id=cam['id'],
            camera_name=cam['name'],
            coords_path=cam['coords'],
            api_url=API_URL,
            tesseract_path=TESSERACT_PATH
        )
        detectors.append(detector)
        
        thread = threading.Thread(target=detector.run)
        thread.start()
        threads.append(thread)
    
    print("="*60)
    print("✅ TÜM KAMERALAR ÇALIŞIYOR!")
    print("="*60)
    print("Kontroller:")
    print("  ESC: Herhangi bir pencerede ESC'ye basın")
    print("="*60)
    
    # Bekleme
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n⚠️  Sistem durduruluyor...")
        for detector in detectors:
            detector.running = False
    
    cv2.destroyAllWindows()
    print("✅ Sistem kapatıldı")