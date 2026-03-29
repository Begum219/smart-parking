using System;
using System.Collections.Generic;

namespace SmartParking.Domain.Entities
{
    public class ParkingSpace : BaseEntity
    {
        // Mevcut alanlar
        public string SpaceNumber { get; set; } // P1, P2, P3...
        public Guid? CameraId { get; set; }
        public bool IsOccupied { get; set; }
        public string? Coordinates { get; set; } // JSON string (eski - geriye dönük uyumluluk için)
        public int FloorLevel { get; set; }
        public string SpaceType { get; set; } // "standard", "handicapped", "electric", "vip"
        public string Status { get; set; } // "available", "occupied", "reserved", "maintenance"

        // ✨ YENİ EKLEMELER - Sinema Koltuğu UI için
        public int Row { get; set; } // Satır numarası (1, 2, 3...)
        public int Column { get; set; } // Sütun numarası (1, 2, 3...)
        public string Section { get; set; } // Bölüm (A, B, C, D)

        // ✨ YENİ EKLEMELER - Çizgi Tespiti için (YOLO koordinatları)
        public int CoordinateX { get; set; } // X başlangıç noktası
        public int CoordinateY { get; set; } // Y başlangıç noktası
        public int Width { get; set; } // Genişlik (piksel)
        public int Height { get; set; } // Yükseklik (piksel)

        // ✨ YENİ EKLEMELER - Navigasyon için
        public string? NavigationInstructions { get; set; }
        // Örn: "Girişten sağa dönün, 2. sütun, sol taraf"

        public int DistanceFromEntrance { get; set; } // Girişten uzaklık (metre)

        // Navigation Properties
        public virtual Camera? Camera { get; set; }
        public virtual ICollection<ParkingSession> ParkingSessions { get; set; }

        public ParkingSpace()
        {
            SpaceNumber = string.Empty;
            IsOccupied = false;
            FloorLevel = 1;
            SpaceType = "standard";
            Status = "available";
            Section = "A";
            Row = 1;
            Column = 1;
            DistanceFromEntrance = 0;
            ParkingSessions = new HashSet<ParkingSession>();
        }
    }
}