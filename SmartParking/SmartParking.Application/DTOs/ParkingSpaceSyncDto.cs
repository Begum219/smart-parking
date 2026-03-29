using System.Collections.Generic;

namespace SmartParking.Application.DTOs
{
    /// <summary>
    /// Python'dan gelen park yeri sync verisi
    /// </summary>
    public class ParkingSpaceSyncDto
    {
        /// <summary>
        /// Kamera ID (0, 1, 2...)
        /// </summary>
        public int CameraId { get; set; }

        /// <summary>
        /// Kamera adı
        /// </summary>
        public string CameraName { get; set; } = string.Empty;

        /// <summary>
        /// Park yerleri listesi
        /// </summary>
        public List<ParkingSpaceItemDto> ParkingSpaces { get; set; } = new();
    }

    /// <summary>
    /// Tek bir park yeri
    /// </summary>
    public class ParkingSpaceItemDto
    {
        /// <summary>
        /// Park yeri ID (A1, A2, C1, vs.)
        /// </summary>
        public string SpaceId { get; set; } = string.Empty;

        /// <summary>
        /// Koordinatlar [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        /// </summary>
        public List<List<int>> Coordinates { get; set; } = new();
    }
}