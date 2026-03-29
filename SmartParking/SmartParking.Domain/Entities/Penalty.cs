using System;

namespace SmartParking.Domain.Entities
{
    public class Penalty : BaseEntity
    {
        public Guid? ParkingSessionId { get; set; }  // ← NULLABLE yap!
        public string ViolationType { get; set; } = string.Empty; // "WrongParking", "Overtime", "NoPayment"
        public decimal Amount { get; set; }
        public DateTime IssuedAt { get; set; }
        public bool IsPaid { get; set; }
        public DateTime? PaidAt { get; set; }
        public string Description { get; set; } = string.Empty; // "Park çizgilerinin dışında"
        public string? ImageUrl { get; set; } // İhlal fotoğrafı
        public Guid? VehicleId { get; set; }         // Araç FK (opsiyonel)
        public string? PlateNumber { get; set; }     // Plaka (direkt)
        public string? QrCode { get; set; }          // QR kod (direkt)

        // ✨ YENİ ALANLAR - YAMUK PARK + YOL İHLALİ İÇİN
        // ============================================================
        public string? CameraName { get; set; }           // Hangi kamera tespit etti
        public string? DetectionVehicleId { get; set; }   // Python tracking ID'si
        public string? ZoneId { get; set; }               // Yol ihlali için zone ID
        public string? ParkingSpaceIds { get; set; }      // Yamuk park için (JSON: ["C1","C2"])
                                                          // ============================================================


        // Navigation Properties
        public virtual ParkingSession? ParkingSession { get; set; }
        public virtual Vehicle? Vehicle { get; set; }  // ✅ YENİ!
        public Penalty()
        {
            ViolationType = string.Empty;
            Amount = 0;
            IssuedAt = DateTime.UtcNow;
            IsPaid = false;
            Description = string.Empty;
        }
    }
}