using System;

namespace SmartParking.Application.DTOs
{
    public class DetectedVehicleDto
    {
        public int VehicleId { get; set; }
        public int? ParkingSpaceId { get; set; }
        public string? ParkingSpaceName { get; set; }
        public string? QrCode { get; set; }
        public string? PlateNumber { get; set; }
        public double Confidence { get; set; }
        public int FramesDetected { get; set; }
        public string? DetectionTime { get; set; }
        public string Status { get; set; } = "occupied";
    }
}