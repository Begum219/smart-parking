using System.Collections.Generic;

namespace SmartParking.Application.DTOs
{
    /// <summary>
    /// Yamuk park (birden fazla park yeri işgali) cezası DTO
    /// Python detection sistemi tarafından gönderilen format
    /// </summary>
    public class MultiSpaceViolationDto
    {
        /// <summary>
        /// Tespit eden kamera adı
        /// Örnek: "Kamera 2 (C Bölümü)"
        /// </summary>
        public string CameraName { get; set; } = string.Empty;

        /// <summary>
        /// Python tracking sistemi araç ID'si
        /// Örnek: "2", "5"
        /// </summary>
        public string DetectionVehicleId { get; set; } = string.Empty;

        /// <summary>
        /// İşgal edilen park yerleri listesi
        /// Örnek: ["C1", "C2"] veya ["A2", "A3"]
        /// Minimum 2 park yeri gerekli
        /// </summary>
        public List<string> ParkingSpaceIds { get; set; } = new();

        /// <summary>
        /// QR kod (varsa)
        /// </summary>
        public string? QrCode { get; set; }

        /// <summary>
        /// Plaka numarası (varsa)
        /// </summary>
        public string? PlateNumber { get; set; }

        /// <summary>
        /// Ceza miktarı (TL)
        /// Python'dan gelen: 300.00
        /// </summary>
        public decimal Amount { get; set; }

        /// <summary>
        /// İhlal tipi (default: multi_space_violation)
        /// </summary>
        public string ViolationType { get; set; } = "multi_space_violation";
    }
}