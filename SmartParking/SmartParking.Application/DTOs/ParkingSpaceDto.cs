using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SmartParking.Application.DTOs
{
    public class ParkingSpaceDto
    {
        public Guid Id { get; set; }
        public string SpaceNumber { get; set; } = string.Empty;
        public bool IsOccupied { get; set; }
        public string SpaceType { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public int FloorLevel { get; set; }
        public string Section { get; set; } = "A";
        public string? Coordinates { get; set; }  // JSON string
        public int Row { get; set; }

        /// <summary>
        /// Sütun numarası (UI için)
        /// </summary>
        public int Column { get; set; }

        /// <summary>
        /// Kamera ID
        /// </summary>
        public Guid? CameraId { get; set; }
    }
}
