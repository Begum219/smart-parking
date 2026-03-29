using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Application.DTOs
{
    public class ParkingSessionDto
    {
        public Guid Id { get; set; }
        public Guid? VehicleId { get; set; }
        public string VehicleLabel { get; set; } = string.Empty;
        public Guid? ParkingSpaceId { get; set; }
        public string SpaceNumber { get; set; } = string.Empty;
        public DateTime EntryTime { get; set; }
        public DateTime? ExitTime { get; set; }
        public int? DurationMinutes { get; set; }
        public decimal TotalFee { get; set; }
        public string PaymentStatus { get; set; } = string.Empty;
        public string SessionStatus { get; set; } = string.Empty;
        public int? DetectionVehicleId { get; set; }
        public string? DetectedPlateNumber { get; set; }
        public string? QrCode { get; set; }
        public double? Confidence { get; set; }
    }
}
