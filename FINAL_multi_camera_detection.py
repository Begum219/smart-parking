#!/usr/bin/env python3
"""
SMART PARKING MANAGEMENT SYSTEM - FINAL VERSION WITH GLOBAL PENALTY FIX
========================================================================

TESPİT MANTIĞI:
- YOLO oyuncak araçları "cell phone", "knife" vb. olarak algılıyor
- ÇÖZÜM: Sınıf kontrolü YOK - sadece KOORDİNAT kontrolü var!
- Bir nesne PARK YERİNDE veya YOLDA ise → ARAÇ olarak kabul edilir
- Diğer nesneler (duvar, zemin vs.) atlanır

ÖZELLİKLER:
✅ Çift kamera desteği (multi-threading)
✅ Park yeri tespiti (koordinat bazlı)
✅ Yol/yasak alan tespiti + otomatik ceza kesme
✅ ✨ YENİ: 1 dakika timer sistemi (yol ihlali için)
✅ ✨ YENİ: Çoklu ceza engelleme (penalty_issued flag)
✅ ✨✨✨ GLOBAL PENALTY SİSTEMİ - ÇİFT KAMERA SORUNU ÇÖZÜLDÜ!
✅ QR kod okuma (pyzbar)
✅ OCR plaka okuma (Tesseract - opsiyonel)
✅ Araç tracking (ID bazlı)
✅ API entegrasyonu (park + ceza)
✅ Gerçek zamanlı görselleştirme

KULLANIM:
    python FINAL_multi_camera_detection_GLOBAL_FIX.py

AYARLAR:
- Confidence: 0.01 (çok düşük - oyuncak araçlar için)
- Çözünürlük: 1920x1080 (koordinat dosyalarıyla uyumlu)
- DEBUG: True (detaylı log)
"""

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

# ============================================================
# ✨ GLOBAL PENALTY SİSTEMİ - TÜM KAMERALAR PAYLAŞIR!
# ============================================================
# Plaka/QR bazında ceza takibi (çift kamera sorunu çözümü)
GLOBAL_PENALTY_ISSUED = {}  # {plaka: timestamp}
PENALTY_LOCK = threading.Lock()  # Thread-safe erişim
PENALTY_COOLDOWN = 300  # 5 dakika (300 saniye) - aynı plakaya tekrar ceza kesilmez
# ============================================================

