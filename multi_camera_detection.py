import cv2
import json
import numpy as np
import requests
import threading
import time
from datetime import datetime
from ultralytics import YOLO
from pyzbar.pyzbar import decode
import pytesseract
from pathlib import Path

class CameraParkingDetector:
    """Tek kamera için tespit sistemi"""
    
    def __init__(self, camera_id, camera_name, coords_path, tesseract_path, api_url):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.api_url = api_url
        
        # Tesseract yolunu ayarla (Windows için)
        if tesseract_path:
            pytesseract.pytesseract.pytesseract_cmd = tesseract_path
        
        # Park yeri koordinatlarını yükle
        with open(coords_path, 'r', encoding='utf-8') as f:
            self.camera_data = json.load(f)
        
        self.parking_spaces = self.camera_data['spaces']
        print(f"✅ Kamera {camera_id}: {len(self.parking_spaces)} park yeri yüklendi")
        
        # YOLO modelini yükle
        self.model = YOLO('yolov8n.pt')
        
        # Renkler
        self.vehicle_color = (0, 255, 0)
        self.detected_color = (0, 0, 255)
        self.plate_color = (255, 0, 0)
        self.qr_color = (0, 255, 255)
        
        # Tracking
        self.tracked_vehicles = {}
        self.next_vehicle_id = 1
        self.max_distance = 100
        
        # API timer
        self.last_api_send = {}
        self.api_send_interval = 3
        
        # Thread control
        self.running = False
        self.frame = None
        self.detection_count = 0
        
    def get_centroid(self, bbox):
        """Bounding box merkezini al"""
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        return (cx, cy)
    
    def distance(self, p1, p2):
        """İki nokta arasındaki mesafe"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
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
        """Bounding box'ı hangi park yerine ait"""
        center = self.get_centroid(bbox)
        
        for space in self.parking_spaces:
            polygon = space['coordinates']
            if self.point_in_polygon(center, polygon):
                return space['space_id'], space['space_id']
        
        return None, None
    
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
        """Plaka bölgesini çıkar"""
        x1, y1, x2, y2 = bbox
        height = y2 - y1
        plate_y1 = int(y2 - height * 0.3)
        plate_y2 = y2
        plate_region = frame[plate_y1:plate_y2, x1:x2]
        return plate_region
    
    def read_plate(self, plate_region):
        """OCR ile plaka oku"""
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
    
    def track_vehicle(self, bbox, space_id, space_name, plate_text, confidence):
        """Araç takibi"""
        centroid = self.get_centroid(bbox)
        
        closest_id = None
        closest_dist = self.max_distance
        
        for vehicle_id, vehicle_data in list(self.tracked_vehicles.items()):
            dist = self.distance(centroid, vehicle_data['centroid'])
            if dist < closest_dist:
                closest_dist = dist
                closest_id = vehicle_id
        
        if closest_id is not None:
            self.tracked_vehicles[closest_id]['centroid'] = centroid
            self.tracked_vehicles[closest_id]['space_id'] = space_id
            self.tracked_vehicles[closest_id]['space_name'] = space_name
            self.tracked_vehicles[closest_id]['plate'] = plate_text
            self.tracked_vehicles[closest_id]['confidence'] = confidence
            self.tracked_vehicles[closest_id]['frames'] += 1
            return closest_id, self.tracked_vehicles[closest_id]
        else:
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
    
    def send_to_api(self, vehicle_data):
        """API'ye gönder"""
        vehicle_id = vehicle_data['vehicle_id']
        
        now = time.time()
        if vehicle_id in self.last_api_send:
            if now - self.last_api_send[vehicle_id] < self.api_send_interval:
                return
        
        try:
            payload = {
                "cameraId": self.camera_id,  # ⬅️ KAMERA ID EKLENDİ
                "cameraName": self.camera_name,
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
            
            response = requests.post(
                f"{self.api_url}/api/parking/detect",
                json=payload,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                print(f"  [{self.camera_name}] ✅ Araç {vehicle_id} API'ye gönderildi")
                self.last_api_send[vehicle_id] = now
            else:
                print(f"  [{self.camera_name}] ⚠️ API hata: {response.status_code}")
        
        except Exception as e:
            print(f"  [{self.camera_name}] ⚠️ API hatası: {e}")
    
    def draw_parking_spaces(self, frame):
        """Park yerlerini çiz"""
        for space in self.parking_spaces:
            coords = np.array(space['coordinates'], dtype=np.int32)
            cv2.polylines(frame, [coords], True, (255, 0, 0), 1)
            
            M = cv2.moments(coords)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(frame, str(space['space_id']), (cx - 10, cy),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    def process_frame(self, frame, confidence_threshold=0.5):
        """Frame'i işle"""
        results = self.model(frame, conf=confidence_threshold, verbose=False)
        detected_vehicles = []
        
        # DEBUG: Kaç nesne tespit edildi?
        total_detections = sum(len(result.boxes) for result in results)
        if total_detections > 0:
            print(f"  🔍 [{self.camera_name}] {total_detections} nesne tespit edildi!")
        
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Araç ise (car, bus, truck)
                if class_id in [2, 5, 7]:
                    space_id, space_name = self.find_parking_space([x1, y1, x2, y2])
                    
                    # QR kod oku
                    qr_data = self.read_qr_code(frame, [x1, y1, x2, y2])
                    
                    # OCR dene
                    plate_text = qr_data if qr_data else ""
                    if not plate_text:
                        plate_region = self.extract_plate_region(frame, [x1, y1, x2, y2])
                        plate_text = self.read_plate(plate_region)
                    
                    # Araç takibi
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
                    
                    # API'ye gönder
                    if space_id:  # Sadece park yerinde olanları gönder
                        self.send_to_api(vehicle_info)
                    
                    # Görselleştirme
                    color = self.vehicle_color
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    cv2.putText(frame, f"ID:{vehicle_id}", (x1, y1 - 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    if space_id:
                        label = f"Space: {space_id}"
                        cv2.putText(frame, label, (x1, y1 - 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    if qr_data:
                        cv2.putText(frame, f"QR: {qr_data[:15]}", (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.qr_color, 2)
                    elif plate_text:
                        cv2.putText(frame, f"Plate: {plate_text}", (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.plate_color, 2)
        
        # Park yerlerini çiz
        self.draw_parking_spaces(frame)
        
        # Bilgi paneli
        info_text = f"[{self.camera_name}] Araçlar: {len(detected_vehicles)} | Takip: {len(self.tracked_vehicles)}"
        cv2.putText(frame, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame, detected_vehicles
    
    def run(self, confidence_threshold=0.5):
        """Kamera thread'ini çalıştır"""
        cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            print(f"❌ Kamera {self.camera_id} açılamadı!")
            return
        
        print(f"✅ {self.camera_name} başlatıldı")
        
        self.running = True
        frame_count = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                print(f"❌ [{self.camera_name}] Frame alınamadı")
                break
            
            frame_count += 1
            
            # Frame'i işle
            processed_frame, detected_vehicles = self.process_frame(frame, confidence_threshold)
            
            # Pencerede göster
            cv2.imshow(self.camera_name, processed_frame)
            
            # Deteksiyon sayısını güncelle
            self.detection_count = len(detected_vehicles)
            
            # ESC ile çık
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                self.running = False
                break
        
        cap.release()
        cv2.destroyWindow(self.camera_name)
        print(f"🛑 {self.camera_name} durduruldu")


class MultiCameraParkingSystem:
    """2 kameralı park sistemi yöneticisi"""
    
    def __init__(self, tesseract_path, api_url):
        self.tesseract_path = tesseract_path
        self.api_url = api_url
        self.cameras = []
        
        # API test
        self.test_api_connection()
    
    def test_api_connection(self):
        """API bağlantısını test et"""
        try:
            response = requests.get(f"{self.api_url}/api/parking/status", timeout=5)
            if response.status_code == 200:
                print(f"✅ .NET API bağlantısı başarılı: {self.api_url}\n")
            else:
                print(f"⚠️  API yanıt verdi ama status: {response.status_code}\n")
        except:
            print(f"❌ .NET API bağlantı kurulamadı: {self.api_url}")
            print("   Kontrol et: API çalışıyor mu? URL doğru mu?\n")
    
    def add_camera(self, camera_id, camera_name, coords_path):
        """Kamera ekle"""
        if not Path(coords_path).exists():
            print(f"❌ {coords_path} bulunamadı!")
            return False
        
        camera = CameraParkingDetector(
            camera_id=camera_id,
            camera_name=camera_name,
            coords_path=coords_path,
            tesseract_path=self.tesseract_path,
            api_url=self.api_url
        )
        self.cameras.append(camera)
        return True
    
    def run_all(self, confidence_threshold=0.5):
        """Tüm kameraları çalıştır (multi-threading)"""
        print("\n" + "="*60)
        print("🚗 SMART PARKING - MULTI KAMERA SİSTEMİ BAŞLATILIYOR")
        print("="*60 + "\n")
        
        threads = []
        
        for camera in self.cameras:
            thread = threading.Thread(
                target=camera.run,
                args=(confidence_threshold,),
                daemon=True
            )
            thread.start()
            threads.append(thread)
            time.sleep(1)  # Kameralar arası 1 saniye bekle
        
        print("\n" + "="*60)
        print("✅ TÜM KAMERALAR ÇALIŞIYOR!")
        print("="*60)
        print("Kontroller:")
        print("  ESC: Herhangi bir pencerede ESC'ye basın")
        print("="*60 + "\n")
        
        # Ana thread bekleme
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            print("\n⚠️  Sistem durduruluyor...")
            for camera in self.cameras:
                camera.running = False
        
        print("\n✅ Sistem kapatıldı")


# ========================================
# ANA PROGRAM
# ========================================

if __name__ == "__main__":
    # AYARLAR
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    API_URL = "http://localhost:5197"
    CONFIDENCE_THRESHOLD = 0.05  # ⬅️ 0.5'ten 0.05'e düşürüldü (çok daha hassas)
    
    # Sistem oluştur
    system = MultiCameraParkingSystem(TESSERACT_PATH, API_URL)
    
    # Kamera 1 ekle (A-B bölümü)
    system.add_camera(
        camera_id=0,
        camera_name="Kamera 1 (A-B Bölümü)",
        coords_path="camera_0_coordinates.json"
    )
    
    # Kamera 2 ekle (C bölümü)
    system.add_camera(
        camera_id=1,
        camera_name="Kamera 2 (C Bölümü)",
        coords_path="camera_1_coordinates.json"
    )
    
    # Tüm kameraları başlat
    system.run_all(confidence_threshold=CONFIDENCE_THRESHOLD)