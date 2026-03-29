using SmartParking.Domain.Entities;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Domain.Entities
{
    public class ParkingSession : BaseEntity
    {
        public Guid? VehicleId { get; set; }
        public Guid? ParkingSpaceId { get; set; }
        public DateTime EntryTime { get; set; }
        public DateTime? ExitTime { get; set; }
        public int? DurationMinutes { get; set; }
        public decimal TotalFee { get; set; }
        public string PaymentStatus { get; set; } // "pending", "paid", "cancelled"
        public string SessionStatus { get; set; } // "active", "completed", "cancelled"
        public string? EntryImageUrl { get; set; }
        public string? ExitImageUrl { get; set; }
        public int? DetectionVehicleId { get; set; }
        public string? DetectedPlateNumber { get; set; }
        public string? QrCode { get; set; }
        public double? Confidence { get; set; }

        // Navigation Properties
        public virtual Vehicle? Vehicle { get; set; }
        public virtual ParkingSpace? ParkingSpace { get; set; }
        public virtual Payment? Payment { get; set; }

        // ✨ YENİ - Ceza sistemi için ilişki
        public virtual ICollection<Penalty> Penalties { get; set; }

        public ParkingSession()
        {
            EntryTime = DateTime.UtcNow;
            TotalFee = 0;
            PaymentStatus = "pending";
            SessionStatus = "active";

            // ✨ YENİ - Penalties collection başlat
            Penalties = new HashSet<Penalty>();
        }
    }
}