class CameraDetector:
    def __init__(self, camera_id, camera_name, coords_path, api_url, tesseract_path=None, debug=False):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.api_url = api_url
        self.debug = debug
        
        # Tesseract
        if tesseract_path:
            pytesseract.pytesseract.pytesseract_cmd = tesseract_path
            # Test et
            try:
                version = pytesseract.get_tesseract_version()
                print(f"   ✅ Tesseract {version} bulundu")
            except:
                print(f"   ⚠️  Tesseract bulunamadı: {tesseract_path}")
                print(f"       OCR çalışmayacak, sadece QR kod kullanılacak")
        
        # Koordinatları yükle
        with open(coords_path, 'r', encoding='utf-8') as f:
            self.camera_data = json.load(f)
        
        self.parking_spaces = self.camera_data['spaces']
        self.road_zones = self.camera_data.get('road_zones', [])
        
        print(f"✅ Kamera {camera_id}: {len(self.parking_spaces)} park yeri yüklendi")
        if self.road_zones:
            print(f"   🚫 {len(self.road_zones)} yol alanı yüklendi")
        
        # DEBUG - JSON formatını kontrol et
        if self.debug and self.parking_spaces:
            first_space = self.parking_spaces[0]
            print(f"   [DEBUG] İlk park yeri keys: {first_space.keys()}")
            print(f"   [DEBUG] İlk park yeri: {first_space}")
            if 'space_id' not in first_space:
                print(f"   ⚠️  UYARI: 'space_id' yok! Kullanılan key: {list(first_space.keys())}")
        
        # YOLO
        self.model = YOLO('yolov8n.pt')
        
        # Tracking
        self.tracked_vehicles = {}
        self.next_vehicle_id = 1
        self.max_distance = 100
        
        # API timers
        self.last_api_send = {}
        self.api_send_interval = 3
        
        # ✨ YENİ: Yol ihlali timer sistemi (1 dakika kuralı)
        self.road_violation_timers = {}  # {vehicle_id: {'start_time': timestamp, 'zone_id': zone}}
        self.penalty_issued = {}  # {vehicle_id: True/False} - LOKAL (kamera içi)
        self.road_violation_threshold = 60  # 60 saniye
        
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
        
        if self.debug:
            print(f"  [DEBUG] Araç merkezi: {center}")
        
        for space in self.parking_spaces:
            # space_id kontrolü
            if 'space_id' not in space:
                print(f"  [HATA] Park yerinde 'space_id' yok! Keys: {space.keys()}")
                continue
            
            if self.point_in_polygon(center, space['coordinates']):
                if self.debug:
                    print(f"  [DEBUG] ✅ Park yeri bulundu: {space['space_id']}")
                return space['space_id'], space['space_id']
        
        if self.debug:
            print(f"  [DEBUG] ❌ Park yeri bulunamadı! Merkez: {center}")
            print(f"  [DEBUG] Toplam park yeri sayısı: {len(self.parking_spaces)}")
        
        return None, None
    
    def is_in_road_zone(self, bbox):
        """Yol alanında mı? (YASAK!)"""
        center = self.get_centroid(bbox)
        
        if self.debug:
            print(f"  [DEBUG YOL] Kontrol edilen merkez: {center}")
        
        for zone in self.road_zones:
            if self.point_in_polygon(center, zone['coordinates']):
                if self.debug:
                    print(f"  [DEBUG YOL] ✅ Yol alanında! Zone: {zone['zone_id']}")
                return True, zone['zone_id']
        
        if self.debug:
            print(f"  [DEBUG YOL] ❌ Yol alanında değil")
        
        return False, None
    
    # ============================================================
    # ✨ YENİ: YOL İHLALİ TIMER FONKSİYONLARI
    # ============================================================
    def start_road_violation_timer(self, vehicle_id, zone_id):
        """Yol ihlali timer'ını başlat"""
        if vehicle_id not in self.road_violation_timers:
            self.road_violation_timers[vehicle_id] = {
                'start_time': time.time(),
                'zone_id': zone_id
            }
            self.penalty_issued[vehicle_id] = False  # Ceza flag'ini başlat
            print(f"🚗 [{self.camera_name}] Araç {vehicle_id} yola girdi - Timer başlatıldı! (60s)")
    
    def check_road_violation_timer(self, vehicle_id):
        """Timer kontrolü - 60s geçti mi? Ceza kesildi mi?"""
        if vehicle_id in self.road_violation_timers:
            elapsed = time.time() - self.road_violation_timers[vehicle_id]['start_time']
            
            # ✨ ÖNEMLİ: Ceza daha önce kesildi mi kontrol et!
            if self.penalty_issued.get(vehicle_id, False):
                # Zaten ceza kesilmiş, tekrar kesme!
                return False, 0
            
            if elapsed >= self.road_violation_threshold:
                print(f"⏰ [{self.camera_name}] Araç {vehicle_id} yolda {int(elapsed)} saniye!")
                print(f"   ⚠️  1 dakika eşiği aşıldı → CEZA KESİLECEK!")
                return True, elapsed
            else:
                remaining = self.road_violation_threshold - int(elapsed)
                if int(elapsed) % 10 == 0:  # Her 10 saniyede log
                    print(f"⏳ [{self.camera_name}] Araç {vehicle_id} yolda {int(elapsed)}s (Kalan: {remaining}s)")
                return False, elapsed
        return False, 0
    
    def clear_road_violation_timer(self, vehicle_id):
        """Araç yol alanından çıktı - timer'ı temizle"""
        if vehicle_id in self.road_violation_timers:
            elapsed = time.time() - self.road_violation_timers[vehicle_id]['start_time']
            print(f"✅ [{self.camera_name}] Araç {vehicle_id} yoldan çıktı ({int(elapsed)}s sonra)")
            del self.road_violation_timers[vehicle_id]
            # Ceza flag'ini de temizle
            if vehicle_id in self.penalty_issued:
                del self.penalty_issued[vehicle_id]
    
    def get_road_timer_display(self, vehicle_id):
        """Ekranda gösterilecek timer bilgisi"""
        if vehicle_id in self.road_violation_timers:
            elapsed = int(time.time() - self.road_violation_timers[vehicle_id]['start_time'])
            remaining = max(0, self.road_violation_threshold - elapsed)
            
            # Ceza kesildi mi?
            if self.penalty_issued.get(vehicle_id, False):
                return "CEZA KESİLDİ!", (0, 0, 255)  # Kırmızı
            else:
                return f"Timer: {remaining}s", (0, 165, 255)  # Turuncu
        return None, None
    # ============================================================
    
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
        """QR kod oku - TÜM FRAME'DEN!"""
        try:
            # Tüm frame'den QR oku
            qr_codes = decode(frame)
            
            if qr_codes:
                # QR bulundu - araç bbox'ına yakın mı kontrol et
                x1, y1, x2, y2 = bbox
                
                for qr in qr_codes:
                    # QR kodun merkezi
                    qr_rect = qr.rect
                    qr_center = (qr_rect.left + qr_rect.width // 2,
                                qr_rect.top + qr_rect.height // 2)
                    
                    # QR kod araç bbox içinde mi veya yakınında mı?
                    # Genişletilmiş bbox (araç + çevresi)
                    margin = 100
                    if (x1 - margin <= qr_center[0] <= x2 + margin and
                        y1 - margin <= qr_center[1] <= y2 + margin):
                        
                        qr_data = qr.data.decode('utf-8')
                        if self.debug:
                            print(f"  [QR OKUNDU!] {qr_data} @ {qr_center}")
                        return qr_data
        
        except:
            # QR okuma hatası - sessizce atla
            pass
        
        return ""
    
    def extract_plate_region(self, frame, bbox):
        """Plaka bölgesi (alt %30)"""
        x1, y1, x2, y2 = bbox
        height = y2 - y1
        plate_y1 = int(y2 - height * 0.3)
        return frame[plate_y1:y2, x1:x2]
    
    def read_plate(self, plate_region):
        """OCR ile plaka - İYİLEŞTİRİLMİŞ"""
        if plate_region.size == 0:
            return ""
        
        # Tesseract yoksa sessizce geri dön
        try:
            import pytesseract
            # Tesseract path kontrolü
            if not hasattr(pytesseract.pytesseract, 'tesseract_cmd'):
                return ""
        except:
            return ""
        
        try:
            # Resize - küçükse büyüt
            h, w = plate_region.shape[:2]
            if h < 50 or w < 100:
                scale = max(2, 100 / w)
                plate_region = cv2.resize(plate_region, None, fx=scale, fy=scale,
                                         interpolation=cv2.INTER_CUBIC)
            
            # Gray
            gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Kontrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Thresholding (hem siyah hem beyaz)
            _, binary1 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            _, binary2 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Her ikisini de dene
            config = '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            
            text1 = pytesseract.image_to_string(binary1, config=config).strip()
            text2 = pytesseract.image_to_string(binary2, config=config).strip()
            
            # Uzun olanı al
            result = text1 if len(text1) > len(text2) else text2
            
            if self.debug and result:
                print(f"  [PLAKA OKUNDU!] {result}")
            
            return result
        
        except:
            # Tesseract hatası - sessizce atla
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
        """🚨 CEZA KES! - GLOBAL PENALTY SİSTEMİ İLE"""
        global GLOBAL_PENALTY_ISSUED, PENALTY_LOCK, PENALTY_COOLDOWN
        
        vehicle_id = vehicle_data['vehicle_id']
        plate_or_qr = vehicle_data.get('qr') or vehicle_data.get('plate')
        
        # ✨ ÖNEMLİ: Plaka/QR yoksa ceza kesme!
        if not plate_or_qr:
            print(f"[{self.camera_name}] ⚠️  Plaka/QR okunamadı, ceza kesilemiyor!")
            return
        
        # ✨ GLOBAL KONTROL: Bu plakaya daha önce ceza kesildi mi?
        with PENALTY_LOCK:  # Thread-safe
            current_time = time.time()
            
            # Son ceza zamanını kontrol et
            if plate_or_qr in GLOBAL_PENALTY_ISSUED:
                last_penalty_time = GLOBAL_PENALTY_ISSUED[plate_or_qr]
                elapsed_since_penalty = current_time - last_penalty_time
                
                if elapsed_since_penalty < PENALTY_COOLDOWN:
                    remaining = int(PENALTY_COOLDOWN - elapsed_since_penalty)
                    print(f"[{self.camera_name}] ⏸️  {plate_or_qr} zaten cezalı! (Kalan süre: {remaining}s)")
                    # Lokal flag'i de set et
                    self.penalty_issued[vehicle_id] = True
                    return
        
        # Ceza kesme mesajı
        print(f"\n{'='*60}")
        print(f"🚨 CEZA KESİLİYOR! 🚨")
        print(f"Kamera: {self.camera_name}")
        print(f"Araç ID: {vehicle_id}")
        print(f"Alan: {zone_id} (YOL - YASAK!)")
        print(f"Plaka/QR: {plate_or_qr}")
        print(f"Ceza: 500 TL")
        print(f"Sebep: 1 dakikadan fazla yolda park")
        print(f"{'='*60}\n")
        
        try:
            payload = {
                "cameraName": self.camera_name,
                "detectionVehicleId": str(vehicle_id),
                "zoneId": zone_id,
                "qrCode": vehicle_data.get('qr'),
                "plateNumber": vehicle_data.get('plate'),
                "amount": 500.00  # ✨ YENİ: Ceza miktarı!
            }
            
            # ✨ DEBUG: Payload'ı logla
            print(f"[DEBUG] API Payload:")
            print(f"  {payload}")
            
            response = requests.post(
                f"{self.api_url}/api/Penalty/issue-road-violation",
                json=payload,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                # ✨ YENİ: Response body'yi DETAYLI logla!
                print(f"[{self.camera_name}] ✅ API Response:")
                print(f"  Status: {response.status_code}")
                print(f"  Body: {response.text[:500]}")  # İlk 500 karakter
                
                # ✨ ÖNEMLİ: GLOBAL flag'i set et!
                with PENALTY_LOCK:
                    GLOBAL_PENALTY_ISSUED[plate_or_qr] = time.time()
                
                # Lokal flag'i de set et
                self.penalty_issued[vehicle_id] = True
                
                print(f"[GLOBAL] 🔒 {plate_or_qr} cezalandırıldı (Cooldown: 300s)")
            else:
                print(f"[{self.camera_name}] ❌ API HATASI!")
                print(f"  Status: {response.status_code}")
                print(f"  Body: {response.text[:500]}")
        
        except Exception as e:
            print(f"[{self.camera_name}] ❌ Ceza API Exception: {e}")
    
    def process_frame(self, frame, confidence_threshold=0.05):
        """Frame işle"""
        results = self.model(frame, conf=confidence_threshold, verbose=False)
        detected_vehicles = []
        current_frame_vehicles = set()
        
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # TÜM NESNELERİ ARAÇ OLARAK KABUL ET!
                # YOLO oyuncak araçları telefon/bıçak olarak algılıyor
                # Bu yüzden sınıf kontrolü yapmıyoruz - koordinat kontrolü yapacağız
                
                # Önce park yeri ve yol kontrolü yap
                space_id, space_name = self.find_parking_space([x1, y1, x2, y2])
                in_road, road_zone_id = self.is_in_road_zone([x1, y1, x2, y2])
                
                if self.debug:
                    center = self.get_centroid([x1, y1, x2, y2])
                    print(f"  [ÖZET] Merkez: {center} | Park: {space_id or 'YOK'} | Yol: {road_zone_id or 'YOK'}")
                
                # Park yerinde DE yolda DA DEĞİLSE atla (gürültü - duvardaki nesne vs.)
                if not space_id and not in_road:
                    if self.debug:
                        print(f"  [ATLA] Park yok VE yol yok → gürültü")
                    continue
                
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
                
                current_frame_vehicles.add(vehicle_id)
                
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
                
                # ============================================================
                # ✨ YENİ: YOL İHLALİ LOJİĞİ (TIMER İLE)
                # ============================================================
                if in_road:
                    # Araç yol alanında!
                    self.start_road_violation_timer(vehicle_id, road_zone_id)
                    
                    # Timer kontrolü - 60s geçti mi?
                    should_penalize, elapsed = self.check_road_violation_timer(vehicle_id)
                    
                    if should_penalize:
                        # CEZA KES!
                        self.issue_penalty(vehicle_info, road_zone_id)
                else:
                    # Araç yol alanından çıktı - timer'ı temizle
                    self.clear_road_violation_timer(vehicle_id)
                # ============================================================
                
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
                
                # ✨ YENİ: YASAK ALAN + TIMER GÖSTER
                if in_road:
                    cv2.putText(frame, "YASAK ALAN!", (x1, y1 - 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    
                    # Timer bilgisi
                    timer_text, timer_color = self.get_road_timer_display(vehicle_id)
                    if timer_text:
                        cv2.putText(frame, timer_text, (x1, y1 - 90),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, timer_color, 2)
                
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
        
        # ✨ YENİ: Frame'de görünmeyen araçların timer'larını temizle
        for vehicle_id in list(self.road_violation_timers.keys()):
            if vehicle_id not in current_frame_vehicles:
                self.clear_road_violation_timer(vehicle_id)
        
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
                
                # 'space_id' kontrolü
                label = space.get('space_id', space.get('id', '?'))
                
                cv2.putText(frame, str(label), (cx - 10, cy),
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
        
        # ÇÖZÜNÜRLÜK - KOORDİNAT DOSYALARIYLA UYUMLU OLMALI!
        # Koordinat dosyaları 1920x1080 ile oluşturuldu
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)   # Koordinatlarla UYUMLU!
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # Koordinatlarla UYUMLU!
        
        actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        print(f"✅ {self.camera_name} başlatıldı ({int(actual_width)}x{int(actual_height)})")
        
        frame_count = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Tespit - ÇOK DÜŞÜK THRESHOLD (oyuncak araçlar için!)
            vehicles, frame = self.process_frame(frame, confidence_threshold=0.01)  # 0.01 = %1
            
            # Zonu çiz
            self.draw_zones(frame)
            
            # Bilgi paneli
            info = f"[{self.camera_name}] Araclar: {len(vehicles)} | Takip: {len(self.tracked_vehicles)}"
            cv2.putText(frame, info, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Göster
            cv2.imshow(self.camera_name, frame)
            
            # Konsol çıktısı (her 30 frame'de bir - daha sık!)
            if frame_count % 30 == 0 and len(vehicles) > 0:
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
    
    # 🔍 DEBUG MODU - Detaylı log için False (daha az spam)
    DEBUG = False
    
    cameras = [
        {"id": 0, "name": "Kamera 1 (A-B Bölümü)", "coords": "camera_0_coordinates.json"},
        {"id": 1, "name": "Kamera 2 (C Bölümü)", "coords": "camera_1_coordinates.json"}
    ]
    
    detectors = []
    threads = []
    
    print("="*60)
    print("🚀 SMART PARKING BAŞLATILIYOR")
    print("✨ YENİ: 1 Dakika Yol İhlali Kontrolü Aktif!")
    print("✨ YENİ: Tekrar Ceza Kesme Engellendi!")
    print("✨✨✨ GLOBAL PENALTY SİSTEMİ - ÇİFT KAMERA FIX!")
    print(f"⏱️  Penalty Cooldown: {PENALTY_COOLDOWN} saniye (5 dakika)")
    print("="*60)
    
    # Kameraları başlat
    for cam in cameras:
        detector = CameraDetector(
            camera_id=cam['id'],
            camera_name=cam['name'],
            coords_path=cam['coords'],
            api_url=API_URL,
            tesseract_path=TESSERACT_PATH,
            debug=DEBUG
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