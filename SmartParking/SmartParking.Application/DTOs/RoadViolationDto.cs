using System;

namespace SmartParking.Application.DTOs
{
    /// <summary>
    /// Yol ihlali (şerit ihlali) cezası DTO
    /// Python detection sistemi tarafından gönderilen format
    /// SessionId gerektirmez - doğrudan plaka/QR ile ceza kesilir
    /// </summary>
    public class RoadViolationDto
    {
        /// <summary>
        /// Tespit eden kamera adı
        /// Örnek: "Kamera 1 (A-B Bölümü)"
        /// </summary>
        public string CameraName { get; set; } = string.Empty;

        /// <summary>
        /// Python tracking sistemi araç ID'si
        /// Örnek: "1", "2", "3"
        /// </summary>
        public string DetectionVehicleId { get; set; } = string.Empty;

        /// <summary>
        /// Yol zone ID'si - hangi yol alanında tespit edildi
        /// Örnek: "road_zone_1", "road_zone_AB"
        /// </summary>
        public string ZoneId { get; set; } = string.Empty;

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
        /// Python'dan gelen: 500.00
        /// </summary>
        public decimal Amount { get; set; }

        // ============================================================
        // OPSIYONEL ALANLAR (Python kullanmıyor ama tutulabilir)
        // ============================================================

        /// <summary>
        /// İhlal fotoğrafı URL (opsiyonel - şu an kullanılmıyor)
        /// </summary>
        public string? ImageUrl { get; set; }

        /// <summary>
        /// Tespit zamanı (opsiyonel - backend otomatik oluşturuyor)
        /// </summary>
        public DateTime? DetectionTime { get; set; }
    }
}